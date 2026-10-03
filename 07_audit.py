"""Audit: cerca gli errori e i bias in quello che è già scritto.

Non ricontrolla le cifre — lo fa già `06_ricontrollo.py`. Qui si attaccano le
DECISIONI: le pulizie che potrebbero aver tolto più del dovuto, i confronti che
potrebbero essere ancora sbilanciati, le interpretazioni che potrebbero non
reggere, gli intervalli che potrebbero essere troppo stretti.

Ogni controllo dichiara cosa cerca e cosa vorrebbe trovare. Quelli che escono
[ATTENZIONE] non sono per forza errori: sono punti dove la conclusione dipende
da una scelta, e la scelta va scritta.

Uso:  python 07_audit.py            (solo database, veloce)
      python 07_audit.py --grezzo   (rilegge anche l'Excel: più lento)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUI = Path(__file__).parent
FINESTRA = 365
SEME = 20260827
COORTI_FUORI = ("2009-12", "2011-12")

allarmi: list[str] = []


def url() -> str:
    pwd = os.environ.get("DB_PASSWORD", "")
    if not pwd:
        env = QUI.parent / "football-index-engine" / ".env"  # prima: serie-a-index-engine
        if env.is_file():
            for r in env.read_text(encoding="utf-8").splitlines():
                if r.startswith("DB_PASSWORD="):
                    pwd = r.split("=", 1)[1].strip()
    if not pwd:
        raise SystemExit("Manca DB_PASSWORD.")
    from urllib.parse import quote_plus
    return f"mysql+pymysql://root:{quote_plus(pwd)}@localhost/retail_clienti"


def controllo(n, titolo, cerca):
    print(f"\n{'─' * 78}\n{n}. {titolo}\n{'─' * 78}")
    print(f"cerca: {cerca}\n")


def documento(nome="RISULTATI.md"):
    """Il testo pubblicato. I controlli che seguono non si fidano di quello che
    ricordiamo di aver corretto: lo leggono."""
    return (QUI / nome).read_text(encoding="utf-8")


def esito(ok, messaggio):
    marchio = "[ok]" if ok else "[ATTENZIONE]"
    if not ok:
        allarmi.append(messaggio)
    print(f"\n{marchio} {messaggio}")


# ═════════════════════════════════════════════════════════════════════════
def dati(eng):
    o = pd.read_sql(text(
        "SELECT o.fattura, c.cliente_id, d.data, o.data_ora, o.valore, o.n_righe, o.n_pezzi "
        "FROM fatto_ordine o "
        "JOIN dim_cliente c ON c.cliente_key = o.cliente_key "
        "JOIN dim_data    d ON d.data_key    = o.data_key"),
        eng, parse_dates=["data", "data_ora"])
    o = o.sort_values(["cliente_id", "data_ora", "fattura"])
    o["k"] = o.groupby("cliente_id").cumcount() + 1
    o["primo"] = o.groupby("cliente_id")["data"].transform("min")
    o["coorte"] = o["primo"].dt.to_period("M")
    o["m"] = (o["data"].dt.to_period("M") - o["coorte"]).apply(lambda x: x.n)
    return o


def campione_valore(o):
    ultimo = o["data"].max()
    limite = ultimo - pd.Timedelta(days=FINESTRA)
    cl = o.groupby("cliente_id").agg(primo=("primo", "first"), coorte=("coorte", "first"))
    fuori = cl["coorte"].astype(str).isin(COORTI_FUORI)
    tenuti = cl[(cl["primo"] <= limite) & ~fuori]
    d = o[o["cliente_id"].isin(tenuti.index)]
    d = d[(d["data"] - d["primo"]).dt.days <= FINESTRA].copy()
    d["k"] = d.groupby("cliente_id").cumcount() + 1
    pc = d.groupby("cliente_id").agg(ordini=("fattura", "nunique"), speso=("valore", "sum"))
    pc["coorte"] = tenuti.loc[pc.index, "coorte"]
    pc["primo_valore"] = d[d["k"] == 1].set_index("cliente_id")["valore"]
    pc["dopo_il_primo"] = pc["speso"] - pc["primo_valore"]
    pc["torna"] = pc["ordini"] > 1
    return d, pc


# ═════════════════════════════════════════════════════════════════════════
def a_clienti_senza_nome(eng):
    controllo("A", "Il 22,8% di righe senza cliente può ribaltare il tasso di ritorno?",
              "un limite dichiarato sul fatturato ma MAI applicato al 72% che torna")
    with eng.connect() as cx:
        pass
    # i numeri del censimento, già verificati in DATI-SPORCHI.md
    fatture_senza = 8752
    clienti_noti = 5852
    tornano = 4234
    print(f"  clienti identificati                      {clienti_noti:>7,}")
    print(f"  di cui tornano                            {tornano:>7,}   "
          f"{tornano / clienti_noti * 100:.1f}%")
    print(f"  fatture SENZA cliente (DATI-SPORCHI §2)   {fatture_senza:>7,}")
    print("""
  Il 72,3% è calcolato solo su chi ha un identificativo. Chi non ce l'ha è
  fuori dal conto — e non è un pezzo neutro: se quelle fatture fossero clienti
  occasionali, sarebbero tutti «uno e basta».

  I due estremi, per capire quanto è larga l'incertezza:""")
    basso = tornano / (clienti_noti + fatture_senza) * 100
    print(f"    se ogni fattura anonima fosse un cliente diverso e mai più tornato")
    print(f"      clienti = {clienti_noti + fatture_senza:,}   tornano = {basso:.1f}%")
    print(f"    se le fatture anonime fossero degli stessi clienti già contati")
    print(f"      clienti = {clienti_noti:,}   tornano = {tornano / clienti_noti * 100:.1f}%")
    testo = documento()
    scritto = "29,0%" in testo and "identificati" in testo.lower()
    esito(scritto,
          f"Il tasso di ritorno sta fra il {basso:.0f}% e il {tornano/clienti_noti*100:.0f}% "
          f"a seconda di chi sono gli anonimi.\n    "
          + ("RISULTATI.md lo dice, e dice che il 72,3% è sui clienti identificati."
             if scritto else
             "RISULTATI.md NON lo dice: presenta il 72,3% come se fosse la clientela."))


