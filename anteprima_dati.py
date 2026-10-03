"""Genera una pagina HTML per guardare il file grezzo senza Excel.

Non è un'analisi: è una finestra sul file. Mostra i due fogli, le fatture che
stanno in tutti e due, e un esempio per ogni difetto elencato in
DATI-SPORCHI.md — così i difetti si vedono invece di doverli credere.

Uso:  python anteprima_dati.py        (scrive e apre la pagina)
      python anteprima_dati.py --no-apri
"""
from __future__ import annotations

import html
import sys
import webbrowser
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUI = Path(__file__).parent
FILE = QUI / "dati_grezzi" / "online_retail_II.xlsx"
USCITA = QUI / "risultati" / "anteprima_dati.html"
COLONNE = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate",
           "Price", "Customer ID", "Country"]


def tabella(d: pd.DataFrame, evidenzia=None) -> str:
    """Una tabella HTML da un pezzo di dataframe. `evidenzia` è una funzione
    riga -> bool: le righe vere prendono la classe .segnata."""
    testa = "".join(f"<th>{html.escape(c)}</th>" for c in COLONNE)
    corpo = []
    for _, r in d.iterrows():
        classe = ' class="segnata"' if evidenzia and evidenzia(r) else ""
        celle = []
        for c in COLONNE:
            v = r[c]
            if pd.isna(v):
                celle.append('<td class="vuoto">—</td>')
            elif c == "InvoiceDate":
                celle.append(f'<td class="num">{v:%Y-%m-%d %H:%M}</td>')
            elif c in ("Quantity", "Price", "Customer ID"):
                testo = f"{v:,.2f}" if c == "Price" else f"{v:,.0f}"
                celle.append(f'<td class="num">{testo}</td>')
            else:
                celle.append(f"<td>{html.escape(str(v))}</td>")
        corpo.append(f"<tr{classe}>{''.join(celle)}</tr>")
    return (f'<div class="scorre"><table><thead><tr>{testa}</tr></thead>'
            f"<tbody>{''.join(corpo)}</tbody></table></div>")


