"""Costruisce index.html: il modello più i dati, cuciti insieme.

I dati vengono INCORPORATI nella pagina, non caricati con fetch. Non è pigrizia:
fetch su file:// è bloccato dal browser, e una pagina che funziona solo quando
è su un server è una pagina che chi la scarica vede rotta senza capire perché.

Uso:  python 09_pagina.py            (costruisce e apre)
      python 09_pagina.py --no-apri
"""
from __future__ import annotations

import json
import re
import sys
import webbrowser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUI = Path(__file__).parent
MODELLO = QUI / "sito" / "modello.html"
DATI = QUI / "sito" / "dati.json"
USCITA = QUI / "index.html"
SEGNO = "/*DATI*/"


def main() -> None:
    for f in (MODELLO, DATI):
        if not f.is_file():
            raise SystemExit(f"Manca {f}. Lancia prima 08_dati_pagina.py.")

    modello = MODELLO.read_text(encoding="utf-8")
    if SEGNO not in modello:
        raise SystemExit(f"Il modello non contiene {SEGNO}: non so dove mettere i dati.")

    dati = json.loads(DATI.read_text(encoding="utf-8"))
    # allow_nan=False: un NaN dentro il JSON rende illeggibile TUTTA la pagina, e
    # il browser non dice quale campo. Meglio fallire qui.
    compatto = json.dumps(dati, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    # `</script>` dentro una stringa chiuderebbe il blocco prima del tempo
    compatto = compatto.replace("</", "<\\/")

    pagina = modello.replace(SEGNO, compatto, 1)
    USCITA.write_text(pagina, encoding="utf-8")

    print(f"scritta {USCITA}  ({USCITA.stat().st_size / 1024:.0f} KB)")

    # ── controlli, prima di dire che è fatta ────────────────────────────
    problemi = []
    if SEGNO in pagina:
        problemi.append("il segnaposto dei dati è ancora nella pagina")
    if "NaN" in compatto:
        problemi.append("c'è un NaN nei dati: la pagina non caricherebbe")
    # ogni id usato dallo script deve esistere nel documento
    usati = set(re.findall(r'getElementById\("([^"]+)"\)', pagina))
    presenti = set(re.findall(r'\bid="([^"]+)"', pagina))
    if usati - presenti:
        problemi.append(f"id cercati dallo script ma assenti: {sorted(usati - presenti)}")
    # le variabili di colore usate dal disegno devono essere dichiarate
    for nome in ("--freddo", "--tiepido", "--caldo"):
        if pagina.count(nome) < 2:
            problemi.append(f"la variabile di colore {nome} non è dichiarata")

    print(f"  coorti nella matrice   {len(dati['coorti'])}")
    print(f"  id verificati          {len(usati)}")
    print(f"  differenza appaiata    {dati['valore']['appaiata']:,} "
          f"[{dati['valore']['appaiata_ic'][0]:,}, {dati['valore']['appaiata_ic'][1]:,}]")

    if problemi:
        print("\nPROBLEMI:")
        for p in problemi:
            print(f"  - {p}")
        sys.exit(1)
    print("  nessun problema")

    if "--no-apri" not in sys.argv:
        webbrowser.open(USCITA.resolve().as_uri())
        print("aperta nel browser")


if __name__ == "__main__":
    main()