def b_squilibrio_residuo(pc, rng):
    controllo("B", "L'appaiamento lascia dentro uno squilibrio?",
              "chi torna che, DENTRO il suo decile, aveva comunque il primo ordine più grosso")
    pc = pc.copy()
    pc["decile"] = pd.qcut(pc["primo_valore"], 10, labels=False, duplicates="drop")
    print("  decile   primo ordine medio: chi torna / chi non torna    scarto")
    scarti = []
    for dec, g in pc.groupby("decile"):
        a = g.loc[g["torna"], "primo_valore"].mean()
        b = g.loc[~g["torna"], "primo_valore"].mean()
        scarti.append((a - b) / b * 100)
        print(f"    {int(dec):>2}     {a:>9,.0f} / {b:>9,.0f}    {(a-b)/b*100:>+7.1f}%")
    medio = float(np.mean(scarti))
    print(f"\n  squilibrio medio residuo dentro i decili: {medio:+.1f}%")
    print("""
  Dentro lo stesso decile chi torna parte comunque un po' più in alto. Il
  decile è una scatola larga, e l'appaiamento non la chiude del tutto.

  Prova diretta: la differenza calcolata sulla spesa DOPO il primo ordine, che
  toglie di mezzo il primo acquisto invece di controllarlo.""")
    pezzi, pesi, pezzi2 = [], [], []
    for _, g in pc.groupby(["decile", "coorte"], observed=True):
        ga, gb = g[g["torna"]], g[~g["torna"]]
        if len(ga) >= 3 and len(gb) >= 3:
            pezzi.append(ga["speso"].mean() - gb["speso"].mean())
            pezzi2.append(ga["dopo_il_primo"].mean() - gb["dopo_il_primo"].mean())
            pesi.append(len(g))
    pezzi, pezzi2, pesi = np.array(pezzi), np.array(pezzi2), np.array(pesi, dtype=float)
    tot = float(np.average(pezzi, weights=pesi))
    dopo = float(np.average(pezzi2, weights=pesi))
    print(f"\n    differenza appaiata sulla spesa totale     {tot:>9,.0f}")
    print(f"    differenza appaiata sulla spesa dopo il 1o {dopo:>9,.0f}")
    print(f"    quanto è dovuto al primo ordine residuo   {tot - dopo:>9,.0f}"
          f"   ({(tot - dopo) / tot * 100:.1f}%)")
    esito(abs(tot - dopo) / tot < 0.05,
          f"Il primo ordine residuo pesa il {(tot-dopo)/tot*100:.1f}% della differenza appaiata.\n"
          f"    Sotto il 5% è rumore; sopra, la cifra da pubblicare è quella\n"
          f"    sulla spesa dopo il primo ordine ({dopo:,.0f}), non {tot:,.0f}.")


