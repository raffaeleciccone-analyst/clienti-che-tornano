"""Il valore di chi torna, misurato senza girare in tondo.

Aggiunto il 2 ottobre 2026, dopo una revisione esterna.

Il confronto della sezione 7-8 di RISULTATI.md definiva «chi torna» con gli ordini
del primo anno (ordini > 1) e poi misurava la spesa dello STESSO anno. La spesa
in piu' di chi torna era quindi, per costruzione, il valore degli ordini che lo
facevano contare come «uno che torna»: il confronto misurava la propria
definizione.

Qui il tempo si taglia in due:
  - i primi 90 giorni dal primo ordine decidono il gruppo (tornato o no);
  - la spesa si misura dopo, dal giorno 91 al 365.
Cosi' l'esito non contiene gli ordini che definiscono il gruppo.

E si appaia in due modi, perche' rispondono a due domande diverse:
  - per decile del primo ordine e coorte: a parita' di partenza;
  - per decile della spesa nei primi 90 giorni e coorte: a parita' di quanto il
    cliente ha gia' comprato quando si decide se riattivarlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TAGLIO = 90       # giorni che decidono il gruppo
FINESTRA = 365    # fine della misura
MIN_PER_PARTE = 3
RIPETIZIONI = 2000


def _appaiata(pc: pd.DataFrame, strato: list[str], rng) -> dict:
    pezzi, pesi = [], []
    for _, g in pc.groupby(strato, observed=True):
        ga = g.loc[g["tornato"], "speso_dopo"]
        gb = g.loc[~g["tornato"], "speso_dopo"]
        if len(ga) >= MIN_PER_PARTE and len(gb) >= MIN_PER_PARTE:
            pezzi.append(ga.mean() - gb.mean())
            pesi.append(len(g))
    pezzi, pesi = np.array(pezzi), np.array(pesi, dtype=float)
    stima = float(np.average(pezzi, weights=pesi))
    boot = np.empty(RIPETIZIONI)
    for i in range(RIPETIZIONI):
        k = rng.integers(0, len(pezzi), len(pezzi))
        boot[i] = np.average(pezzi[k], weights=pesi[k])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"stima": round(stima), "ic": [round(float(lo)), round(float(hi))],
            "clienti": int(pesi.sum()), "strati": int(len(pezzi))}


def misura(ordini: pd.DataFrame, coorte: pd.Series, rng) -> dict:
    """ordini: una riga per fattura, con cliente_id, fattura, data, primo (data del
    primo ordine), n_ordine, valore; solo clienti con 365 giorni osservabili.
    coorte: la coorte di ogni cliente, indicizzata per cliente_id."""
    o = ordini.copy()
    o["g"] = (o["data"] - o["primo"]).dt.days
    o = o[o["g"] <= FINESTRA]
    prima = o[o["g"] <= TAGLIO].groupby("cliente_id").agg(
        ordini_90=("fattura", "nunique"), speso_90=("valore", "sum"))
    dopo = o[o["g"] > TAGLIO].groupby("cliente_id").agg(speso_dopo=("valore", "sum"))
    primo = o[o["n_ordine"] == 1].groupby("cliente_id")["valore"].first().rename("valore_primo")
    pc = prima.join(dopo).join(primo)
    pc["speso_dopo"] = pc["speso_dopo"].fillna(0.0)
    pc["coorte"] = coorte.reindex(pc.index).values
    pc["tornato"] = pc["ordini_90"] > 1

    a = pc.loc[pc["tornato"], "speso_dopo"].to_numpy(float)
    b = pc.loc[~pc["tornato"], "speso_dopo"].to_numpy(float)
    boot = np.array([a[rng.integers(0, len(a), len(a))].mean()
                     - b[rng.integers(0, len(b), len(b))].mean() for _ in range(RIPETIZIONI)])

    pc["dec_primo"] = pd.qcut(pc["valore_primo"], 10, labels=False, duplicates="drop")
    pc["dec_90"] = pd.qcut(pc["speso_90"], 10, labels=False, duplicates="drop")
    return {
        "clienti": int(len(pc)),
        "tornati": int(len(a)),
        "quota_tornati": round(len(a) / len(pc) * 100, 1),
        "tornati_media": round(float(a.mean())), "tornati_mediana": round(float(np.median(a))),
        "altri_media": round(float(b.mean())), "altri_mediana": round(float(np.median(b))),
        "tornati_ancora": round(float((a > 0).mean()) * 100, 1),
        "altri_ancora": round(float((b > 0).mean()) * 100, 1),
        "grezza": round(float(a.mean() - b.mean())),
        "grezza_ic": [round(float(x)) for x in np.percentile(boot, [2.5, 97.5])],
        "pari_partenza": _appaiata(pc, ["dec_primo", "coorte"], rng),
        "pari_spesa_90": _appaiata(pc, ["dec_90", "coorte"], rng),
    }
