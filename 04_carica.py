"""Applica le pulizie di DATI-SPORCHI.md e carica lo schema a stella.

Ogni passaggio di pulizia ha lo stesso nome che ha nel documento, e stampa
quante righe toglie: se un giorno i due numeri non coincidono piu', se ne
accorge chi lancia lo script, non chi legge i risultati sei mesi dopo.

L'ordine di caricamento e' quello che impongono le chiavi esterne: prima le
dimensioni, poi i fatti. Le chiavi surrogate si prendono rileggendo le
dimensioni dal database, non indovinandole: se MySQL assegna un AUTO_INCREMENT
diverso da quello che ci aspettiamo, i fatti puntano comunque alla riga giusta.

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

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica"]


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

    print("\nPulizia — i nomi sono quelli di DATI-SPORCHI.md")
    print(f"  {'il file com e':<38} {len(df):>9,}")
    df = passo(df, "Togli le righe duplicate", ~df.duplicated(subset=CHIAVE))
    df = passo(df, "Tieni solo le righe con cliente", df["Customer ID"].notna())
    df = passo(df, "Togli le fatture di storno", ~df["Invoice"].str.startswith("C"))
    df = passo(df, "Togli i prezzi non positivi", df["Price"] > 0)
    df = passo(df, "Togli le quantita non positive", df["Quantity"] > 0)
    df = passo(df, "Togli i codici non-prodotto", ~df["StockCode"].isin(NON_PRODOTTI))

    df["cliente_id"] = df["Customer ID"].astype(int)
    df["valore"] = (df["Quantity"] * df["Price"]).round(2)
    df["data"] = df["InvoiceDate"].dt.normalize()

    # Una fattura con due clienti diversi sarebbe un difetto del modello, non
    # dei dati: si controlla invece di sperare.
    doppie = int((df.groupby("Invoice")["cliente_id"].nunique() > 1).sum())
    if doppie:
        print(f"\n  ATTENZIONE: {doppie} fatture con piu' di un cliente")

    # ══ le dimensioni ════════════════════════════════════════════════════
    print("\nCostruzione delle dimensioni")

    # ── dim_data: un giorno per riga, buchi compresi ──────────────────────
    giorni = pd.date_range(df["data"].min(), df["data"].max(), freq="D")
    dim_data = pd.DataFrame({"data": giorni})
    dim_data["data_key"] = dim_data["data"].dt.strftime("%Y%m%d").astype(int)
    dim_data["anno"] = dim_data["data"].dt.year
    dim_data["mese"] = dim_data["data"].dt.month
    dim_data["nome_mese"] = dim_data["mese"].map(lambda m: MESI[m - 1])
    dim_data["trimestre"] = dim_data["data"].dt.quarter
    dim_data["anno_mese"] = dim_data["data"].dt.strftime("%Y-%m")
    dim_data["giorno_settimana"] = dim_data["data"].dt.dayofweek + 1
    dim_data["nome_giorno"] = dim_data["data"].dt.dayofweek.map(lambda g: GIORNI[g])
    dim_data["fine_settimana"] = (dim_data["data"].dt.dayofweek >= 5).astype(int)
    dim_data["data"] = dim_data["data"].dt.date
    con_vendite = df["data"].nunique()
    print(f"  dim_data      {len(dim_data):>9,} giorni  "
          f"({con_vendite:,} con vendite, {len(dim_data) - con_vendite:,} senza)")

    # ── dim_cliente ───────────────────────────────────────────────────────
    per_cliente = (df.sort_values(["cliente_id", "InvoiceDate"])
                     .groupby("cliente_id")
                     .agg(paese=("Country", "first"), primo_ordine=("data", "min")))
    dim_cliente = per_cliente.reset_index()
    dim_cliente["coorte"] = pd.to_datetime(dim_cliente["primo_ordine"]).dt.strftime("%Y-%m")
    dim_cliente["primo_ordine"] = pd.to_datetime(dim_cliente["primo_ordine"]).dt.date
    print(f"  dim_cliente   {len(dim_cliente):>9,} clienti")

    # ── dim_articolo ──────────────────────────────────────────────────────
    # 621 codici hanno piu' di una descrizione: si tiene la piu' frequente e si
    # scrive quante ne sono state viste, perche' chi legge sappia che c'era una
    # scelta invece di crederla un dato.
    desc = (df.dropna(subset=["Description"])
              .groupby(["StockCode", "Description"]).size()
              .rename("n").reset_index()
              .sort_values(["StockCode", "n"], ascending=[True, False]))
    scelta = desc.groupby("StockCode").first()["Description"]
    quante = desc.groupby("StockCode").size()
    dim_articolo = pd.DataFrame({"codice": sorted(df["StockCode"].unique())})
    dim_articolo["descrizione"] = (dim_articolo["codice"].map(scelta)
                                   .astype("object").str.slice(0, 120))
    dim_articolo["n_descrizioni"] = dim_articolo["codice"].map(quante).fillna(0).astype(int)
    ambigui = int((dim_articolo["n_descrizioni"] > 1).sum())
    print(f"  dim_articolo  {len(dim_articolo):>9,} codici   "
          f"({ambigui:,} con piu' di una descrizione: tenuta la piu' frequente)")

    # ══ il caricamento ═══════════════════════════════════════════════════
    eng = create_engine(url(), pool_pre_ping=True)
    print("\nCreazione dello schema...")
    ddl = SCHEMA.read_text(encoding="utf-8")
    with eng.begin() as cx:
        cx.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for istruzione in [s.strip() for s in ddl.split(";") if s.strip() and
                           not all(r.strip().startswith("--") for r in s.strip().splitlines())]:
            cx.execute(text(istruzione))
        cx.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print("Caricamento delle dimensioni...")
    for nome, tab in (("dim_data", dim_data), ("dim_cliente", dim_cliente),
                      ("dim_articolo", dim_articolo)):
        tab.to_sql(nome, eng, if_exists="append", index=False, chunksize=20_000)
        print(f"  {nome:<14} {len(tab):>9,}")

    # Le chiavi surrogate si rileggono dal database invece di indovinarle: se
    # MySQL assegnasse un AUTO_INCREMENT diverso da quello atteso, i fatti
    # punterebbero comunque alla riga giusta.
    chiavi_cliente = pd.read_sql(text("SELECT cliente_key, cliente_id FROM dim_cliente"),
                                 eng).set_index("cliente_id")["cliente_key"]
    chiavi_articolo = pd.read_sql(text("SELECT articolo_key, codice FROM dim_articolo"),
                                  eng).set_index("codice")["articolo_key"]

    # ── fatto_riga ────────────────────────────────────────────────────────
    fatto_riga = pd.DataFrame({
        "fattura": df["Invoice"].values,
        "cliente_key": df["cliente_id"].map(chiavi_cliente).values,
        "articolo_key": df["StockCode"].map(chiavi_articolo).values,
        "data_key": df["data"].dt.strftime("%Y%m%d").astype(int).values,
        "data_ora": df["InvoiceDate"].values,
        "quantita": df["Quantity"].values,
        "prezzo": df["Price"].values,
        "valore": df["valore"].values,
    })
    if fatto_riga[["cliente_key", "articolo_key"]].isna().any().any():
        raise SystemExit("Una riga non trova la sua dimensione: caricamento interrotto.")

    # ── fatto_ordine: l'aggregato, costruito da fatto_riga ────────────────
    fatto_ordine = (fatto_riga.groupby("fattura")
                    .agg(cliente_key=("cliente_key", "first"),
                         data_key=("data_key", "min"),
                         data_ora=("data_ora", "min"),
                         n_righe=("fattura", "size"),
                         n_pezzi=("quantita", "sum"),
                         valore=("valore", "sum"))
                    .reset_index())
    fatto_ordine["valore"] = fatto_ordine["valore"].round(2)

    print("Caricamento dei fatti...")
    for nome, tab in (("fatto_riga", fatto_riga), ("fatto_ordine", fatto_ordine)):
        tab.to_sql(nome, eng, if_exists="append", index=False, chunksize=20_000)
        print(f"  {nome:<14} {len(tab):>9,}")

    # ══ i controlli ══════════════════════════════════════════════════════
    print("\nControlli:")
    esiti = []
    with eng.connect() as cx:
        def prova(nome, query, atteso, tolleranza=0):
            got = cx.execute(text(query)).scalar()
            ok = abs(float(got) - float(atteso)) <= tolleranza
            esiti.append(ok)
            print(f"  [{'ok ' if ok else 'NO '}] {nome:<34} {got:>12,}  (atteso {atteso:,})")

        prova("dim_data", "SELECT COUNT(*) FROM dim_data", len(dim_data))
        prova("dim_cliente", "SELECT COUNT(*) FROM dim_cliente", len(dim_cliente))
        prova("dim_articolo", "SELECT COUNT(*) FROM dim_articolo", len(dim_articolo))
        prova("fatto_riga", "SELECT COUNT(*) FROM fatto_riga", len(fatto_riga))
        prova("fatto_ordine", "SELECT COUNT(*) FROM fatto_ordine", len(fatto_ordine))

        # nessun fatto senza la sua dimensione
        for nome, tabella, dim, chiave in (
                ("righe senza cliente", "fatto_riga", "dim_cliente", "cliente_key"),
                ("righe senza articolo", "fatto_riga", "dim_articolo", "articolo_key"),
                ("righe senza data", "fatto_riga", "dim_data", "data_key"),
                ("ordini senza cliente", "fatto_ordine", "dim_cliente", "cliente_key")):
            prova(nome, f"SELECT COUNT(*) FROM {tabella} f LEFT JOIN {dim} d "
                        f"ON d.{chiave}=f.{chiave} WHERE d.{chiave} IS NULL", 0)

        # L'AGGREGATO DEVE QUADRARE CON LA TABELLA ATOMICA. E' il controllo che
        # giustifica l'esistenza di fatto_ordine: senza, sarebbe una copia che
        # invecchia da sola, cioe' il difetto che questo schema doveva togliere.
        a = float(cx.execute(text("SELECT ROUND(SUM(valore),2) FROM fatto_riga")).scalar())
        b = float(cx.execute(text("SELECT ROUND(SUM(valore),2) FROM fatto_ordine")).scalar())
        ok = abs(a - b) < 1
        esiti.append(ok)
        print(f"  [{'ok ' if ok else 'NO '}] {'aggregato = atomica':<34} "
              f"{a:>12,.2f}  (righe {b:,.2f})")

        sballate = cx.execute(text("""
            SELECT COUNT(*) FROM fatto_ordine o
            JOIN (SELECT fattura, COUNT(*) n, SUM(quantita) q, ROUND(SUM(valore),2) v
                  FROM fatto_riga GROUP BY fattura) r ON r.fattura = o.fattura
            WHERE r.n <> o.n_righe OR r.q <> o.n_pezzi OR ABS(r.v - o.valore) > 0.01
        """)).scalar()
        ok = sballate == 0
        esiti.append(ok)
        print(f"  [{'ok ' if ok else 'NO '}] {'fatture con totali diversi':<34} {sballate:>12,}"
              f"  (atteso 0)")

    if not all(esiti):
        print("\nIl caricamento non e' coerente: mi fermo qui.")
        sys.exit(1)


if __name__ == "__main__":
    main()