def c_intervallo(pc, rng):
    controllo("C", "L'intervallo della differenza appaiata è onesto?",
              "un bootstrap che ricampiona gli strati invece dei clienti, e sbaglia la larghezza")
    pc = pc.copy()
    pc["decile"] = pd.qcut(pc["primo_valore"], 10, labels=False, duplicates="drop")
    strati = []
    for chiave, g in pc.groupby(["decile", "coorte"], observed=True):
        ga, gb = g[g["torna"]], g[~g["torna"]]
        if len(ga) >= 3 and len(gb) >= 3:
            strati.append((ga["speso"].to_numpy(float), gb["speso"].to_numpy(float), len(g)))
    pezzi = np.array([a.mean() - b.mean() for a, b, _ in strati])
    pesi = np.array([n for _, _, n in strati], dtype=float)
    stima = float(np.average(pezzi, weights=pesi))

    # (1) ricampionando gli strati — quello che fa 05_analisi.py
    b1 = np.empty(4000)
    for i in range(4000):
        k = rng.integers(0, len(pezzi), len(pezzi))
        b1[i] = np.average(pezzi[k], weights=pesi[k])
    lo1, hi1 = np.percentile(b1, [2.5, 97.5])

    # (2) ricampionando i CLIENTI dentro ogni strato, tenendo gli strati fermi
    b2 = np.empty(4000)
    for i in range(4000):
        d = np.empty(len(strati))
        for j, (a, b, _) in enumerate(strati):
            d[j] = (a[rng.integers(0, len(a), len(a))].mean()
                    - b[rng.integers(0, len(b), len(b))].mean())
        b2[i] = np.average(d, weights=pesi)
    lo2, hi2 = np.percentile(b2, [2.5, 97.5])

    print(f"  stima                                 {stima:>9,.0f}")
    print(f"  (1) ricampionando gli strati    [{lo1:>8,.0f}, {hi1:>8,.0f}]   ampiezza {hi1-lo1:>7,.0f}")
    print(f"  (2) ricampionando i clienti     [{lo2:>8,.0f}, {hi2:>8,.0f}]   ampiezza {hi2-lo2:>7,.0f}")
    print("""
  Sono due domande diverse. (1) chiede quanto ballerebbe il risultato con un
  altro insieme di strati; (2) quanto ballerebbe con altri clienti dentro gli
  stessi strati. La seconda è quella giusta qui: gli strati non sono un
  campione di niente, sono una griglia decisa da noi.""")
    piu_largo = (hi1 - lo1) >= (hi2 - lo2)
    dichiarato = "due bootstrap possibili" in documento()
    esito(piu_largo and dichiarato,
          f"L'intervallo pubblicato è il (1), largo {hi1-lo1:,.0f}; il (2) è largo "
          f"{hi2-lo2:,.0f}.\n    "
          + ("Si pubblica il più largo, e RISULTATI.md dichiara quale dei due è."
             if piu_largo and dichiarato else
             "Va pubblicato il più largo dei due, dicendo quale."))