def main() -> None:
    if not FILE.is_file():
        raise SystemExit(f"Manca {FILE}")
    print("Lettura del file (un minuto e mezzo, è un xlsx da 43 MB)...")
    fogli = pd.read_excel(FILE, sheet_name=None)
    nomi = list(fogli)
    for n, d in fogli.items():
        d.columns = [c.strip() for c in d.columns]
        d["Invoice"] = d["Invoice"].astype(str)
        d["StockCode"] = d["StockCode"].astype(str)
    df = pd.concat([d.assign(_foglio=n) for n, d in fogli.items()], ignore_index=True)

    # le fatture che stanno in tutti e due i fogli
    comuni = set(fogli[nomi[0]]["Invoice"]) & set(fogli[nomi[1]]["Invoice"])
    esempio = sorted(comuni)[len(comuni) // 2]
    a = fogli[nomi[0]][fogli[nomi[0]]["Invoice"] == esempio]
    b = fogli[nomi[1]][fogli[nomi[1]]["Invoice"] == esempio]

    # un esempio per ogni difetto
    senza_cliente = df[df["Customer ID"].isna()].head(6)
    storni = df[df["Invoice"].str.startswith("C")].head(6)
    non_prodotti = df[df["StockCode"].isin(["POST", "DOT", "M", "BANK CHARGES",
                                            "AMAZONFEE", "ADJUST"])].head(6)
    debito = df[df["Price"] < 0].head(6)
    fuori_scala = df.nlargest(4, "Quantity")

    mb = FILE.stat().st_size / 1024 / 1024
    p = f"""<title>Online Retail II — il file grezzo</title>
<style>
:root {{
  --sfondo:#faf9f7; --carta:#ffffff; --testo:#1c1b19; --tenue:#6b6862;
  --linea:#e3e0da; --segna:#fdf3d8; --bordo-segna:#e0b73f; --acc:#8a3324;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --sfondo:#16151a; --carta:#1e1d23; --testo:#eceaf0; --tenue:#9d99a6;
    --linea:#302e38; --segna:#3a3018; --bordo-segna:#8a6d1f; --acc:#e0785f;
  }}
}}
:root[data-theme="dark"] {{
  --sfondo:#16151a; --carta:#1e1d23; --testo:#eceaf0; --tenue:#9d99a6;
  --linea:#302e38; --segna:#3a3018; --bordo-segna:#8a6d1f; --acc:#e0785f;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--sfondo); color:var(--testo);
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
.foglio {{ max-width:1180px; margin:0 auto; padding:40px 24px 80px; }}
h1 {{ font-size:1.9rem; margin:0 0 6px; letter-spacing:-.02em; }}
.sotto {{ color:var(--tenue); margin:0 0 32px; }}
h2 {{ font-size:1.15rem; margin:44px 0 6px; letter-spacing:-.01em; }}
h2 .n {{ color:var(--acc); font-variant-numeric:tabular-nums; margin-right:8px; }}
p {{ margin:6px 0 14px; max-width:76ch; }}
.tenue {{ color:var(--tenue); font-size:.92rem; }}
.fatti {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1px; background:var(--linea); border:1px solid var(--linea);
  border-radius:8px; overflow:hidden; margin:0 0 8px; }}
.fatto {{ background:var(--carta); padding:14px 16px; }}
.fatto b {{ display:block; font-size:1.3rem; font-variant-numeric:tabular-nums;
  letter-spacing:-.02em; }}
.fatto span {{ color:var(--tenue); font-size:.82rem; }}
.scorre {{ overflow-x:auto; border:1px solid var(--linea); border-radius:8px;
  background:var(--carta); }}
table {{ border-collapse:collapse; width:100%; font-size:.86rem; }}
th {{ text-align:left; padding:9px 12px; background:var(--sfondo);
  border-bottom:1px solid var(--linea); font-weight:600; white-space:nowrap;
  position:sticky; top:0; }}
td {{ padding:8px 12px; border-bottom:1px solid var(--linea); white-space:nowrap; }}
tr:last-child td {{ border-bottom:0; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.vuoto {{ color:var(--bordo-segna); text-align:center; font-weight:600; }}
.segnata td {{ background:var(--segna); }}
.nota {{ border-left:3px solid var(--acc); padding:2px 0 2px 16px; margin:16px 0; }}
.paio {{ display:grid; gap:16px; }}
@media (min-width:900px) {{ .paio {{ grid-template-columns:1fr 1fr; }} }}
.eti {{ font-size:.8rem; color:var(--tenue); margin:0 0 6px; font-weight:600;
  text-transform:uppercase; letter-spacing:.06em; }}
</style>

<div class="foglio">
<h1>Online Retail II — il file com'è arrivato</h1>
<p class="sotto">{FILE.name} · {mb:.1f} MB · nessuna riga modificata</p>

<div class="fatti">
  <div class="fatto"><b>{len(df):,}</b><span>righe</span></div>
  <div class="fatto"><b>2</b><span>fogli</span></div>
  <div class="fatto"><b>{df['Invoice'].nunique():,}</b><span>fatture</span></div>
  <div class="fatto"><b>{int(df['Customer ID'].nunique()):,}</b><span>clienti con id</span></div>
  <div class="fatto"><b>{df['StockCode'].nunique():,}</b><span>codici articolo</span></div>
  <div class="fatto"><b>43</b><span>paesi</span></div>
</div>
<p class="tenue">Periodo: {df['InvoiceDate'].min():%d/%m/%Y} → {df['InvoiceDate'].max():%d/%m/%Y}.
Una riga = una voce di fattura, cioè un articolo dentro un ordine.</p>

<h2><span class="n">1</span>Il primo foglio: {html.escape(nomi[0])}</h2>
<p class="tenue">{len(fogli[nomi[0]]):,} righe. Le prime venti, dalla prima fattura del file.</p>
{tabella(fogli[nomi[0]].head(20))}

<h2><span class="n">2</span>Il secondo foglio: {html.escape(nomi[1])}</h2>
<p class="tenue">{len(fogli[nomi[1]]):,} righe.</p>
{tabella(fogli[nomi[1]].head(20))}

<h2><span class="n">3</span>Il difetto più grosso: i due fogli si sovrappongono</h2>
<p><b>{len(comuni):,} fatture stanno in tutti e due i fogli.</b> Non sono due periodi
separati da incollare uno sotto l'altro: chi lo fa conta due volte dicembre 2010.</p>
<p>Ecco la stessa fattura, la <b>{html.escape(esempio)}</b>, presa una volta per foglio.
Guarda che sono identiche riga per riga.</p>
<div class="paio">
  <div><p class="eti">{html.escape(nomi[0])} — {len(a)} righe</p>{tabella(a.head(8))}</div>
  <div><p class="eti">{html.escape(nomi[1])} — {len(b)} righe</p>{tabella(b.head(8))}</div>
</div>
<div class="nota"><p>Su un'analisi che misura <i>quante volte un cliente torna</i>, una
fattura contata due volte diventa un cliente che ha ordinato due volte. Il difetto
spinge il risultato esattamente nella direzione che si spera di trovare — ed è il
motivo per cui la deduplica è il primo passaggio della pulizia, non l'ultimo.</p></div>

<h2><span class="n">4</span>Le righe senza cliente</h2>
<p><b>Il 22,8% delle righe non ha un Customer ID</b> ({df['Customer ID'].isna().sum():,} righe).
Sono vendite vere — hanno articolo, quantità e prezzo — ma non si sa a chi appartengono,
quindi non possono entrare in un'analisi di coorte.</p>
{tabella(senza_cliente, lambda r: pd.isna(r["Customer ID"]))}

<h2><span class="n">5</span>Gli storni</h2>
<p>Le fatture che cominciano per <b>C</b> sono note di credito: quantità negative, merce
resa. Nota anche il tipo della colonna — qui <code>Invoice</code> è testo, altrove è un
numero intero, e basta una join per inciamparci.</p>
{tabella(storni, lambda r: str(r["Invoice"]).startswith("C"))}

<h2><span class="n">6</span>I codici che non sono prodotti</h2>
<p><code>POST</code> è la spedizione, <code>M</code> una rettifica manuale,
<code>BANK CHARGES</code> una commissione. Contarli come articoli gonfia il numero di
pezzi per ordine e sposta il valore medio dello scontrino.</p>
{tabella(non_prodotti, lambda r: True)}

<h2><span class="n">7</span>Le scritture contabili</h2>
<p>Prezzi negativi, tutti con codice <code>B</code> e descrizione <i>Adjust bad debt</i>:
crediti inesigibili, fino a −53.594 in una riga sola. Un credito inesigibile non è un
acquisto.</p>
{tabella(debito, lambda r: True)}

<h2><span class="n">8</span>I valori fuori scala — che restano dentro</h2>
<p>80.995 pezzi di <i>PAPER CRAFT, LITTLE BIRDIE</i> in un ordine solo. Non si toglie:
è un ordine vero di un cliente vero, e togliere le code perché sono grandi è il modo
più rapido di far dire a una media quello che si vuole.</p>
{tabella(fuori_scala, lambda r: True)}

<p class="tenue" style="margin-top:44px">
Il conteggio completo dei difetti, con quante righe toglie ogni passaggio, sta in
DATI-SPORCHI.md. Questa pagina serve solo a far vedere che ci sono.</p>
</div>
"""
    USCITA.parent.mkdir(exist_ok=True)
    USCITA.write_text(p, encoding="utf-8")
    print(f"Scritta: {USCITA}  ({USCITA.stat().st_size/1024:.0f} KB)")
    if "--no-apri" not in sys.argv:
        webbrowser.open(USCITA.resolve().as_uri())
        print("Aperta nel browser.")


if __name__ == "__main__":
    main()
