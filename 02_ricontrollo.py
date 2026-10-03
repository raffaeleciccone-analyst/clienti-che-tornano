"""Ricontrolla le affermazioni scritte in DATI-SPORCHI.md.

Non ripete il censimento: prende le frasi che finiscono nel documento e prova a
smentirle una per una. Se una verifica fallisce, il documento va corretto, non il
controllo.

Uso:  python 02_ricontrollo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FILE = Path(__file__).parent / "dati_grezzi" / "online_retail_II.xlsx"
CHIAVE = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"]
NON_PRODOTTI = {"POST", "DOT", "M", "m", "C2", "C3", "D", "S", "BANK CHARGES",
                "AMAZONFEE", "ADJUST", "ADJUST2", "TEST001", "TEST002", "PADS",
                "SP1002", "B", "CRUK", "gift_0001_10", "gift_0001_20",
                "gift_0001_30", "gift_0001_40", "gift_0001_50"}

esiti = []


def controlla(nome, condizione, dettaglio=""):
    esiti.append((nome, bool(condizione), dettaglio))
    print(f"  [{'ok ' if condizione else 'NO '}] {nome}")
    if dettaglio:
        print(f"         {dettaglio}")


def main() -> None:
    fogli = pd.read_excel(FILE, sheet_name=None)
    for n, d in fogli.items():
        d["foglio"] = n
    df = pd.concat(fogli.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    df["Invoice"] = df["Invoice"].astype(str)
    ric = df["Quantity"] * df["Price"]

    print("\n== 1. La sovrapposizione fra i fogli ==")
    per_foglio = {n: set(d["Invoice"].astype(str)) for n, d in fogli.items()}
    nomi = list(per_foglio)
    comuni = per_foglio[nomi[0]] & per_foglio[nomi[1]]
    righe_comuni = df["Invoice"].isin(comuni)
    dup_esatti = df.duplicated(subset=CHIAVE, keep=False)
    controlla("1.088 fatture in comune", len(comuni) == 1088, f"trovate {len(comuni)}")
    controlla("45.046 righe su fatture in comune", int(righe_comuni.sum()) == 45046,
              f"trovate {int(righe_comuni.sum()):,}")

    # Il punto che avevo dato per scontato: le righe delle fatture in comune sono
    # TUTTE duplicati esatti, o alcune differiscono?
    non_dup = righe_comuni & ~dup_esatti
    print(f"\n  righe su fatture in comune ma NON duplicati esatti: {int(non_dup.sum()):,}")
    if int(non_dup.sum()):
        campione = df[non_dup].sort_values(["Invoice", "StockCode"]).head(6)
        print(campione[["Invoice", "StockCode", "Quantity", "Price", "Customer ID", "foglio"]]
              .to_string(index=False))
        # una stessa fattura+articolo che compare nei due fogli con valori diversi?
        cop = df[righe_comuni].groupby(["Invoice", "StockCode"])["foglio"].nunique()
        print(f"\n  coppie fattura+articolo presenti in tutti e due i fogli: "
              f"{int((cop > 1).sum()):,} su {len(cop):,}")

    print("\n== 2. Duplicati esatti ==")
    n_dup_da_togliere = int(df.duplicated(subset=CHIAVE).sum())
    controlla("34.337 righe da togliere", n_dup_da_togliere == 34337,
              f"trovate {n_dup_da_togliere:,}")
    # quanti dei duplicati vengono dalla sovrapposizione, e quanti sono interni a un foglio?
    d = df[dup_esatti]
    per_gruppo = d.groupby(CHIAVE, dropna=False)["foglio"].nunique()
    fra_fogli = int((per_gruppo > 1).sum())
    print(f"  gruppi di duplicati che stanno a cavallo dei due fogli: {fra_fogli:,}")
    print(f"  gruppi di duplicati interni a un solo foglio          : {int((per_gruppo == 1).sum()):,}")

    print("\n== 3. Le righe senza cliente valgono il 13,7% del ricavo ==")
    senza = df["Customer ID"].isna()
    q = ric[senza].sum() / ric.sum() * 100
    controlla("13,7% del ricavo lordo", abs(q - 13.7) < 0.15, f"calcolato {q:.2f}%")
    # e su una base più onesta: senza duplicati e senza storni
    pulito = ~df.duplicated(subset=CHIAVE) & ~df["Invoice"].str.startswith("C")
    q2 = ric[senza & pulito].sum() / ric[pulito].sum() * 100
    print(f"  la stessa quota su base deduplicata e senza storni: {q2:.2f}%")

    print("\n== 4. Le negative fuori dagli storni sono tutte senza cliente ==")
    storno = df["Invoice"].str.startswith("C")
    fuori = (df["Quantity"] < 0) & ~storno
    controlla("tutte senza cliente", int((fuori & ~senza).sum()) == 0,
              f"con cliente: {int((fuori & ~senza).sum())} su {int(fuori.sum()):,}")

    print("\n== 5. I buoni regalo: quante righe davvero ==")
    cod = df["StockCode"].astype(str)
    n_gift = int(cod.str.startswith("gift_0001").sum())
    print(f"  righe con codice gift_0001_*: {n_gift}")
    controlla("«circa 90» è onesto", 60 <= n_gift <= 130, f"sono {n_gift}")

    print("\n== 6. La sequenza di pulizia ==")
    m = pd.Series(True, index=df.index)
    tappe = {}
    m &= ~df.duplicated(subset=CHIAVE);           tappe["dopo duplicati"] = int(m.sum())
    m &= ~senza;                                  tappe["dopo senza cliente"] = int(m.sum())
    m &= ~storno;                                 tappe["dopo storni"] = int(m.sum())
    m &= df["Quantity"] > 0;                      tappe["dopo quantita"] = int(m.sum())
    m &= df["Price"] > 0;                         tappe["dopo prezzi"] = int(m.sum())
    m &= ~cod.isin(NON_PRODOTTI);                 tappe["dopo non-prodotti"] = int(m.sum())
    attesi = {"dopo duplicati": 1033034, "dopo senza cliente": 797883,
              "dopo storni": 779493, "dopo quantita": 779493,
              "dopo prezzi": 779423, "dopo non-prodotti": 776575}
    for k, atteso in attesi.items():
        controlla(f"{k} = {atteso:,}", tappe[k] == atteso, f"trovato {tappe[k]:,}")

    fin = df[m]
    controlla("5.852 clienti finali", int(fin["Customer ID"].nunique()) == 5852,
              f"trovati {int(fin['Customer ID'].nunique()):,}")
    controlla("36.594 fatture finali", fin["Invoice"].nunique() == 36594,
              f"trovate {fin['Invoice'].nunique():,}")

    print("\n== 7. «Esce il 27,2% delle righe ma solo l'11,5% del ricavo» ==")
    ric_fin = (fin["Quantity"] * fin["Price"]).sum()
    perse_righe = (1 - len(fin) / len(df)) * 100
    # Il confronto onesto NON è contro il lordo, che dentro ha i duplicati e gli
    # storni negativi: è contro il lordo deduplicato, senza il quale il
    # denominatore è esso stesso sbagliato.
    ric_lordo = ric.sum()
    ric_dedup = ric[~df.duplicated(subset=CHIAVE)].sum()
    print(f"  righe perse            : {perse_righe:.1f}%")
    print(f"  ricavo finale / lordo  : {ric_fin / ric_lordo * 100:.1f}%  (perso {100 - ric_fin / ric_lordo * 100:.1f}%)")
    print(f"  ricavo finale / dedup. : {ric_fin / ric_dedup * 100:.1f}%  (perso {100 - ric_fin / ric_dedup * 100:.1f}%)")
    print("  -> il secondo è il confronto giusto: il lordo contiene le copie")

    print("\n== 8. Il riacquisto ==")
    per_cliente = fin.groupby("Customer ID")["Invoice"].nunique()
    rip = int((per_cliente > 1).sum())
    quota = rip / len(per_cliente) * 100
    controlla("72,3% torna", abs(quota - 72.3) < 0.15, f"calcolato {quota:.2f}%")

    print("\n" + "=" * 66)
    falliti = [n for n, ok, _ in esiti if not ok]
    print(f"  {len(esiti) - len(falliti)}/{len(esiti)} verifiche passate")
    if falliti:
        print("  DA CORREGGERE NEL DOCUMENTO:")
        for n in falliti:
            print("   -", n)


if __name__ == "__main__":
    main()