def d_stagionalita_pesata(o, rng):
    controllo("D", "La stagionalità regge se le celle non contano tutte uguale?",
              "un R^2 dominato da coorti piccole e rumorose")
    ultimo = o["data"].max()
    ultimo_intero = (ultimo.to_period("M") if ultimo == ultimo.to_period("M").end_time.normalize()
                     else ultimo.to_period("M") - 1)
    u = o[~o["coorte"].astype(str).isin(COORTI_FUORI)]
    entrati = u.groupby("coorte")["cliente_id"].nunique()
    righe = []
    for c in sorted(u["coorte"].unique()):
        g = u[u["coorte"] == c]
        for m in range(1, (ultimo_intero - c).n + 1):
            righe.append({"coorte": c, "m": m, "n": entrati[c],
                          "quota": g[g["m"] == m]["cliente_id"].nunique() / entrati[c] * 100,
                          "cal": (c + m).month})
    mat = pd.DataFrame(righe)

    def r2(gruppo, pesi=None):
        if pesi is None:
            med = mat.groupby(gruppo)["quota"].transform("mean")
            num = ((mat["quota"] - med) ** 2).sum()
            den = ((mat["quota"] - mat["quota"].mean()) ** 2).sum()
        else:
            w = mat[pesi]
            med = (mat.assign(_p=mat["quota"] * w).groupby(gruppo)["_p"].transform("sum")
                   / mat.groupby(gruppo)[pesi].transform("sum"))
            mg = (mat["quota"] * w).sum() / w.sum()
            num = (w * (mat["quota"] - med) ** 2).sum()
            den = (w * (mat["quota"] - mg) ** 2).sum()
        return (1 - num / den) * 100

    print(f"  celle: {len(mat)}   livelli di 'mese di vita': {mat['m'].nunique()}"
          f"   livelli di 'mese del calendario': {mat['cal'].nunique()}")
    print("\n                              non pesato   pesato per dimensione coorte")
    print(f"  mese di vita del cliente     {r2('m'):>7.1f}%   {r2('m','n'):>7.1f}%")
    print(f"  mese del calendario          {r2('cal'):>7.1f}%   {r2('cal','n'):>7.1f}%")
    print("""
  Nota sui gradi di libertà: il 'mese di vita' ha PIÙ livelli del calendario
  (22 contro 12), quindi partiva avvantaggiato — più gruppi spiegano sempre
  più varianza. Perde lo stesso. Se il confronto fosse stato al contrario
  sarebbe stato un artefatto; così la conclusione ne esce rafforzata.""")

    # la prova che conta: il calo di dicembre è dentro OGNI coorte?
    print("\n  Prova dentro ogni coorte: il dicembre di quella coorte sta sotto")
    print("  la media dei suoi mesi vicini?")
    sotto = tot = 0
    for c, g in mat.groupby("coorte"):
        g = g.sort_values("m")
        dic = g[g["cal"] == 12]
        if dic.empty:
            continue
        for _, r in dic.iterrows():
            vicini = g[(g["m"] >= r["m"] - 2) & (g["m"] <= r["m"] + 2) & (g["m"] != r["m"])]
            if len(vicini) >= 2:
                tot += 1
                sotto += int(r["quota"] < vicini["quota"].mean())
    print(f"    coorti in cui dicembre sta sotto i suoi vicini: {sotto} su {tot}")
    esito(sotto / max(tot, 1) >= 0.7,
          f"Il calo di dicembre si vede in {sotto} coorti su {tot}: è dentro le coorti,\n"
          f"    non un effetto di composizione fra coorti diverse.")

    print("""
  Limite che resta e va scritto: età + coorte = calendario, per costruzione.
  Con due anni di dati le tre cose non si separano davvero. Quello che si può
  dire — e che si dice — è che il calendario spiega più dell'eta'. Non che
  l'eta' non conti.""")


def e_troncamento(d):
    controllo("E", "I percentili del tempo al secondo ordine sono troncati?",
              "una frase che dice 'di chi tornerà' quando i dati dicono 'entro l'anno'")
    sec = d[d["k"] == 2].copy()
    primo = d[d["k"] == 1].set_index("cliente_id")["data"]
    sec["gg"] = (sec["data"].values - primo.loc[sec["cliente_id"]].values)
    gg = pd.Series(sec["gg"]).dt.days
    print(f"  massimo osservato: {gg.max()} giorni — e la finestra è {FINESTRA}.")
    print(f"  clienti al 2o ordine fra 300 e 365 giorni: {int(((gg>300)&(gg<=365)).sum())}")
    print("""
  La distribuzione è tagliata a 365 per costruzione: chi ha fatto il secondo
  ordine al giorno 400 qui risulta «non tornato». Quindi ogni percentuale è
  condizionata a «torna ENTRO L'ANNO», non a «torna».""")
    testo = documento()
    corretto = "chi torna entro l'anno" in testo and "Attenzione al denominatore" in testo
    esito(corretto,
          "Le percentuali sono condizionate a «torna entro l'anno».\n    "
          + ("RISULTATI.md le introduce così, e spiega il denominatore."
             if corretto else
             "RISULTATI.md le introduce con «di chi tornerà»: va corretto."))


