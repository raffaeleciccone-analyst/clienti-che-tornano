"""Conta cosa e' rotto nei dati grezzi, senza modificarli.

Legge `dati_grezzi/online_retail_II.xlsx` e stampa i conteggi che finiscono in
DATI-SPORCHI.md. Non scrive niente: e' solo il censimento, e va rilanciato se il
dataset viene riscaricato.

Uso:  python 01_censimento.py
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

# I codici che non sono prodotti: spedizione, rettifiche, spese bancarie, campioni.
# Si riconoscono perche' non cominciano con cinque cifre, ma l'elenco si guarda a
# occhio prima di fidarsi della regola.
NON_PRODOTTI = {"POST", "DOT", "M", "m", "C2", "C3", "D", "S", "BANK CHARGES",
                "AMAZONFEE", "ADJUST", "ADJUST2", "TEST001", "TEST002", "PADS",
                "SP1002", "B", "CRUK", "gift_0001_10", "gift_0001_20",
                "gift_0001_30", "gift_0001_40", "gift_0001_50"}


def titolo(n, t):
    print(f"\n{'=' * 72}\n{n}. {t}\n{'=' * 72}")


def riga(etichetta, valore, su=None):
    if su:
        print(f"  {etichetta:<46} {valore:>10,}  ({valore / su * 100:5.2f}%)")
    else:
        print(f"  {etichetta:<46} {valore:>10,}")


def main() -> None:
    if not FILE.is_file():
        print(f"manca {FILE}")
        return

    print("Lettura del file (un milione di righe, ci mette un po')...")
    fogli = pd.read_excel(FILE, sheet_name=None)
    for nome, d in fogli.items():
        d["foglio"] = nome
    df = pd.concat(fogli.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    tot = len(df)

    titolo(0, "Il file com'e' arrivato")
    riga("righe totali", tot)
    for nome, d in fogli.items():
        riga(f"  di cui foglio {nome}", len(d), tot)
    print(f"  periodo: {df['InvoiceDate'].min():%Y-%m-%d} -> {df['InvoiceDate'].max():%Y-%m-%d}")
    riga("fatture distinte", df["Invoice"].nunique())
    riga("clienti distinti (ID presente)", int(df["Customer ID"].nunique()))
    riga("codici articolo distinti", df["StockCode"].nunique())

    # ── 1. le due annate si sovrappongono? ──────────────────────────────
    titolo(1, "Sovrapposizione fra i due fogli")
    per_foglio = {n: set(d["Invoice"]) for n, d in fogli.items()}
    nomi = list(per_foglio)
    comuni = per_foglio[nomi[0]] & per_foglio[nomi[1]]
    riga("fatture presenti in tutti e due i fogli", len(comuni))
    if comuni:
        dup = df[df["Invoice"].isin(comuni)]
        riga("righe coinvolte", len(dup), tot)
        print("  esempio:", sorted(map(str, comuni))[:5])
        # La colonna Invoice ha tipi misti: le fatture normali arrivano come numero,
        # quelle di storno come stringa perche' cominciano per C. Basta un confronto
        # o una join per inciamparci.
        tipi = df["Invoice"].map(type).value_counts()
        print("  tipi nella colonna Invoice:", ", ".join(f"{t.__name__} {v:,}" for t, v in tipi.items()))

    # ── 2. righe duplicate identiche ────────────────────────────────────
    titolo(2, "Righe duplicate identiche")
    chiave = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"]
    n_dup = int(df.duplicated(subset=chiave).sum())
    riga("righe ripetute uguali in tutto", n_dup, tot)

    # ── 3. cliente mancante ─────────────────────────────────────────────
    titolo(3, "Righe senza Customer ID")
    senza = df["Customer ID"].isna()
    riga("righe senza cliente", int(senza.sum()), tot)
    ric = (df["Quantity"] * df["Price"])
    riga("fatture coinvolte", df.loc[senza, "Invoice"].nunique())
    print(f"  ricavo su quelle righe: {ric[senza].sum():>14,.0f}")
    print(f"  ricavo totale del file : {ric.sum():>14,.0f}")
    print(f"  quota di ricavo che esce dall'analisi: {ric[senza].sum() / ric.sum() * 100:.1f}%")

    # ── 4. storni e quantita' negative ──────────────────────────────────
    titolo(4, "Storni e quantita' negative")
    inv = df["Invoice"].astype(str)
    storno = inv.str.startswith("C")
    negativo = df["Quantity"] < 0
    riga("fatture di storno (C...)", int(storno.sum()), tot)
    riga("righe con quantita' negativa", int(negativo.sum()), tot)
    riga("  negative MA non su fattura di storno", int((negativo & ~storno).sum()))
    riga("  storni con quantita' positiva", int((storno & ~negativo).sum()))
    print(f"  valore degli storni: {ric[storno].sum():>14,.0f}")
    if int((negativo & ~storno).sum()):
        print("\n  le negative fuori dagli storni, che cosa sono:")
        campione = df[negativo & ~storno]
        print("   codici piu' frequenti:",
              ", ".join(f"{k}({v})" for k, v in campione["StockCode"].value_counts().head(6).items()))
        print("   descrizioni piu' frequenti:",
              " | ".join(str(x)[:34] for x in campione["Description"].value_counts().head(4).index))

    # ── 5. prezzo non positivo ──────────────────────────────────────────
    titolo(5, "Prezzo a zero o negativo")
    zero = df["Price"] == 0
    neg = df["Price"] < 0
    riga("prezzo = 0", int(zero.sum()), tot)
    riga("prezzo < 0", int(neg.sum()), tot)
    riga("  di cui con cliente noto", int((zero & ~senza).sum()))
    if int(neg.sum()):
        print("   le negative:", df.loc[neg, ["StockCode", "Description", "Price"]].head(4).to_string(index=False))

    # ── 6. codici che non sono prodotti ─────────────────────────────────
    titolo(6, "Codici articolo che non sono prodotti")
    cod = df["StockCode"].astype(str)
    sospetti = ~cod.str[:5].str.isdigit()
    riga("righe con codice non numerico", int(sospetti.sum()), tot)
    print("\n  i piu' frequenti (i primi cinque caratteri non sono cifre):")
    for k, v in cod[sospetti].value_counts().head(14).items():
        d = df.loc[cod == k, "Description"].dropna()
        etichetta = str(d.iloc[0])[:40] if len(d) else "(senza descrizione)"
        marchio = "  <-- non prodotto" if k in NON_PRODOTTI else ""
        print(f"    {k:<14} {v:>6,}  {etichetta}{marchio}")
    veri_non_prod = cod.isin(NON_PRODOTTI)
    riga("\n  righe classificate come non-prodotto", int(veri_non_prod.sum()), tot)
    print(f"  valore che portano: {ric[veri_non_prod].sum():>14,.0f}  "
          f"({ric[veri_non_prod].sum() / ric.sum() * 100:.1f}% del ricavo)")

    # ── 7. descrizioni mancanti ─────────────────────────────────────────
    titolo(7, "Descrizioni mancanti")
    riga("righe senza descrizione", int(df["Description"].isna().sum()), tot)
    riga("  di cui anche senza cliente", int((df["Description"].isna() & senza).sum()))

    # ── 8. quantita' e prezzi fuori scala ───────────────────────────────
    titolo(8, "Valori fuori scala")
    q = df["Quantity"]
    print(f"  quantita': min {q.min():,}  mediana {q.median():,.0f}  "
          f"99.9° percentile {q.quantile(0.999):,.0f}  max {q.max():,}")
    print(f"  prezzo   : min {df['Price'].min():,.2f}  mediana {df['Price'].median():,.2f}  "
          f"99.9° perc. {df['Price'].quantile(0.999):,.2f}  max {df['Price'].max():,.2f}")
    grandi = df.nlargest(5, "Quantity")[["Invoice", "StockCode", "Description", "Quantity", "Price", "Customer ID"]]
    print("\n  le cinque quantita' piu' grandi:")
    print(grandi.to_string(index=False, max_colwidth=32))

    # ── 9. paesi ────────────────────────────────────────────────────────
    titolo(9, "Paesi")
    p = df["Country"].value_counts()
    for k, v in p.head(6).items():
        riga(str(k), int(v), tot)
    riga("paesi distinti", int(df["Country"].nunique()))
    strani = [x for x in df["Country"].unique() if str(x).lower() in
              ("unspecified", "european community", "rsa", "channel islands")]
    if strani:
        print("  etichette che non sono paesi:", ", ".join(map(str, strani)))

    # ── 10. cosa resta ──────────────────────────────────────────────────
    titolo(10, "Cosa resta applicando le decisioni, una alla volta")
    passi = [
        ("il file com'e'", pd.Series(True, index=df.index)),
    ]
    m = pd.Series(True, index=df.index)
    # La deduplica viene PRIMA di tutto: i due fogli si sovrappongono su dicembre
    # 2010, e finche' le copie restano dentro ogni conteggio successivo — ricavo,
    # ordini per cliente, coorti — e' gonfiato senza dirlo.
    m &= ~df.duplicated(subset=chiave)
    passi.append(("tolte le righe duplicate identiche", m.copy()))
    m &= ~senza;               passi.append(("tolte le righe senza cliente", m.copy()))
    m &= ~storno;              passi.append(("tolte le fatture di storno", m.copy()))
    fuori_storno = negativo & ~storno
    print(f"  [nota] delle {int(fuori_storno.sum()):,} quantita' negative fuori dagli storni, "
          f"{int((fuori_storno & senza).sum()):,} sono su righe senza cliente")
    m &= df["Quantity"] > 0;   passi.append(("tolte le quantita' <= 0", m.copy()))
    m &= df["Price"] > 0;      passi.append(("tolti i prezzi <= 0", m.copy()))
    m &= ~veri_non_prod;       passi.append(("tolti i codici non-prodotto", m.copy()))
    precedente = tot
    for etichetta, maschera in passi:
        n = int(maschera.sum())
        delta = n - precedente
        segno = f"  ({delta:+,})" if delta else ""
        print(f"  {etichetta:<40} {n:>10,}{segno}")
        precedente = n
    finale = df[m]
    print()
    riga("clienti che restano", int(finale["Customer ID"].nunique()))
    riga("fatture che restano", finale["Invoice"].nunique())
    print(f"  ricavo che resta: {(finale['Quantity'] * finale['Price']).sum():,.0f} "
          f"({(finale['Quantity'] * finale['Price']).sum() / ric.sum() * 100:.1f}% del lordo)")

    # ── 11. il dato che regge la domanda ────────────────────────────────
    titolo(11, "Il riacquisto, sui dati ripuliti")
    per_cliente = finale.groupby("Customer ID")["Invoice"].nunique()
    n = len(per_cliente)
    ripetuti = int((per_cliente > 1).sum())
    riga("clienti", n)
    riga("clienti con piu' di un ordine", ripetuti, n)
    print("\n  ordini per cliente:")
    for k, v in per_cliente.value_counts().sort_index().head(6).items():
        riga(f"    {k} ordine/i", int(v), n)


if __name__ == "__main__":
    main()
