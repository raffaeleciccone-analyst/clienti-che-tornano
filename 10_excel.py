"""Costruisce la cartella di lavoro: clienti-che-tornano.xlsx

Legge sito/dati.json, gli stessi numeri della pagina e di RISULTATI.md. Non
rifà nessun conto: se una cifra qui non torna con i documenti, il colpevole è
uno solo ed è 08_dati_pagina.py.

Fino al 21/11/2026 c'era un foglio «Valore e pareggio» con le formule di una
soglia di spesa. La soglia è stata ritirata il 2/10 (RISULTATI.md §9) e il
foglio ora si chiama «Valore»: mostra i numeri corretti e spiega perché una
soglia non si può calcolare (SPEC C17).

Uso:  python 10_excel.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUI = Path(__file__).parent
DATI = QUI / "sito" / "dati.json"
USCITA = QUI / "clienti-che-tornano.xlsx"

MESI = ["gen", "feb", "mar", "apr", "mag", "giu",
        "lug", "ago", "set", "ott", "nov", "dic"]

INCHIOSTRO = "FF15181B"
TENUE = "FF5D656C"
OTTONE = "FF8A6414"
CARTA = "FFF2F3F4"

T_TITOLO = Font(name="Calibri", size=17, bold=True, color=INCHIOSTRO)
T_H2 = Font(name="Calibri", size=12, bold=True, color=OTTONE)
T_TESTA = Font(name="Calibri", size=9, bold=True, color=TENUE)
T_NORM = Font(name="Calibri", size=10.5, color=INCHIOSTRO)
T_TENUE = Font(name="Calibri", size=9.5, color=TENUE)
T_FORTE = Font(name="Calibri", size=10.5, bold=True, color=INCHIOSTRO)

SOTTILE = Side(style="thin", color="FFD6DADE")
BORDO = Border(bottom=SOTTILE)


def scrivi(ws, cella, valore, font=T_NORM, formato=None, riemp=None,
           allinea=None, bordo=None):
    c = ws[cella]
    c.value = valore
    c.font = font
    if formato:
        c.number_format = formato
    if riemp:
        c.fill = PatternFill("solid", fgColor=riemp)
    if allinea:
        c.alignment = allinea
    if bordo:
        c.border = bordo
    return c


def testo(ws, riga, righe, col="A", font=T_NORM):
    for t in righe:
        if t:
            scrivi(ws, f"{col}{riga}", t, font)
        riga += 1
    return riga


# ═════════════════════════════════════════════════════════════════════════
def foglio_leggimi(wb, d):
    ws = wb.active
    ws.title = "Leggimi"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 104

    scrivi(ws, "B2", "Clienti che tornano", T_TITOLO)
    scrivi(ws, "B3", "Online Retail II — negozio online britannico di articoli da regalo, "
                     "dicembre 2009 – dicembre 2011, 1.067.371 righe.", T_TENUE)

    r = 5
    scrivi(ws, f"B{r}", "LA DOMANDA", T_H2); r += 1
    r = testo(ws, r, [
        "Quanto vale un cliente che torna, e conviene di più trattenerlo o acquisirne "
        "uno nuovo?",
        "Scritta prima di aprire SQL. Il committente immaginabile: chi decide il budget "
        "marketing di un negozio online.",
        "",
    ])

    # La risposta è quella corretta il 2/10/2026 (RISULTATI.md §9). La versione del
    # 27 agosto e la soglia di spesa sono ritirate e non compaiono qui (SPEC C17).
    f = d["valore_futuro"]
    scrivi(ws, f"B{r}", "LA RISPOSTA", T_H2); r += 1
    r = testo(ws, r, [
        f"Fra i {f['clienti']:,} clienti entrati nel 2010, chi torna entro 90 giorni spende dal "
        f"giorno 91 al 365 in media {f['tornati_media']:,} £, gli altri {f['altri_media']:,} £."
        .replace(",", "."),
        f"A parità di primo ordine il divario resta {f['pari_partenza']['stima']:,} £ "
        f"(intervallo {f['pari_partenza']['ic'][0]:,}–{f['pari_partenza']['ic'][1]:,}); a parità "
        f"di spesa nei primi 90 giorni scende a {f['pari_spesa_90']['stima']:,} £ (intervallo "
        f"{f['pari_spesa_90']['ic'][0]:,}–{f['pari_spesa_90']['ic'][1]:,}, comprende lo zero)."
        .replace(",", "."),
        "Per prevedere la spesa futura basta la spesa iniziale. È una lettura predittiva, "
        "non causale: quanto renda riattivare un cliente lo può dire solo un test con la "
        "riattivazione assegnata a caso. Il foglio «Valore» spiega perché.",
        "",
    ])

    scrivi(ws, f"B{r}", "E LA COSA CHE NON ERA IN PROGRAMMA", T_H2); r += 1
    r = testo(ws, r, [
        "La retention di questo negozio non è una curva di abbandono: è un calendario.",
        f"Il mese dell'anno spiega il {d['spiegata']['calendario']}% della variazione fra "
        f"le celle, l'età del cliente solo il {d['spiegata']['eta']}%. Novembre 25%, "
        f"gennaio 11%.",
        "Leggere la matrice da sinistra a destra vuol dire leggere il Natale e chiamarlo "
        "fedeltà. I due fogli «Matrice» mostrano le stesse celle nei due allineamenti: "
        "confrontali.",
        "",
    ])

    scrivi(ws, f"B{r}", "COSA QUESTI NUMERI NON DICONO", T_H2); r += 1
    r = testo(ws, r, [
        "• Non dicono se trattenere convenga più che acquisire: manca il costo di "
        "acquisizione.",
        "• Misurano ricavo, non profitto: manca il costo del venduto.",
        f"• Il 22,8% delle righe non ha un identificativo cliente. Il tasso di ritorno "
        f"vero sta fra il {d['anonimi']['quota_bassa']}% e il {d['anonimi']['quota_alta']}%: "
        f"si scrive «tre clienti IDENTIFICATI su quattro tornano».",
        "• Non dimostrano una causa. «I clienti che tornano valgono N volte» è vero; "
        "«farli tornare li fa valere N volte» richiederebbe un esperimento.",
        "• I dati sono del 2009-2011. Il metodo si trasferisce, i numeri no.",
        "",
    ], font=T_TENUE)

    scrivi(ws, f"B{r}", "COME È STATO FATTO", T_H2); r += 1
    testo(ws, r, [
        "Python e SQL (MySQL 8, funzioni finestra). Le pulizie, il modello, le verifiche e "
        "i limiti stanno nel repo, un documento per ognuno.",
        "Le cifre di questo file escono dallo stesso file di dati della pagina web, e sono "
        "ricontrollate da uno script che rifà 68 conti dalle tabelle di base.",
    ], font=T_TENUE)


# ═════════════════════════════════════════════════════════════════════════
def foglio_matrice(wb, d, per_calendario: bool):
    nome = "Matrice per calendario" if per_calendario else "Matrice per età"
    ws = wb.create_sheet(nome)
    ws.sheet_view.showGridLines = False
    c0 = d["coorti"][0]
    off = lambda c: (c["anno"] - c0["anno"]) * 12 + (c["mese"] - c0["mese"])
    n_col = max(off(c) + len(c["celle"]) for c in d["coorti"]) if per_calendario \
        else max(len(c["celle"]) for c in d["coorti"])

    scrivi(ws, "A1", "Matrice per mese del calendario" if per_calendario
           else "Matrice per età del cliente", T_TITOLO)
    scrivi(ws, "A2",
           "Ogni riga è un mese di clienti nuovi. Le celle dicono quanti di loro hanno "
           "ordinato in quel mese, su cento." if not per_calendario else
           "Le STESSE celle del foglio precedente, spostate: ogni riga parte dal suo mese "
           "vero. Ora si legge dall'alto in basso.", T_TENUE)
    scrivi(ws, "A3",
           "Si legge da sinistra a destra, e sembra una discesa. Il foglio dopo mostra "
           "perché non lo è." if not per_calendario else
           "Le colonne si accendono e si spengono tutte insieme: novembre acceso in ogni "
           "riga, gennaio spento in ogni riga. Non è l'età del cliente a muovere il "
           "numero, è il mese dell'anno.", T_TENUE)

    R0 = 5
    scrivi(ws, f"A{R0}", "coorte", T_TESTA)
    scrivi(ws, f"B{R0}", "clienti", T_TESTA, allinea=Alignment(horizontal="right"))
    for i in range(n_col):
        col = get_column_letter(3 + i)
        et = (f"{MESI[(c0['mese'] - 1 + i) % 12]} "
              f"{str(c0['anno'] + (c0['mese'] - 1 + i) // 12)[2:]}"
              if per_calendario else ("0" if i == 0 else f"+{i}"))
        scrivi(ws, f"{col}{R0}", et, T_TESTA, allinea=Alignment(horizontal="center"))
        ws.column_dimensions[col].width = 6.5
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 8

    for j, c in enumerate(d["coorti"]):
        r = R0 + 1 + j
        scrivi(ws, f"A{r}", c["coorte"], T_NORM)
        scrivi(ws, f"B{r}", c["entrati"], T_NORM, "#,##0")
        base = off(c) if per_calendario else 0
        for i, val in enumerate(c["celle"]):
            if val is None:
                continue
            col = get_column_letter(3 + base + i)
            cel = scrivi(ws, f"{col}{r}", val / 100, T_NORM, "0%",
                         allinea=Alignment(horizontal="center"))
            if i == 0:
                cel.font = Font(name="Calibri", size=9, color=TENUE)

    ultima = R0 + len(d["coorti"])
    zona = f"D{R0 + 1}:{get_column_letter(2 + n_col)}{ultima}"
    # La scala diverge intorno alla retention media: sotto la media le celle
    # leggono fredde, sopra calde. Non è decorazione, è la differenza che
    # questi due fogli devono far vedere.
    ws.conditional_formatting.add(zona, ColorScaleRule(
        start_type="num", start_value=0.05, start_color="FFA8C0D4",
        mid_type="num", mid_value=0.185, mid_color="FFF4EFE3",
        end_type="num", end_value=0.40, end_color="FFB8801F"))

    ws.freeze_panes = f"C{R0 + 1}"
    r = ultima + 2
    testo(ws, r, [
        "La colonna 0 è il mese di ingresso: vale 100 per definizione, non è un risultato.",
        "Le celle vuote a destra non sono zeri: sono mesi che il calendario non ha ancora "
        "raggiunto quando i dati finiscono (9 dicembre 2011).",
    ], font=T_TENUE)
    if per_calendario:
        scrivi(ws, f"A{r + 3}",
               "Le colonne di questo foglio sono mesi veri: ogni colonna contiene un solo "
               "mese del calendario, per tutte le coorti. Verificato contando.", T_TENUE)


# ═════════════════════════════════════════════════════════════════════════
def foglio_riacquisto(wb, d):
    ws = wb.create_sheet("Riacquisto")
    ws.sheet_view.showGridLines = False
    for col, w in (("A", 14), ("B", 11), ("C", 11), ("D", 26), ("E", 13), ("F", 13)):
        ws.column_dimensions[col].width = w

    scrivi(ws, "A1", "Il riacquisto", T_TITOLO)
    scrivi(ws, "A2", f"Sui {d['campione']['clienti']:,} clienti entrati nel 2010 che hanno "
                     f"avuto 365 giorni interi davanti. Finestra uguale per tutti: se no si "
                     f"misura quanto tempo ha avuto il cliente, non il cliente."
           .replace(",", "."), T_TENUE)

    R0 = 4
    for i, t in enumerate(["gradino", "clienti", "quota", "sopravvive dal precedente"]):
        scrivi(ws, f"{get_column_letter(1+i)}{R0}", t, T_TESTA, bordo=BORDO,
               allinea=Alignment(horizontal="right" if i else "left"))
    for j, g in enumerate(d["funnel"]):
        r = R0 + 1 + j
        scrivi(ws, f"A{r}", f"{g['gradino']}º ordine", T_NORM)
        scrivi(ws, f"B{r}", g["clienti"], T_NORM, "#,##0")
        scrivi(ws, f"C{r}", g["quota"] / 100, T_NORM, "0,0%")
        if g["sopravvive"]:
            scrivi(ws, f"D{r}", g["sopravvive"] / 100, T_FORTE, "0,0%")

    r = R0 + len(d["funnel"]) + 2
    scrivi(ws, f"A{r}", f"La colonna di destra non si muove: {d['sopravvivenza_media']}% a "
                        f"ogni gradino.", T_FORTE); r += 1
    r = testo(ws, r, [
        "Arrivare al secondo ordine non rende un cliente più fedele di quanto fosse. "
        "«Portali al secondo acquisto e sono tuoi» qui è falso.",
        "",
        "Contando tutta la vita di ogni cliente veniva 72%, poi 78%, 80%, 81% — una fedeltà "
        "che cresce. Ma le vite non sono lunghe uguali: chi è entrato a gennaio 2010 ha "
        "avuto due anni per arrivare all'ottavo ordine, chi è entrato a settembre 2011 ne "
        "ha avuti tre mesi. Quella salita era il tempo in più di chi era arrivato in fondo.",
        "",
    ], font=T_TENUE)

    scrivi(ws, f"A{r}", "IL CONTROLLO", T_H2); r += 1
    scrivi(ws, f"A{r}", "Se la sopravvivenza è costante, il numero di ordini deve seguire "
                        "una geometrica. Il parametro è stimato dagli stessi dati, quindi "
                        "è una riscrittura coerente, non una prova indipendente.", T_TENUE)
    r += 2
    for i, t in enumerate(["ordini", "attesa", "osservata"]):
        scrivi(ws, f"{get_column_letter(1+i)}{r}", t, T_TESTA, bordo=BORDO,
               allinea=Alignment(horizontal="right" if i else "left"))
    for j, g in enumerate(d["geometrica"]):
        rr = r + 1 + j
        scrivi(ws, f"A{rr}", g["ordini"], T_NORM)
        scrivi(ws, f"B{rr}", g["attesa"] / 100, T_NORM, "0,0%")
        scrivi(ws, f"C{rr}", g["osservata"] / 100, T_NORM, "0,0%")

    # il tempo al secondo ordine
    r = r + len(d["geometrica"]) + 3
    scrivi(ws, f"A{r}", "QUANTO TEMPO PASSA FRA PRIMO E SECONDO ORDINE", T_H2); r += 1
    p = d["tempo_secondo"]["percentili"]
    scrivi(ws, f"A{r}", f"Mediana {p['50']} giorni. Un quarto torna entro {p['25']}, "
                        f"tre quarti entro {p['75']}, nove su dieci entro {p['90']}.",
           T_NORM); r += 1
    scrivi(ws, f"A{r}", "Una soglia di silenzio oltre la quale il cliente è perso NON "
                        "esiste: la curva cala in modo regolare e non precipita mai. "
                        "Dichiararne una vorrebbe dire inventarla.", T_TENUE)
    r += 2
    for i, t in enumerate(["giorni", "già tornati"]):
        scrivi(ws, f"{get_column_letter(1+i)}{r}", t, T_TESTA, bordo=BORDO,
               allinea=Alignment(horizontal="right" if i else "left"))
    for j, punto in enumerate(d["tempo_secondo"]["cumulata"][::3]):
        rr = r + 1 + j
        scrivi(ws, f"A{rr}", punto["giorni"], T_NORM)
        scrivi(ws, f"B{rr}", punto["quota"] / 100, T_NORM, "0,0%")
    scrivi(ws, f"D{r}", "Percentuali di chi torna ENTRO L'ANNO: la finestra taglia a 365 "
                        "giorni, quindi non sono percentuali di «chi tornerà» mai.", T_TENUE)


# ═════════════════════════════════════════════════════════════════════════
def foglio_valore(wb, d):
    """Quanto spende dopo chi torna presto: RISULTATI.md §9, corretto il 2/10/2026.

    Fino al 21/11 questo foglio si chiamava «Valore e pareggio» e calcolava con le
    formule una soglia di spesa. La soglia è stata ritirata il 2/10 (il confronto su
    cui poggiava girava in tondo) e il 21/11 è uscita dal foglio: un numero ritirato
    non deve restare calcolabile in un file che si passa di mano (SPEC C17)."""
    ws = wb.create_sheet("Valore")
    ws.sheet_view.showGridLines = False
    for col, w in (("A", 44), ("B", 14), ("C", 14), ("D", 14), ("E", 4)):
        ws.column_dimensions[col].width = w
    f = d["valore_futuro"]

    scrivi(ws, "A1", "Quanto spende dopo chi torna presto", T_TITOLO)
    scrivi(ws, "A2", f"I {f['clienti']:,} clienti entrati nel 2010. I primi 90 giorni dal primo "
                     f"ordine decidono il gruppo; la spesa si conta dal giorno 91 al 365."
                     .replace(",", "."), T_TENUE)

    R0 = 4
    for i, t in enumerate(["", "clienti", "spesa media", "mediana"]):
        if t:
            scrivi(ws, f"{get_column_letter(1+i)}{R0}", t, T_TESTA, bordo=BORDO,
                   allinea=Alignment(horizontal="right" if i else "left"))
    scrivi(ws, f"A{R0+1}", "tornati entro 90 giorni", T_FORTE)
    scrivi(ws, f"B{R0+1}", f["tornati"], T_FORTE, "#,##0")
    scrivi(ws, f"C{R0+1}", f["tornati_media"], T_FORTE, '#,##0 "£"')
    scrivi(ws, f"D{R0+1}", f["tornati_mediana"], T_NORM, '#,##0 "£"')
    scrivi(ws, f"A{R0+2}", "non tornati", T_NORM)
    scrivi(ws, f"B{R0+2}", f["clienti"] - f["tornati"], T_NORM, "#,##0")
    scrivi(ws, f"C{R0+2}", f["altri_media"], T_NORM, '#,##0 "£"')
    scrivi(ws, f"D{R0+2}", f["altri_mediana"], T_NORM, '#,##0 "£"')
    scrivi(ws, f"A{R0+3}", "Media e mediana sono lontane: la spesa ha una coda lunga.", T_TENUE)

    r = R0 + 5
    scrivi(ws, f"A{r}", "MA CHI TORNA ERA GIÀ DIVERSO", T_H2); r += 1
    scrivi(ws, f"A{r}", "Si confrontano clienti che partivano uguali. Intervalli al 95%, "
                        "2.000 ricampionamenti dentro ogni strato.", T_TENUE); r += 2
    for i, t in enumerate(["confronto", "differenza", "da", "a"]):
        scrivi(ws, f"{get_column_letter(1+i)}{r}", t, T_TESTA, bordo=BORDO,
               allinea=Alignment(horizontal="right" if i else "left"))
    righe = [("grezzo", f["grezza"], f["grezza_ic"], T_NORM),
             ("a parità di primo ordine e coorte", f["pari_partenza"]["stima"],
              f["pari_partenza"]["ic"], T_FORTE),
             ("a parità di spesa nei primi 90 giorni", f["pari_spesa_90"]["stima"],
              f["pari_spesa_90"]["ic"], T_FORTE)]
    for nome, stima, ic, font in righe:
        r += 1
        scrivi(ws, f"A{r}", nome, font)
        scrivi(ws, f"B{r}", stima, font, '#,##0 "£"')
        scrivi(ws, f"C{r}", ic[0], T_NORM, '#,##0 "£";-#,##0 "£"')
        scrivi(ws, f"D{r}", ic[1], T_NORM, '#,##0 "£"')
    r += 2

    scrivi(ws, f"A{r}", "PERCHÉ QUI NON C'È UNA SOGLIA DI SPESA", T_H2); r += 1
    testo(ws, r, [
        "La domanda di partenza chiedeva fino a quanto conviene spendere per far tornare un "
        "cliente. Questi numeri non lo permettono:",
        "• a parità di spesa nei primi 90 giorni il ritorno aggiunge "
        f"{f['pari_spesa_90']['stima']} £ e l'intervallo comprende lo zero: chi torna da solo è "
        "soprattutto chi spendeva già di più;",
        "• quindi non si può assumere che un cliente riportato con una campagna si comporti "
        "come chi è tornato da solo.",
        "Per rispondere serve un test: due gruppi di clienti con la stessa spesa iniziale, la "
        "riattivazione mandata a uno solo, scelto a caso.",
    ], font=T_TENUE)


# ═════════════════════════════════════════════════════════════════════════
def foglio_dati(wb, d):
    """La matrice in formato lungo: una riga per cella. È il foglio da cui si
    fa una tabella pivot senza dover disfare una matrice larga."""
    ws = wb.create_sheet("Coorti (mese d'ingresso)")
    intestazioni = ["coorte", "anno coorte", "mese coorte", "clienti entrati",
                    "mese relativo", "mese calendario", "anno calendario", "quota attivi"]
    for i, t in enumerate(intestazioni):
        scrivi(ws, f"{get_column_letter(1+i)}1", t, T_TESTA, bordo=BORDO)
        ws.column_dimensions[get_column_letter(1 + i)].width = max(12, len(t) + 3)
    r = 2
    for c in d["coorti"]:
        for i, val in enumerate(c["celle"]):
            if val is None:
                continue
            m = (c["mese"] - 1 + i) % 12 + 1
            a = c["anno"] + (c["mese"] - 1 + i) // 12
            for j, v in enumerate([c["coorte"], c["anno"], c["mese"], c["entrati"],
                                   i, MESI[m - 1], a]):
                scrivi(ws, f"{get_column_letter(1+j)}{r}", v, T_NORM)
            scrivi(ws, f"H{r}", val / 100, T_NORM, "0,0%")
            r += 1
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:H{r-1}"
    return r - 2


# ═════════════════════════════════════════════════════════════════════════
def verifica(d) -> list[str]:
    """Riapre il file appena scritto e lo confronta con i dati di partenza.

    Serve perché openpyxl scrive senza lamentarsi anche quando il risultato è
    sbagliato: una cella spostata di una riga, una formula diventata testo, una
    matrice allineata male. Qui si riapre e si guarda.
    """
    from openpyxl import load_workbook
    guai = []
    wb = load_workbook(USCITA)

    attesi = ["Leggimi", "Matrice per età", "Matrice per calendario",
              "Riacquisto", "Valore", "Coorti (mese d'ingresso)"]
    for nome in attesi:
        if nome not in wb.sheetnames:
            guai.append(f"manca il foglio «{nome}»")
    if guai:
        return guai

    # le due matrici devono contenere le STESSE celle, solo in posizioni diverse
    c0 = d["coorti"][0]
    off = lambda c: (c["anno"] - c0["anno"]) * 12 + (c["mese"] - c0["mese"])
    for per_cal, nome in ((False, "Matrice per età"), (True, "Matrice per calendario")):
        ws = wb[nome]
        for j, c in enumerate(d["coorti"]):
            base = off(c) if per_cal else 0
            for i, val in enumerate(c["celle"]):
                if val is None:
                    continue
                letto = ws.cell(row=6 + j, column=3 + base + i).value
                if letto is None or abs(letto * 100 - val) > 0.051:
                    guai.append(f"{nome}: coorte {c['coorte']} mese +{i} "
                                f"vale {letto} invece di {val / 100}")
                    break

    # nel foglio per calendario, ogni colonna deve essere UN solo mese vero
    ws = wb["Matrice per calendario"]
    colonne = {}
    for j, c in enumerate(d["coorti"]):
        for i, val in enumerate(c["celle"]):
            if val is None:
                continue
            k = off(c) + i
            mese = ((c["mese"] - 1 + i) % 12 + 1, c["anno"] + (c["mese"] - 1 + i) // 12)
            colonne.setdefault(k, set()).add(mese)
    miste = [k for k, v in colonne.items() if len(v) > 1]
    if miste:
        guai.append(f"colonne che mescolano mesi diversi: {miste}")

    # la soglia di spesa è ritirata (2/10) e non deve ricomparire (SPEC C17)
    testi_min = " ".join(str(c.value) for ws in wb for riga in ws.iter_rows()
                         for c in riga if c.value is not None).lower()
    for ritirato in ("pareggio", "margine ×", "1.125", "1.374"):
        if ritirato in testi_min:
            guai.append(f"compare ancora «{ritirato}», che appartiene alla soglia ritirata")

    # le cifre chiave devono comparire da qualche parte
    testi = " ".join(str(c.value) for ws in wb for riga in ws.iter_rows()
                     for c in riga if c.value is not None)
    f = d["valore_futuro"]
    for nome, atteso in (("a parità di primo ordine", f["pari_partenza"]["stima"]),
                         ("a parità di spesa nei 90 giorni", f["pari_spesa_90"]["stima"]),
                         ("spesa media di chi torna", f["tornati_media"])):
        if str(atteso) not in testi and f"{atteso:,}".replace(",", ".") not in testi:
            guai.append(f"la cifra «{nome}» ({atteso}) non compare nel file")
    return guai


def main() -> None:
    if not DATI.is_file():
        raise SystemExit("Manca sito/dati.json. Lancia prima 08_dati_pagina.py.")
    d = json.loads(DATI.read_text(encoding="utf-8"))

    wb = Workbook()
    foglio_leggimi(wb, d)
    foglio_matrice(wb, d, per_calendario=False)
    foglio_matrice(wb, d, per_calendario=True)
    foglio_riacquisto(wb, d)
    foglio_valore(wb, d)
    n = foglio_dati(wb, d)

    wb.properties.title = "Clienti che tornano"
    wb.properties.subject = "Coorti, retention e riacquisto su Online Retail II"
    wb.properties.creator = "Raffaele Ciccone"
    wb.save(USCITA)

    print(f"scritto {USCITA.name}  ({USCITA.stat().st_size / 1024:.0f} KB)")
    print(f"  fogli: {', '.join(wb.sheetnames)}")
    print(f"  righe nel foglio dati: {n}")
    f = d["valore_futuro"]
    print(f"  a parità di primo ordine: {f['pari_partenza']['stima']:,} "
          f"[{f['pari_partenza']['ic'][0]:,}, {f['pari_partenza']['ic'][1]:,}]")

    guai = verifica(d)
    if guai:
        print(f"\nPROBLEMI ({len(guai)}):")
        for g in guai:
            print(f"  - {g}")
        sys.exit(1)
    print("  riaperto e ricontrollato: le due matrici contengono le stesse celle,")
    print("  le colonne del calendario sono mesi veri, la soglia ritirata non compare")


if __name__ == "__main__":
    main()