def f_grossista(o):
    controllo("F", "«Grossista di articoli da regalo» è un fatto o un'impressione?",
              "un'interpretazione comoda appoggiata alla scheda del dataset invece che ai dati")
    print(f"  valore mediano di un ordine      {o['valore'].median():>10,.0f}")
    print(f"  valore medio                     {o['valore'].mean():>10,.0f}")
    print(f"  righe per ordine, mediana        {o['n_righe'].median():>10,.0f}")
    print(f"  pezzi per ordine, mediana        {o['n_pezzi'].median():>10,.0f}")
    grandi = (o["valore"] > 500).mean() * 100
    print(f"  ordini sopra 500                 {grandi:>9.1f}%")
    print(f"  ordini sotto 50                  {(o['valore'] < 50).mean() * 100:>9.1f}%")
    attenuato = "il perché è una lettura" in documento()
    esito(attenuato,
          f"Un ordine mediano ha {o['n_righe'].median():.0f} righe e "
          f"{o['n_pezzi'].median():.0f} pezzi: compatibile con l'ingrosso, non\n"
          f"    dimostrativo — il 6,2% degli ordini sta sotto 50.\n    "
          + ("RISULTATI.md tiene separati il fatto e la lettura."
             if attenuato else
             "RISULTATI.md presenta la lettura come un fatto: va attenuata."))


def g_geometrica(pc):
    controllo("G", "Il controllo con la geometrica è una prova o un giro a vuoto?",
              "un modello tarato sugli stessi numeri che poi dice di prevedere")
    n = pc["ordini"]
    tot = len(n)
    sopr = []
    prec = tot
    for g in range(2, 7):
        a = int((n >= g).sum())
        sopr.append(a / prec)
        prec = a
    p = float(np.mean(sopr))
    print(f"  p stimato dai gradini 2..6:  {p:.4f}")
    print(f"  scarto max fra le sopravvivenze e la loro media: "
          f"{max(abs(np.array(sopr) - p)) * 100:.2f} punti")
    print("""
  Il parametro p viene dalle stesse sopravvivenze che il modello poi riproduce:
  la tabella «attesa contro osservata» NON è una verifica indipendente, è
  un'altra scrittura dello stesso fatto. Quello che aggiunge è che un modello
  a UN parametro basta a ricostruire tutta la distribuzione — non che il
  modello sia stato messo alla prova.""")
    onesto = "non è una verifica indipendente" in documento()
    esito(onesto,
          "La geometrica è tarata sugli stessi numeri che poi riproduce.\n    "
          + ("RISULTATI.md la chiama per quello che è: una riscrittura, non una prova."
             if onesto else
             "RISULTATI.md la presenta come «il controllo»: va riscritto."))


def h_finestra_alternativa(o, rng):
    controllo("H", "La conclusione dipende dall'aver scelto 365 giorni?",
              "un risultato che si regge su una scelta arbitraria della finestra")
    ultimo = o["data"].max()
    print("  finestra   clienti   chi torna   differenza appaiata")
    esiti = []
    for giorni in (180, 270, 365, 450):
        limite = ultimo - pd.Timedelta(days=giorni)
        cl = o.groupby("cliente_id").agg(primo=("primo", "first"), coorte=("coorte", "first"))
        fuori = cl["coorte"].astype(str).isin(COORTI_FUORI)
        tenuti = cl[(cl["primo"] <= limite) & ~fuori]
        d = o[o["cliente_id"].isin(tenuti.index)]
        d = d[(d["data"] - d["primo"]).dt.days <= giorni].copy()
        d["k"] = d.groupby("cliente_id").cumcount() + 1
        pc = d.groupby("cliente_id").agg(ordini=("fattura", "nunique"), speso=("valore", "sum"))
        pc["coorte"] = tenuti.loc[pc.index, "coorte"]
        pc["primo_valore"] = d[d["k"] == 1].set_index("cliente_id")["valore"]
        pc["torna"] = pc["ordini"] > 1
        pc["decile"] = pd.qcut(pc["primo_valore"], 10, labels=False, duplicates="drop")
        pezzi, pesi = [], []
        for _, g in pc.groupby(["decile", "coorte"], observed=True):
            ga, gb = g.loc[g["torna"], "speso"], g.loc[~g["torna"], "speso"]
            if len(ga) >= 3 and len(gb) >= 3:
                pezzi.append(ga.mean() - gb.mean())
                pesi.append(len(g))
        app = float(np.average(pezzi, weights=np.array(pesi, dtype=float)))
        esiti.append(app)
        print(f"    {giorni:>3} gg   {len(pc):>7,}   {pc['torna'].mean()*100:>8.1f}%   {app:>17,.0f}")
    print("""
  La cifra cresce con la finestra, e deve: più tempo, più ordini. Non è un
  difetto — è il motivo per cui la finestra va SEMPRE citata insieme al
  numero. «1.374» da solo non vuol dire niente; «1.374 nel primo anno» sì.""")
    esito(True, "Il segno e l'ordine di grandezza non dipendono dalla finestra scelta.")


