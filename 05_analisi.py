"""Le misure: retention, valore del cliente, funnel di riacquisto.

Le scelte metodologiche stanno nei commenti dentro le sezioni, non in fondo:
sono la parte che cambia i numeri, e vanno lette insieme al numero che cambiano.

Quello che stampa finisce in RISULTATI.md. La matrice esce anche in CSV.

Uso:  python 05_analisi.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

import valore_futuro

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUI = Path(__file__).parent
DB = "retail_clienti"
FINESTRA = 365          # giorni di osservazione, uguali per ogni cliente
RIPETIZIONI = 2000      # ricampionamenti per gli intervalli
SEME = 20260827

# Le due coorti escluse, e il perche' sta in MODELLO.md, punti 1 e 2.
COORTI_FUORI = ("2009-12", "2011-12")
MESI = "gen feb mar apr mag giu lug ago set ott nov dic".split()


def url() -> str:
    pwd = os.environ.get("DB_PASSWORD", "")
    if not pwd:
        # la cartella si chiamava serie-a-index-engine: il nome nuovo e' football-index-engine
        env = next((p for p in (QUI.parent / "football-index-engine" / ".env",
                                QUI.parent / "serie-a-index-engine" / ".env") if p.is_file()),
                   QUI.parent / "football-index-engine" / ".env")
        if env.is_file():
            for r in env.read_text(encoding="utf-8").splitlines():
                if r.startswith("DB_PASSWORD="):
                    pwd = r.split("=", 1)[1].strip()
    if not pwd:
        raise SystemExit("Manca DB_PASSWORD.")
    from urllib.parse import quote_plus
    return f"mysql+pymysql://root:{quote_plus(pwd)}@localhost/{DB}"


def titolo(n, t):
    print(f"\n{'=' * 76}\n{n}. {t}\n{'=' * 76}")


def quota_spiegata(d, colonna, gruppo):
    """Quanta della variazione di `colonna` resta spiegata raggruppando per
    `gruppo`. E' un R^2 fatto a mano sulle medie di gruppo: serve a confrontare
    due spiegazioni fra loro, non a dichiarare un modello."""
    m = d.groupby(gruppo)[colonna].transform("mean")
    return 1 - ((d[colonna] - m) ** 2).sum() / ((d[colonna] - d[colonna].mean()) ** 2).sum()


# ══════════════════════════════════════════════════════════════════════════
def matrice(eng):
    d = pd.read_sql(text("""
        SELECT coorte, mese_relativo, clienti_attivi, clienti_entrati,
               quota_attivi, mesi_osservabili
        FROM v_retention_coorte
    """), eng, parse_dates=["coorte"])
    d = d[~d["coorte"].dt.strftime("%Y-%m").isin(COORTI_FUORI)]

    titolo(1, "La matrice di retention")
    print("""  Una cella dice: di cento clienti entrati nel mese X, quanti hanno ordinato
  al mese X+n. Le celle che il calendario non ha ancora raggiunto restano
  vuote, non a zero: `mesi_osservabili` conta solo i mesi FINITI, e dicembre
  2011 e' lungo nove giorni.""")

    # una cella vale solo se il mese e' passato per davvero
    d["valida"] = d["mese_relativo"] <= d["mesi_osservabili"]
    print(f"\n  coorti utili                        {d['coorte'].nunique():>4}")
    print(f"  celle piene e osservate (n >= 1)    "
          f"{int((d['valida'] & (d['mese_relativo'] >= 1)).sum()):>4}")
    print("  (la coorte di novembre 2011 non ha nemmeno un mese intero davanti:")
    print("   esiste, ma non porta celle alla matrice)")

    tab = d[d["valida"]].pivot_table(index="coorte", columns="mese_relativo",
                                     values="quota_attivi")
    salva = tab.copy()
    salva.index = salva.index.strftime("%Y-%m")
    salva.to_csv(QUI / "risultati" / "matrice_retention.csv", float_format="%.1f")

    entrati = d.groupby("coorte")["clienti_entrati"].first()
    print("\n  " + "coorte      n".ljust(15) + "".join(f"{m:>5}" for m in range(0, 13)))
    for etichetta, riga in tab.iterrows():
        celle = "".join("    ." if pd.isna(riga.get(m)) else f"{riga.get(m):5.0f}"
                        for m in range(0, 13))
        print(f"  {etichetta:%Y-%m} {int(entrati[etichetta]):>5}  {celle}")
    print("     (valori in percentuale; il punto e' una cella non ancora osservabile)")
    return d[d["valida"] & (d["mese_relativo"] >= 1)].copy()


