"""Ricontrolla le cifre scritte in RISULTATI.md.

Non rilancia `05_analisi.py`: rifarebbe gli stessi passaggi e confermerebbe gli
stessi errori. Qui i conti si rifanno dalle tabelle di base — `ordini` e
`clienti` — senza passare dalle viste, cosi' se una vista e' sbagliata la
differenza salta fuori.

Ogni riga stampa [ok] o [NO] e il valore trovato accanto a quello scritto.

Uso:  python 06_ricontrollo.py
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

esiti: list[bool] = []


def url() -> str:
    pwd = os.environ.get("DB_PASSWORD", "")
    if not pwd:
        env = QUI.parent / "serie-a-index-engine" / ".env"
        if env.is_file():
            for r in env.read_text(encoding="utf-8").splitlines():
                if r.startswith("DB_PASSWORD="):
                    pwd = r.split("=", 1)[1].strip()
    if not pwd:
        raise SystemExit("Manca DB_PASSWORD.")
    from urllib.parse import quote_plus
    return f"mysql+pymysql://root:{quote_plus(pwd)}@localhost/retail_clienti"


def prova(etichetta, trovato, scritto, tolleranza=0.05):
    ok = abs(float(trovato) - float(scritto)) <= tolleranza
    esiti.append(ok)
    print(f"  [{'ok' if ok else 'NO'}] {etichetta:<52} {trovato:>10,.1f}  (scritto {scritto:,})")


def sezione(t):
    print(f"\n── {t} " + "─" * max(0, 68 - len(t)))


def main() -> None:
    eng = create_engine(url(), pool_pre_ping=True)
    rng = np.random.default_rng(SEME)

    # tutto ricostruito da zero dalle tabelle di base
    o = pd.read_sql(text("SELECT fattura, cliente_id, data, data_ora, valore FROM ordini"),
                    eng, parse_dates=["data", "data_ora"])
    o = o.sort_values(["cliente_id", "data_ora", "fattura"])
    o["n"] = o.groupby("cliente_id").cumcount() + 1
    o["primo"] = o.groupby("cliente_id")["data"].transform("min")
    o["coorte"] = o["primo"].dt.to_period("M")
    o["m"] = (o["data"].dt.to_period("M") - o["coorte"]).apply(lambda x: x.n)
    ultimo = o["data"].max()
    # l'ultimo mese di cui si sono visti tutti i giorni
    ultimo_intero = (ultimo.to_period("M") if ultimo == ultimo.to_period("M").end_time.normalize()
                     else ultimo.to_period("M") - 1)

    print(f"ultimo giorno nei dati: {ultimo:%Y-%m-%d}   "
          f"ultimo mese intero: {ultimo_intero}")

    # ══ la matrice ═══════════════════════════════════════════════════════
    sezione("1. la matrice")
    u = o[~o["coorte"].astype(str).isin(COORTI_FUORI)]
    coorti = sorted(u["coorte"].unique())
    prova("coorti utili", len(coorti), 23, 0)

    entrati = u.groupby("coorte")["cliente_id"].nunique()
    righe = []
    for c in coorti:
        osservabili = (ultimo_intero - c).n
        g = u[u["coorte"] == c]
        for m in range(1, osservabili + 1):
            righe.append({"coorte": c, "m": m,
                          "quota": g[g["m"] == m]["cliente_id"].nunique() / entrati[c] * 100,
                          "osservabili": osservabili})
    mat = pd.DataFrame(righe)
    prova("celle osservate (m >= 1)", len(mat), 253, 0)

    # ══ la stagionalita' ═════════════════════════════════════════════════
    sezione("2. la stagionalita'")
    mat["cal"] = [(c + m).month for c, m in zip(mat["coorte"], mat["m"])]

    def spiegata(gruppo):
        med = mat.groupby(gruppo)["quota"].transform("mean")
        return (1 - ((mat["quota"] - med) ** 2).sum()
                / ((mat["quota"] - mat["quota"].mean()) ** 2).sum()) * 100

    prova("spiegata dal mese di vita", spiegata("m"), 16.6, 0.1)
    prova("spiegata dal mese del calendario", spiegata("cal"), 34.8, 0.1)
    prova("spiegata dai due insieme", spiegata(["m", "cal"]), 85.8, 0.1)

    per_mese = mat.groupby("cal")["quota"].mean()
    prova("novembre", per_mese[11], 25.0, 0.1)
    prova("gennaio", per_mese[1], 11.3, 0.1)
    prova("dicembre", per_mese[12], 13.8, 0.1)

    # il dicembre e il gennaio poggiano su un anno solo?
    for mese, nome in ((12, "dicembre"), (1, "gennaio")):
        anni = {(c + m).year for c, m in zip(mat.loc[mat["cal"] == mese, "coorte"],
                                             mat.loc[mat["cal"] == mese, "m"])}
        prova(f"{nome}: quanti anni distinti", len(anni), 1, 0)

    # la coorte di dicembre 2010
    dic = o[o["coorte"] == pd.Period("2010-12")]
    prova("coorte 2010-12: clienti", dic["cliente_id"].nunique(), 76, 0)
    prova("coorte 2010-12: quota al mese +1",
          dic[dic["m"] == 1]["cliente_id"].nunique() / dic["cliente_id"].nunique() * 100, 9, 0.6)

    # ══ il panel bilanciato ══════════════════════════════════════════════
    sezione("3. il panel bilanciato")
    bil = mat[mat["osservabili"] >= 12]
    prova("coorti nel panel", bil["coorte"].nunique(), 11, 0)
    for m, atteso in ((1, 19.8), (3, 21.5), (6, 17.6), (10, 13.1), (12, 17.9)):
        prova(f"panel bilanciato, mese +{m}",
              bil[bil["m"] == m]["quota"].mean(), atteso, 0.1)

    # ══ la finestra del valore ═══════════════════════════════════════════
    sezione("4. la finestra del valore")
    limite = ultimo - pd.Timedelta(days=FINESTRA)
    cl = o.groupby("cliente_id").agg(primo=("primo", "first"), coorte=("coorte", "first"))
    fuori = cl["coorte"].astype(str).isin(COORTI_FUORI)
    prova("clienti in tutto", len(cl), 5852, 0)
    prova("esclusi per coorte", int(fuori.sum()), 979, 0)
    prova("esclusi per finestra", int(((cl["primo"] > limite) & ~fuori).sum()), 1539, 0)
    tenuti = cl[(cl["primo"] <= limite) & ~fuori]
    prova("clienti nell'analisi del valore", len(tenuti), 3334, 0)
    prova("coorti tutte nel 2010",
          int(tenuti["coorte"].astype(str).str[:4].eq("2010").all()), 1, 0)

    # l'affermazione «24 mesi non si puo'»
    a_due_anni = cl[(cl["primo"] <= ultimo - pd.Timedelta(days=730)) & ~fuori]
    prova("clienti utili con 24 mesi interi", len(a_due_anni), 0, 0)

    # ══ il funnel ════════════════════════════════════════════════════════
    sezione("5. il funnel, dentro i 365 giorni")
    d = o[o["cliente_id"].isin(tenuti.index)]
    d = d[(d["data"] - d["primo"]).dt.days <= FINESTRA]
    nord = d.groupby("cliente_id")["fattura"].nunique()
    tot = len(nord)
    prova("clienti nel funnel", tot, 3334, 0)
    for g, atteso in ((2, 2373), (3, 1715), (4, 1249), (5, 905), (6, 657), (8, 371)):
        prova(f"arrivati al gradino {g}", int((nord >= g).sum()), atteso, 0)

    sopr = [int((nord >= g).sum()) / int((nord >= g - 1).sum()) for g in range(2, 7)]
    p = float(np.mean(sopr))
    prova("sopravvivenza media sui primi sei gradini", p * 100, 72.3, 0.1)
    prova("ordini medi attesi dalla geometrica", 1 / (1 - p), 3.61, 0.02)
    prova("ordini medi osservati", nord.mean(), 3.81, 0.02)

    # ══ il tempo al secondo ordine ═══════════════════════════════════════
    sezione("6. il tempo fra primo e secondo ordine")
    d = d.sort_values(["cliente_id", "data_ora", "fattura"])
    d["k"] = d.groupby("cliente_id").cumcount() + 1
    secondi = d[d["k"] == 2].copy()
    secondi["gg"] = (secondi["data"].values
                     - d[d["k"] == 1].set_index("cliente_id").loc[secondi["cliente_id"], "data"].values)
    gg = pd.Series(secondi["gg"]).dt.days
    prova("clienti che arrivano al secondo", len(gg), 2373, 0)
    for q, atteso in ((0.25, 26), (0.50, 64), (0.75, 139), (0.90, 231)):
        prova(f"percentile {int(q*100)}", gg.quantile(q), atteso, 1)
    for giorni, atteso in ((30, 28.4), (60, 48.2), (90, 60.9), (120, 70.1), (180, 83.3)):
        prova(f"tornati entro {giorni} giorni", (gg <= giorni).mean() * 100, atteso, 0.1)

    # ══ il valore ════════════════════════════════════════════════════════
    sezione("7. il valore")
    pc = d.groupby("cliente_id").agg(ordini=("fattura", "nunique"), speso=("valore", "sum"))
    pc["coorte"] = tenuti.loc[pc.index, "coorte"]
    pc["primo_valore"] = d[d["k"] == 1].set_index("cliente_id")["valore"]
    pc["torna"] = pc["ordini"] > 1
    a = pc.loc[pc["torna"], "speso"].to_numpy(dtype=float)
    b = pc.loc[~pc["torna"], "speso"].to_numpy(dtype=float)
    prova("chi torna: quanti", len(a), 2373, 0)
    prova("chi non torna: quanti", len(b), 961, 0)
    prova("chi torna: media", a.mean(), 1990, 1)
    prova("chi torna: mediana", np.median(a), 1091, 1)
    prova("chi non torna: media", b.mean(), 337, 1)
    prova("chi non torna: mediana", np.median(b), 229, 1)

    grezza = a.mean() - b.mean()
    prova("differenza grezza", grezza, 1653, 1)
    boot = np.array([a[rng.integers(0, len(a), len(a))].mean()
                     - b[rng.integers(0, len(b), len(b))].mean() for _ in range(2000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    prova("estremo basso dell'intervallo grezzo", lo, 1453, 15)
    prova("estremo alto dell'intervallo grezzo", hi, 1915, 15)

    sezione("8. la differenza appaiata")
    pc["decile"] = pd.qcut(pc["primo_valore"], 10, labels=False, duplicates="drop")
    pezzi, pesi = [], []
    for _, g in pc.groupby(["decile", "coorte"], observed=True):
        ga, gb = g.loc[g["torna"], "speso"], g.loc[~g["torna"], "speso"]
        if len(ga) >= 3 and len(gb) >= 3:
            pezzi.append(ga.mean() - gb.mean())
            pesi.append(len(g))
    pezzi, pesi = np.array(pezzi), np.array(pesi, dtype=float)
    app = float(np.average(pezzi, weights=pesi))
    prova("strati usati", len(pezzi), 105, 0)
    prova("clienti coperti dagli strati", pesi.sum() / len(pc) * 100, 95, 0.6)
    prova("differenza appaiata", app, 1374, 1)
    prova("quota della grezza che sopravvive", app / grezza * 100, 83, 0.6)
    boot = np.empty(2000)
    for i in range(2000):
        k = rng.integers(0, len(pezzi), len(pezzi))
        boot[i] = np.average(pezzi[k], weights=pesi[k])
    lo_a, hi_a = np.percentile(boot, [2.5, 97.5])
    prova("estremo basso dell'intervallo appaiato", lo_a, 1125, 20)
    prova("estremo alto dell'intervallo appaiato", hi_a, 1658, 20)

    sezione("9. da dove arrivano i soldi")
    t = d[d["cliente_id"].isin(pc.index[pc["torna"]])]
    secondo = t[t["k"] == 2]["valore"].sum() / len(a)
    oltre = t[t["k"] > 2]["valore"].sum() / len(a)
    prova("il secondo ordine, per cliente che torna", secondo, 348, 1)
    prova("dal terzo in poi", oltre, 1202, 1)
    prova("quota del secondo ordine", secondo / (secondo + oltre) * 100, 22, 0.6)

    sezione("la soglia di pareggio")
    prova("margine 20%, soglia prudente", 0.20 * lo_a, 225, 4)

    print(f"\n{'=' * 76}")
    print(f"controlli: {sum(esiti)} su {len(esiti)} passati")
    if not all(esiti):
        print("RISULTATI.md ha almeno una cifra da correggere.")
        sys.exit(1)
    print("Tutte le cifre di RISULTATI.md reggono al ricalcolo indipendente.")
    print("=" * 76)


if __name__ == "__main__":
    main()