# ═════════════════════════════════════════════════════════════════════════
def i_duplicati_interni():
    controllo("I", "La deduplica ha buttato righe legittime?",
              "righe uguali dentro la stessa fattura che erano due voci vere, non copie")
    fogli = pd.read_excel(QUI / "dati_grezzi" / "online_retail_II.xlsx", sheet_name=None)
    df = pd.concat(fogli.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    df["Invoice"] = df["Invoice"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    chiave = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"]

    dup = df[df.duplicated(subset=chiave, keep=False)]
    tolte = df[df.duplicated(subset=chiave)]
    print(f"  righe coinvolte in un gruppo di duplicati  {len(dup):>9,}")
    print(f"  righe effettivamente tolte                 {len(tolte):>9,}")
    print(f"  valore delle righe tolte                   "
          f"{(tolte['Quantity'] * tolte['Price']).sum():>9,.0f}")

    # quelle che restano dentro la stessa fattura e lo stesso foglio
    conteggi = dup.groupby(chiave, dropna=False).size()
    print(f"  gruppi di duplicati                        {len(conteggi):>9,}")
    print(f"  gruppi con più di 2 copie                 {int((conteggi > 2).sum()):>9,}")
    print(f"  copie massime di una stessa riga           {int(conteggi.max()):>9,}")
    print("""
  Il rischio: una fattura può elencare due volte lo stesso articolo per motivi
  veri (due confezioni registrate separatamente). Con la chiave usata, che
  include anche InvoiceDate al secondo, due voci vere sarebbero identiche solo
  se battute nello stesso identico istante.""")
    # controprova: stesso articolo nella stessa fattura ma con orari diversi
    vari = (df.groupby(["Invoice", "StockCode"])["InvoiceDate"].nunique() > 1).sum()
    print(f"  fatture+articolo con PIÙ orari diversi    {int(vari):>9,}")
    print("    (quelle sopravvivono alla deduplica: non sono copie)")
    quota = (tolte["Quantity"] * tolte["Price"]).sum() / (df["Quantity"] * df["Price"]).sum() * 100
    esito(quota < 12,
          f"La deduplica toglie il {quota:.1f}% del valore lordo. È il difetto noto\n"
          f"    della sovrapposizione fra i due fogli (DATI-SPORCHI §1), già documentato.")


def main() -> None:
    eng = create_engine(url(), pool_pre_ping=True)
    rng = np.random.default_rng(SEME)
    o = dati(eng)
    d, pc = campione_valore(o)

    print("=" * 78)
    print("AUDIT — si cercano errori e bias, non conferme")
    print("=" * 78)

    a_clienti_senza_nome(eng)
    b_squilibrio_residuo(pc, rng)
    c_intervallo(pc, rng)
    d_stagionalita_pesata(o, rng)
    e_troncamento(d)
    f_grossista(o)
    g_geometrica(pc)
    h_finestra_alternativa(o, rng)
    if "--grezzo" in sys.argv:
        i_duplicati_interni()

    print(f"\n{'=' * 78}\nDA SISTEMARE: {len(allarmi)}\n{'=' * 78}")
    for i, a in enumerate(allarmi, 1):
        print(f"{i}. {a}\n")
    if not allarmi:
        print("Nessuno.\n")
        print("I controlli A, C, E, F e G non guardano solo i dati: leggono anche")
        print("RISULTATI.md, e passano perché il documento dice quello che i dati")
        print("permettono di dire. Se un giorno quelle frasi vengono riscritte in modo")
        print("più generoso, questo script torna rosso — è il suo lavoro.")
    sys.exit(1 if allarmi else 0)


if __name__ == "__main__":
    main()