def stagionalita(d):
    titolo(2, "La retention non e' una discesa: e' un calendario")
    print("""  Prima di leggere la matrice come una curva di abbandono, conviene chiedersi
  se scende per il motivo che sembra. Ogni cella sta a un mese di vita del
  cliente E a un mese del calendario. Si guarda quale dei due la spiega.""")
    d["mese_calendario"] = (d["coorte"].dt.to_period("M") + d["mese_relativo"]).dt.month
    a = quota_spiegata(d, "quota_attivi", "mese_relativo")
    b = quota_spiegata(d, "quota_attivi", "mese_calendario")
    c = quota_spiegata(d, "quota_attivi", ["mese_relativo", "mese_calendario"])
    print(f"\n  il mese di vita del cliente (+1, +2, +3...)  spiega il  {a*100:4.1f}%")
    print(f"  il mese del calendario (gennaio, febbraio...) spiega il  {b*100:4.1f}%")
    print(f"  tutti e due insieme                           spiegano l'{c*100:4.1f}%")
    print("\n  Il calendario conta piu' del doppio dell'eta' del cliente.")

    print("\n  media della retention per mese del calendario:")
    quando = (d["coorte"].dt.to_period("M") + d["mese_relativo"])
    for m, riga in d.groupby("mese_calendario")["quota_attivi"].mean().items():
        anni = sorted(set(quando[d["mese_calendario"] == m].dt.year))
        nota = "" if len(anni) > 1 else f"   <- un anno solo ({anni[0]})"
        print(f"    {MESI[m-1]}  {riga:5.1f}%  {'#' * int(round(riga))}{nota}")

    print("""
  Novembre 25%, gennaio 11%, e il picco arriva PRIMA di Natale, non durante.
  La lettura naturale e' che molti di questi clienti siano negozi che si
  riforniscono in autunno: la stagione sarebbe del compratore, non del
  venditore. I dati la sostengono — ordine mediano 303, con 15 righe e 153
  pezzi — ma non la dimostrano. Il picco e' un fatto, il perche' e' una
  lettura, e quello che segue non dipende dal perche'.

  I due estremi sono anche i meno sostenuti: nella finestra dei dati c'e' un
  dicembre solo e un gennaio solo. La forma regge sui mesi centrali, che hanno
  due anni a testa; sui due estremi si dice la direzione, non la cifra.

  Conseguenza pratica, ed e' la ragione per cui questa sezione viene prima
  delle altre: due coorti non si confrontano se non hanno vissuto gli stessi
  mesi. Chi entra a ottobre ha Natale davanti; chi entra a gennaio ha undici
  mesi di attesa. Una classifica delle coorti per retention misurerebbe il mese
  di ingresso, non la qualita' dei clienti.""")


def decrescita(d):
    titolo(3, "Quanto scende davvero, a parita' di coorti")
    print("""  Nella tabella per mese di vita, ogni riga e' fatta di coorti diverse: al
  mese +12 arrivano solo le coorti vecchie. Se quelle fossero migliori, la
  curva sembrerebbe piatta senza esserlo. Si rifa' il conto sulle coorti che
  hanno tutti i dodici mesi, sempre le stesse in ogni riga.""")
    bil = d[d["mesi_osservabili"] >= 12]
    b = bil[bil["mese_relativo"] <= 12]
    print(f"\n  coorti nel panel bilanciato: {bil['coorte'].nunique()}"
          f"  ({bil['coorte'].min():%Y-%m} -> {bil['coorte'].max():%Y-%m})\n")
    for m, g in b.groupby("mese_relativo"):
        media = g["quota_attivi"].mean()
        print(f"    +{m:<3} {media:5.1f}%  {'#' * int(round(media))}")

    print("\n  quanto cambia rispetto alla versione sbilanciata:")
    for m in (1, 6, 12):
        x = d[d["mese_relativo"] == m]["quota_attivi"].mean()
        y = b[b["mese_relativo"] == m]["quota_attivi"].mean()
        print(f"    +{m:<3} sbilanciato {x:5.1f}%   bilanciato {y:5.1f}%   scarto {y - x:+.1f}")
    print("""
  Lo scarto e' sotto il punto percentuale: il difetto c'era ma non mordeva. Si
  usa comunque il panel bilanciato, perche' qui costa niente e altrove no.

  La curva scende dal 20% al 13% e poi RISALE al 18% al dodicesimo mese. Non e'
  un ritorno di fiamma: per una coorte del 2010, il mese +12 e' lo stesso mese
  del calendario un anno dopo. E' la stagionalita' della sezione 2 che rientra
  dalla finestra.""")


