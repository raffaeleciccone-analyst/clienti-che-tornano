"""Estrae quello che serve alla pagina, e nient'altro.

La pagina non rifa' i conti: legge questo file. Cosi' se un numero sulla pagina
non torna con RISULTATI.md, il colpevole e' uno solo e sta qui.

Uso:  python 08_dati_pagina.py   ->  sito/dati.json
"""
from __future__ import annotations

import json
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
USCITA = QUI / "sito" / "dati.json"
FINESTRA = 365
SEME = 20260827
COORTI_FUORI = ("2009-12", "2011-12")


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


def main() -> None:
    eng = create_engine(url(), pool_pre_ping=True)
    rng = np.random.default_rng(SEME)
    d = {}

    # ── la matrice ───────────────────────────────────────────────────────
    m = pd.read_sql(text("""
        SELECT coorte, mese_relativo, clienti_attivi, clienti_entrati,
               quota_attivi, mesi_osservabili
        FROM v_retention_coorte
    """), eng, parse_dates=["coorte"])
    m = m[~m["coorte"].dt.strftime("%Y-%m").isin(COORTI_FUORI)]
    m = m[m["mese_relativo"] <= m["mesi_osservabili"]]

    coorti = []
    for c, g in m.groupby("coorte"):
        celle = g.set_index("mese_relativo")["quota_attivi"].to_dict()
        coorti.append({
            "coorte": f"{c:%Y-%m}",
            "anno": c.year, "mese": c.month,
            "entrati": int(g["clienti_entrati"].iloc[0]),
            "celle": [round(float(celle[k]), 1) if k in celle else None
                      for k in range(0, int(g["mese_relativo"].max()) + 1)],
        })
    d["coorti"] = coorti

    vivi = m[m["mese_relativo"] >= 1].copy()
    vivi["cal"] = (vivi["coorte"].dt.to_period("M") + vivi["mese_relativo"]).dt.month
    quando = (vivi["coorte"].dt.to_period("M") + vivi["mese_relativo"])
    d["per_mese_calendario"] = [
        {"mese": int(k), "quota": round(float(v), 1),
         "anni": sorted({int(a) for a in quando[vivi["cal"] == k].dt.year})}
        for k, v in vivi.groupby("cal")["quota_attivi"].mean().items()]

    def spiegata(gruppo):
        med = vivi.groupby(gruppo)["quota_attivi"].transform("mean")
        return round(float(1 - ((vivi["quota_attivi"] - med) ** 2).sum()
                           / ((vivi["quota_attivi"] - vivi["quota_attivi"].mean()) ** 2).sum()) * 100, 1)

    d["spiegata"] = {"eta": spiegata("mese_relativo"),
                     "calendario": spiegata("cal"),
                     "insieme": spiegata(["mese_relativo", "cal"])}

    bil = vivi[vivi["mesi_osservabili"] >= 12]
    d["panel_bilanciato"] = {
        "coorti": int(bil["coorte"].nunique()),
        "curva": [{"mese": int(k), "quota": round(float(v), 1)} for k, v in
                  bil[bil["mese_relativo"] <= 12].groupby("mese_relativo")["quota_attivi"].mean().items()]}

    # ── il campione del valore ───────────────────────────────────────────
    o = pd.read_sql(text("""
        SELECT fattura, cliente_id, data, valore, n_ordine, giorni_dal_precedente,
               data_primo_ordine, coorte
        FROM v_ordini_sequenza
    """), eng, parse_dates=["data", "data_primo_ordine", "coorte"])
    ultimo = o["data"].max()
    cl = o.groupby("cliente_id").agg(primo=("data_primo_ordine", "first"),
                                     coorte=("coorte", "first"))
    fuori = cl["coorte"].dt.strftime("%Y-%m").isin(COORTI_FUORI)
    tenuti = cl[(cl["primo"] <= ultimo - pd.Timedelta(days=FINESTRA)) & ~fuori]
    dd = o[o["cliente_id"].isin(tenuti.index)].copy()
    dd["primo"] = tenuti.loc[dd["cliente_id"], "primo"].values
    dd = dd[(dd["data"] - dd["primo"]).dt.days <= FINESTRA]

    pc = dd.groupby("cliente_id").agg(ordini=("fattura", "nunique"),
                                      speso=("valore", "sum")).reset_index()
    pc["coorte"] = tenuti.loc[pc["cliente_id"], "coorte"].values
    pc = pc.merge(dd[dd["n_ordine"] == 1].set_index("cliente_id")["valore"]
                  .rename("primo_valore"), on="cliente_id", how="left")
    pc["torna"] = pc["ordini"] > 1

    n = len(pc)
    d["campione"] = {"clienti": int(n), "totali": int(len(cl)),
                     "coorte_da": f"{tenuti['coorte'].min():%Y-%m}",
                     "coorte_a": f"{tenuti['coorte'].max():%Y-%m}"}

    funnel, prec = [], n
    for g in range(1, 9):
        arr = int((pc["ordini"] >= g).sum())
        funnel.append({"gradino": g, "clienti": arr, "quota": round(arr / n * 100, 1),
                       "sopravvive": None if g == 1 else round(arr / prec * 100, 1)})
        prec = arr
    d["funnel"] = funnel
    p = float(np.mean([f["sopravvive"] / 100 for f in funnel[1:6]]))
    d["sopravvivenza_media"] = round(p * 100, 1)
    d["geometrica"] = [{"ordini": k,
                        "attesa": round((p ** (k - 1)) * (1 - p) * 100, 1),
                        "osservata": round(float((pc["ordini"] == k).mean()) * 100, 1)}
                       for k in range(1, 7)]

    sec = dd[dd["n_ordine"] == 2]["giorni_dal_precedente"].dropna()
    d["tempo_secondo"] = {
        "clienti": int(len(sec)),
        "percentili": {str(int(q * 100)): int(round(sec.quantile(q))) for q in (.25, .5, .75, .9)},
        "cumulata": [{"giorni": g, "quota": round(float((sec <= g).mean()) * 100, 1)}
                     for g in range(10, 366, 10)]}

    a = pc.loc[pc["torna"], "speso"].to_numpy(float)
    b = pc.loc[~pc["torna"], "speso"].to_numpy(float)
    grezza = float(a.mean() - b.mean())
    boot = np.array([a[rng.integers(0, len(a), len(a))].mean()
                     - b[rng.integers(0, len(b), len(b))].mean() for _ in range(2000)])
    pc["decile"] = pd.qcut(pc["primo_valore"], 10, labels=False, duplicates="drop")
    pezzi, pesi = [], []
    for _, g in pc.groupby(["decile", "coorte"], observed=True):
        ga, gb = g.loc[g["torna"], "speso"], g.loc[~g["torna"], "speso"]
        if len(ga) >= 3 and len(gb) >= 3:
            pezzi.append(ga.mean() - gb.mean())
            pesi.append(len(g))
    pezzi, pesi = np.array(pezzi), np.array(pesi, float)
    app = float(np.average(pezzi, weights=pesi))
    bapp = np.empty(2000)
    for i in range(2000):
        k = rng.integers(0, len(pezzi), len(pezzi))
        bapp[i] = np.average(pezzi[k], weights=pesi[k])
    lo_a, hi_a = np.percentile(bapp, [2.5, 97.5])

    t = dd.merge(pc[["cliente_id", "torna"]], on="cliente_id")
    t = t[t["torna"]]
    d["valore"] = {
        "torna": {"clienti": int(len(a)), "media": round(float(a.mean())),
                  "mediana": round(float(np.median(a)))},
        "non_torna": {"clienti": int(len(b)), "media": round(float(b.mean())),
                      "mediana": round(float(np.median(b)))},
        "grezza": round(grezza), "grezza_ic": [round(float(x)) for x in np.percentile(boot, [2.5, 97.5])],
        "appaiata": round(app), "appaiata_ic": [round(float(lo_a)), round(float(hi_a))],
        "strati": int(len(pezzi)), "coperti": round(float(pesi.sum() / n * 100)),
        "secondo_ordine": round(float(t[t["n_ordine"] == 2]["valore"].sum() / len(a))),
        "dal_terzo": round(float(t[t["n_ordine"] > 2]["valore"].sum() / len(a)))}

    # il limite: quanto e' largo il tasso di ritorno vero
    d["anonimi"] = {"fatture": 8752, "clienti_noti": 5852, "tornano": 4234,
                    "quota_alta": 72.3,
                    "quota_bassa": round(4234 / (5852 + 8752) * 100, 1)}

    USCITA.parent.mkdir(exist_ok=True)
    USCITA.write_text(json.dumps(d, ensure_ascii=False, indent=1, allow_nan=False),
                      encoding="utf-8")
    print(f"scritto {USCITA}  ({USCITA.stat().st_size / 1024:.0f} KB)")
    print(f"  coorti {len(d['coorti'])}   funnel {len(d['funnel'])}   "
          f"cumulata {len(d['tempo_secondo']['cumulata'])} punti")
    print(f"  appaiata {d['valore']['appaiata']:,} "
          f"[{d['valore']['appaiata_ic'][0]:,}, {d['valore']['appaiata_ic'][1]:,}]")


if __name__ == "__main__":
    main()
