"""Applica le pulizie di DATI-SPORCHI.md e carica il modello in MySQL.

Ogni passaggio ha lo stesso nome che ha nel documento, e stampa quante righe
toglie: se un giorno i due numeri non coincidono piu', se ne accorge chi lancia
lo script, non chi legge i risultati sei mesi dopo.

Il file grezzo non viene mai modificato.

Uso:  python 04_carica.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUI = Path(__file__).parent
FILE = QUI / "dati_grezzi" / "online_retail_II.xlsx"
SCHEMA = QUI / "03_schema.sql"
DB = "retail_clienti"

CHIAVE = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"]

# Scritto a mano dopo aver guardato i codici, non dedotto da una regola: la
# regola «non comincia con cinque cifre» prende anche DCGS0058, che e' un
# prodotto vero. Vedi DATI-SPORCHI.md §5.
NON_PRODOTTI = {"POST", "DOT", "M", "m", "C2", "C3", "D", "S", "BANK CHARGES",
                "AMAZONFEE", "ADJUST", "ADJUST2", "TEST001", "TEST002", "PADS",
                "SP1002", "B", "CRUK", "gift_0001_10", "gift_0001_20",
                "gift_0001_30", "gift_0001_40", "gift_0001_50"}


def url() -> str:
    pwd = os.environ.get("DB_PASSWORD", "")
    if not pwd:
        # la stessa .env del motore Serie A, se c'e': una password sola sul portatile
        env = QUI.parent / "serie-a-index-engine" / ".env"
        if env.is_file():
            for r in env.read_text(encoding="utf-8").splitlines():
                if r.startswith("DB_PASSWORD="):
                    pwd = r.split("=", 1)[1].strip()
    if not pwd:
        raise SystemExit("Manca DB_PASSWORD nell'ambiente.")
    from urllib.parse import quote_plus
    return f"mysql+pymysql://root:{quote_plus(pwd)}@localhost/{DB}"


def passo(df: pd.DataFrame, nome: str, tieni: pd.Series) -> pd.DataFrame:
    prima = len(df)
    fuori = df[tieni]
    print(f"  {nome:<38} {len(fuori):>9,}  ({len(fuori) - prima:+,})")
    return fuori


def main() -> None:
    print("Lettura del grezzo...")
    fogli = pd.read_excel(FILE, sheet_name=None)
    df = pd.concat(fogli.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    # Invoice arriva con due tipi: interi per le fatture normali, stringhe per
    # gli storni. Vedi DATI-SPORCHI.md, nota al §1.
    df["Invoice"] = df["Invoice"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)

    print(f"\nPulizia — i nomi sono quelli di DATI-SPORCHI.md")
    print(f"  {'il file com e':<38} {len(df):>9,}")
    df = passo(df, "Togli le righe duplicate", ~df.duplicated(subset=CHIAVE))
    df = passo(df, "Tieni solo le righe con cliente", df["Customer ID"].notna())
    df = passo(df, "Togli le fatture di storno", ~df["Invoice"].str.startswith("C"))
    df = passo(df, "Togli i prezzi non positivi", df["Price"] > 0)
    df = passo(df, "Togli le quantita non positive", df["Quantity"] > 0)
    df = passo(df, "Togli i codici non-prodotto", ~df["StockCode"].isin(NON_PRODOTTI))

    df["cliente_id"] = df["Customer ID"].astype(int)
    df["valore"] = (df["Quantity"] * df["Price"]).round(2)
    df["data"] = df["InvoiceDate"].dt.date

    # ── ordini ───────────────────────────────────────────────────────────
    ordini = (df.groupby("Invoice")
                .agg(cliente_id=("cliente_id", "first"),
                     data_ora=("InvoiceDate", "min"),
                     n_righe=("Invoice", "size"),
                     n_pezzi=("Quantity", "sum"),
                     valore=("valore", "sum"),
                     paese=("Country", "first"))
                .reset_index()
                .rename(columns={"Invoice": "fattura"}))
    ordini["data"] = ordini["data_ora"].dt.date
    ordini["valore"] = ordini["valore"].round(2)

    # Una fattura con due clienti diversi sarebbe un difetto del modello, non
    # dei dati: si controlla invece di sperare.
    per_fattura = df.groupby("Invoice")["cliente_id"].nunique()
    if int((per_fattura > 1).sum()):
        print(f"\n  ATTENZIONE: {int((per_fattura > 1).sum())} fatture con piu' di un cliente")

    # ── clienti ──────────────────────────────────────────────────────────
    clienti = (ordini.groupby("cliente_id")
                     .agg(paese=("paese", "first"),
                          primo_ordine=("data", "min"),
                          ultimo_ordine=("data", "max"),
                          n_ordini=("fattura", "nunique"),
                          ricavo_totale=("valore", "sum"))
                     .reset_index())
    clienti["ricavo_totale"] = clienti["ricavo_totale"].round(2)

    # ── righe ────────────────────────────────────────────────────────────
    righe = df[["Invoice", "cliente_id", "StockCode", "Description",
                "Quantity", "Price", "valore", "InvoiceDate"]].copy()
    righe.columns = ["fattura", "cliente_id", "articolo", "descrizione",
                     "quantita", "prezzo", "valore", "data_ora"]
    righe["descrizione"] = righe["descrizione"].astype(str).str[:120]

    print(f"\nDa caricare: {len(clienti):,} clienti, {len(ordini):,} ordini, {len(righe):,} righe")

    eng = create_engine(url(), pool_pre_ping=True)
    print("\nCreazione dello schema...")
    ddl = SCHEMA.read_text(encoding="utf-8")
    with eng.begin() as cx:
        cx.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for istruzione in [s.strip() for s in ddl.split(";") if s.strip() and
                           not all(r.strip().startswith("--") for r in s.strip().splitlines())]:
            cx.execute(text(istruzione))
        cx.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print("Caricamento...")
    for nome, tab in (("clienti", clienti), ("ordini", ordini), ("righe", righe)):
        tab.to_sql(nome, eng, if_exists="append", index=False, chunksize=20_000)
        print(f"  {nome:<10} {len(tab):>9,}")

    # ── controlli dopo il caricamento ────────────────────────────────────
    print("\nControlli:")
    with eng.connect() as cx:
        prove = {
            "clienti": ("SELECT COUNT(*) FROM clienti", len(clienti)),
            "ordini": ("SELECT COUNT(*) FROM ordini", len(ordini)),
            "righe": ("SELECT COUNT(*) FROM righe", len(righe)),
            "ordini orfani": ("SELECT COUNT(*) FROM ordini o LEFT JOIN clienti c "
                              "ON c.cliente_id=o.cliente_id WHERE c.cliente_id IS NULL", 0),
            "righe orfane": ("SELECT COUNT(*) FROM righe r LEFT JOIN ordini o "
                             "ON o.fattura=r.fattura WHERE o.fattura IS NULL", 0),
        }
        for nome, (q, atteso) in prove.items():
            got = cx.execute(text(q)).scalar()
            print(f"  [{'ok ' if got == atteso else 'NO '}] {nome:<16} {got:>9,}  (atteso {atteso:,})")

        # la somma dei valori d'ordine deve tornare con la somma delle righe
        a = cx.execute(text("SELECT ROUND(SUM(valore),2) FROM ordini")).scalar()
        b = cx.execute(text("SELECT ROUND(SUM(valore),2) FROM righe")).scalar()
        print(f"  [{'ok ' if abs(float(a) - float(b)) < 1 else 'NO '}] "
              f"{'quadratura ordini/righe':<16} {a:,} vs {b:,}")


if __name__ == "__main__":
    main()