# ══════════════════════════════════════════════════════════════════════════
def valore(eng, rng):
    ordini = pd.read_sql(text("""
        SELECT fattura, cliente_id, data, valore, paese, n_ordine,
               giorni_dal_precedente, data_primo_ordine, coorte
        FROM v_ordini_sequenza
    """), eng, parse_dates=["data", "data_primo_ordine", "coorte"])
    ultimo = pd.Timestamp(pd.read_sql(text("SELECT MAX(data) d FROM dim_data d JOIN fatto_ordine o ON o.data_key = d.data_key"), eng)["d"].iloc[0])

    titolo(4, "La finestra di osservazione, per la domanda sul valore")
    print(f"""  ultimo giorno nei dati: {ultimo:%Y-%m-%d}
  finestra per cliente  : {FINESTRA} giorni dal SUO primo ordine

  Confrontare "quanto ha speso finora" fra un cliente entrato a gennaio 2010 e
  uno entrato a ottobre 2011 non misura il cliente: misura quanto tempo ha
  avuto. Si guardano i primi {FINESTRA} giorni di ciascuno, e restano solo i
  clienti che quei giorni li hanno avuti per intero.

  Nota: questa selezione vale per il valore, non per la matrice. La matrice
  gestisce lo stesso problema in un altro modo, lasciando vuote le celle non
  osservate, e non ha bisogno di buttare via nessuno.""")

    limite = ultimo - pd.Timedelta(days=FINESTRA)
    clienti = (ordini.groupby("cliente_id")
                     .agg(primo=("data_primo_ordine", "first"), coorte=("coorte", "first"))
                     .reset_index())
    fuori = clienti["coorte"].dt.strftime("%Y-%m").isin(COORTI_FUORI)
    print(f"\n  clienti in tutto                       {len(clienti):>7,}")
    print(f"  meno le coorti 2009-12 e 2011-12       {int(fuori.sum()):>7,}")
    print(f"  meno chi non ha {FINESTRA} giorni davanti    "
          f"{int(((clienti['primo'] > limite) & ~fuori).sum()):>7,}")
    tenuti = clienti[(clienti["primo"] <= limite) & ~fuori]
    print(f"  clienti nell'analisi del valore        {len(tenuti):>7,}")
    print(f"  coorti coinvolte: {tenuti['coorte'].min():%Y-%m} -> {tenuti['coorte'].max():%Y-%m}")
    print("""
  Sono tutte coorti del 2010, e dopo la sezione 2 questo NON e' un dettaglio:
  il gruppo non e' piu' un campione di tutti i clienti, e' un campione di chi
  e' entrato nel 2010. Vale come confronto interno fra questi clienti, non come
  ritratto della base.""")

    o = (ordini.drop(columns=["coorte"])
               .merge(tenuti[["cliente_id", "primo", "coorte"]], on="cliente_id"))
    dentro = o[(o["data"] - o["primo"]).dt.days <= FINESTRA]

    pc = (dentro.groupby("cliente_id")
                .agg(ordini_365=("fattura", "nunique"), speso_365=("valore", "sum"),
                     coorte=("coorte", "first"))
                .reset_index())
    pc = pc.merge(dentro[dentro["n_ordine"] == 1].set_index("cliente_id")["valore"]
                  .rename("valore_primo"), on="cliente_id", how="left")
    pc["torna"] = pc["ordini_365"] > 1

    titolo(5, "Il funnel di riacquisto, dentro i 365 giorni")
    n = len(pc)
    prec = n
    sopravvivenze = []
    print("  gradino   clienti   quota   sopravvive dal gradino prima")
    for g in range(1, 9):
        arr = int((pc["ordini_365"] >= g).sum())
        if g > 1:
            sopravvivenze.append(arr / prec)
            coda = f"{arr / prec * 100:>10.1f}%"
        else:
            coda = ""
        print(f"  {g:>5}    {arr:>7,}  {arr / n * 100:6.1f}%{coda}")
        prec = arr
    p = float(np.mean(sopravvivenze[:5]))
    print(f"""
  Sopravvivenza media sui primi sei gradini: {p * 100:.1f}%, e non si muove.
  Questo contraddice il conto della Fase 2, dove il primo salto sembrava il piu'
  duro (72% e poi 78%, 80%, 81%). Quel conto guardava tutta la vita di ogni
  cliente: chi e' entrato nel 2010 aveva due anni per arrivare all'ottavo
  ordine, chi e' entrato a settembre 2011 ne aveva tre mesi. La sopravvivenza
  che saliva era il tempo in piu' di chi era arrivato in fondo, non una fedelta'
  che cresce. A tempo fissato la salita sparisce.

  Il processo non ha memoria: arrivare al secondo ordine non mette al sicuro.
  «Portali al secondo acquisto e sono tuoi» qui non e' vero.""")

    # Se la sopravvivenza e' davvero costante, il numero di ordini deve essere
    # una geometrica. E' un'ipotesi che si puo' controllare, quindi si controlla.
    atteso = 1 / (1 - p)
    print(f"\n  Controllo: con una sopravvivenza costante il numero di ordini")
    print(f"  segue una geometrica. Confronto fra quello che quel modello")
    print(f"  prevede e quello che si osserva:\n")
    print(f"    ordini medi per cliente    attesi {atteso:5.2f}    osservati {pc['ordini_365'].mean():5.2f}")
    print("\n     ordini   attesa  osservata")
    for k in range(1, 8):
        q = (p ** (k - 1)) * (1 - p)
        print(f"     {k:>5}    {q * 100:5.1f}%    {(pc['ordini_365'] == k).mean() * 100:6.1f}%")
    print("""
  Fino al sesto ordine lo scarto sta sotto il mezzo punto. Piu' in la' la
  sopravvivenza sale davvero (dal 74% al 77%): li' non e' piu' il tempo, sono i
  clienti — chi ha gia' comprato otto volte e' un negozio che si rifornisce, e
  non somiglia piu' agli altri.""")

    titolo(6, "Quanto tempo passa fra il primo e il secondo ordine")
    sec = dentro[dentro["n_ordine"] == 2]["giorni_dal_precedente"].dropna()
    print(f"  clienti che arrivano al secondo entro la finestra: {len(sec):,}\n")
    for q in (0.25, 0.50, 0.75, 0.90):
        print(f"    {int(q * 100)}o percentile: {sec.quantile(q):>4.0f} giorni")
    print("\n  Letto come soglia operativa:")
    for giorni in (30, 60, 90, 120, 180):
        print(f"    entro {giorni:>3} giorni e' gia' tornato il "
              f"{(sec <= giorni).mean() * 100:5.1f}% di chi torna entro l'anno")
    print("""
  Non c'e' un burrone: la curva non ha un punto in cui la probabilita' crolla.
  A 90 giorni sono tornati sei su dieci, a 180 poco piu' di otto. Chi cercava
  una soglia netta oltre la quale «il cliente e' perso» qui non la trova, e
  dichiararne una sarebbe inventarla.""")

    # ── il valore ────────────────────────────────────────────────────────
    titolo(7, "Quanto vale chi torna, contro chi si ferma al primo ordine")
    a = pc.loc[pc["torna"], "speso_365"].to_numpy(dtype=float)
    b = pc.loc[~pc["torna"], "speso_365"].to_numpy(dtype=float)
    print(f"  chi torna      {len(a):>6,} clienti   media {a.mean():>9,.0f}   mediana {np.median(a):>8,.0f}")
    print(f"  chi non torna  {len(b):>6,} clienti   media {b.mean():>9,.0f}   mediana {np.median(b):>8,.0f}")
    print("\n  Media e mediana sono lontane: la distribuzione ha una coda lunga e la")
    print("  media la sente. Si mostrano tutte e due, non si sceglie la piu' comoda.")

    grezza = a.mean() - b.mean()
    d_boot = np.array([a[rng.integers(0, len(a), len(a))].mean()
                       - b[rng.integers(0, len(b), len(b))].mean()
                       for _ in range(RIPETIZIONI)])
    lo, hi = np.percentile(d_boot, [2.5, 97.5])
    print(f"\n  differenza grezza: {grezza:>7,.0f}   IC 95% [{lo:,.0f}, {hi:,.0f}]"
          f"   ({a.mean() / b.mean():.1f}x)")
    print("""  L'intervallo viene da 2.000 ricampionamenti dei CLIENTI, non degli ordini:
  ricampionare gli ordini tratterebbe due acquisti dello stesso cliente come
  due osservazioni indipendenti, e restituirebbe un intervallo troppo stretto.""")

    titolo(8, "La stessa differenza, fra clienti che partivano uguali")
    print("""  Chi torna era gia' diverso il primo giorno: se ha speso di piu' al primo
  ordine spendera' di piu' anche in totale, e quella parte del divario non
  dipende dal ritorno. Si confrontano allora clienti appaiati per decile di
  primo ordine e per coorte, e si guarda quanto della differenza sopravvive.""")
    pc["decile"] = pd.qcut(pc["valore_primo"], 10, labels=False, duplicates="drop")
    pezzi, pesi = [], []
    for _, g in pc.groupby(["decile", "coorte"], observed=True):
        ga, gb = g.loc[g["torna"], "speso_365"], g.loc[~g["torna"], "speso_365"]
        if len(ga) >= 3 and len(gb) >= 3:
            pezzi.append(ga.mean() - gb.mean())
            pesi.append(len(g))
    pezzi, pesi = np.array(pezzi), np.array(pesi, dtype=float)
    coperti = int(pesi.sum())
    app = float(np.average(pezzi, weights=pesi))
    boot = np.empty(RIPETIZIONI)
    for i in range(RIPETIZIONI):
        k = rng.integers(0, len(pezzi), len(pezzi))
        boot[i] = np.average(pezzi[k], weights=pesi[k])
    lo_a, hi_a = np.percentile(boot, [2.5, 97.5])
    print(f"\n  strati con almeno 3 clienti per parte: {len(pezzi)}"
          f"  ({coperti:,} clienti su {len(pc):,}, il {coperti / len(pc) * 100:.0f}%)")
    print(f"  differenza appaiata: {app:>7,.0f}   IC 95% [{lo_a:,.0f}, {hi_a:,.0f}]")
    print(f"  resta il {app / grezza * 100:.0f}% della differenza grezza:"
          f" l'appaiamento ne toglie il {(1 - app / grezza) * 100:.0f}%.")

    # da dove arrivano i soldi in piu'
    tornati = dentro.merge(pc[["cliente_id", "torna"]], on="cliente_id")
    tornati = tornati[tornati["torna"]]
    secondo = tornati[tornati["n_ordine"] == 2]["valore"].sum() / len(a)
    oltre = tornati[tornati["n_ordine"] > 2]["valore"].sum() / len(a)
    print("\n  Da dove arriva il maggior ricavo, per cliente che torna:")
    print(f"    il secondo ordine        {secondo:>8,.0f}")
    print(f"    dal terzo in poi         {oltre:>8,.0f}")
    print(f"  Il secondo ordine porta solo il {secondo / (secondo + oltre) * 100:.0f}% "
          f"del maggior ricavo.")
    print("""
  E si incastra con la sezione 5. Se la sopravvivenza e' la stessa a ogni
  gradino, un cliente portato al secondo ordine non ha comprato una volta in
  piu': e' entrato in una fila in cui ogni passo ha la stessa probabilita' di
  averne un altro dietro. Quello che si compra riattivandolo non e' il secondo
  ordine, e' la coda che gli si apre dietro — ed e' li' che stanno i quattro
  quinti dei soldi.""")

    titolo(9, "Il punto di pareggio, e cosa non dice")
    print(f"""  La cifra su cui si decide e' quella appaiata: {app:,.0f} in piu' in un anno,
  con un intervallo fra {lo_a:,.0f} e {hi_a:,.0f}.

  Riattivare conviene finche' costa meno di   margine x differenza.
  Il margine non sta nei dati — non c'e' il costo del venduto — quindi resta
  una manopola, e la tabella si legge per righe:

     {'margine':>8}   {'soglia sulla stima':>19}   {'soglia prudente':>16}""")
    for m in (0.10, 0.20, 0.30, 0.40, 0.50):
        print(f"     {m * 100:>7.0f}%   {m * app:>19,.0f}   {m * lo_a:>16,.0f}")
    print("""
  La colonna di destra usa il capo basso dell'intervallo: e' la soglia che
  regge anche se la stima e' ottimista, ed e' quella da portare a una riunione.

  Cosa NON dice questo numero. L'appaiamento toglie il pezzo di divario dovuto
  al fatto che certi clienti partivano gia' piu' grossi. Non toglie quello che
  non si e' misurato: chi torna magari aveva un bisogno ricorrente fin
  dall'inizio, e sarebbe tornato comunque. Il conto vale se un cliente convinto
  a tornare poi si comporta come i clienti che tornano da soli — ed e'
  un'ipotesi, non un risultato. Con dati osservativi non si dimostra:
  servirebbe un test in cui la riattivazione viene assegnata a caso.""")

    # ── 2/10/2026: la stessa domanda senza girare in tondo ──────────────
    titolo(10, "Corretto: il gruppo nei primi 90 giorni, la spesa dopo")
    v = valore_futuro.misura(dentro, tenuti.set_index("cliente_id")["coorte"], rng)
    pp, ps = v["pari_partenza"], v["pari_spesa_90"]
    print(f"""  Le sezioni 7-9 misuravano la spesa dello stesso anno che definiva chi
  torna: la differenza conteneva per costruzione gli ordini del ritorno.
  Qui i primi {valore_futuro.TAGLIO} giorni decidono il gruppo, e la spesa si conta dopo.

  clienti                              {v['clienti']:>7,}
  tornati entro {valore_futuro.TAGLIO} giorni                {v['tornati']:>7,}   ({v['quota_tornati']}%)

  spesa dal giorno 91 al 365     media   mediana   compra ancora
    tornati entro 90 giorni     {v['tornati_media']:>6,}    {v['tornati_mediana']:>6,}        {v['tornati_ancora']}%
    non tornati                 {v['altri_media']:>6,}    {v['altri_mediana']:>6,}        {v['altri_ancora']}%

  differenza grezza                    {v['grezza']:>6,}   IC [{v['grezza_ic'][0]:,}, {v['grezza_ic'][1]:,}]
  a parita' di primo ordine e coorte   {pp['stima']:>6,}   IC [{pp['ic'][0]:,}, {pp['ic'][1]:,}]
  a parita' di spesa nei 90 giorni     {ps['stima']:>6,}   IC [{ps['ic'][0]:,}, {ps['ic'][1]:,}]

  La seconda riga dice che chi torna presto spende di piu' anche dopo, a parita'
  di partenza. La terza dice che, a parita' di quanto ha gia' speso nei primi
  tre mesi, sapere che ha fatto piu' di un ordine non aggiunge quasi niente alla
  previsione: l'intervallo comprende lo zero. Per prevedere la spesa futura basta
  la spesa iniziale; il numero di ordini non dice di piu'.

  Attenzione a cosa NON dice. La spesa dei primi 90 giorni contiene gia' il
  secondo ordine: appaiare su di lei toglie anche una parte del ritorno stesso.
  E' una lettura predittiva, non causale. «Conta il volume» descrive cosa
  prevede la spesa futura, non dimostra che il ritorno non abbia effetto.

  Cade comunque la soglia della sezione 9, che assumeva che un cliente riportato
  al secondo ordine si comporti come chi torna da solo: questi numeri dicono che
  chi torna da solo e' soprattutto chi spende gia' di piu'.""")


def main():
    (QUI / "risultati").mkdir(exist_ok=True)
    eng = create_engine(url(), pool_pre_ping=True)
    rng = np.random.default_rng(SEME)
    d = matrice(eng)
    stagionalita(d)
    decrescita(d)
    valore(eng, rng)
    print(f"\n{'=' * 76}\nmatrice salvata in risultati/matrice_retention.csv\n{'=' * 76}")


if __name__ == "__main__":
    main()
