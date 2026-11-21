# Criteri C11-C13 e C17 di SPEC.md: la pagina e il file Excel.
import re
import shutil
import subprocess
import urllib.request

import pytest
from openpyxl import load_workbook

from conftest import RADICE

PAGINA_ONLINE = "https://raffaeleciccone-analyst.github.io/clienti-che-tornano/"
RITIRATI = ["pareggio", "margine ×", "margine x", "1.125", "1.374"]


@pytest.fixture(scope="module")
def excel():
    return load_workbook(RADICE / "clienti-che-tornano.xlsx")


def _testo_excel(wb, fogli=None):
    return " ".join(str(c.value) for ws in wb if fogli is None or ws.title in fogli
                    for riga in ws.iter_rows() for c in riga if c.value is not None)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node non installato")
def test_c11_la_pagina_gira_e_mostra_le_cifre():
    p = subprocess.run(["node", "sito/prova_pagina.js"], cwd=RADICE, capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "[NO]" not in p.stdout


def test_c11_la_pagina_funziona_senza_server():
    html = (RADICE / "index.html").read_text(encoding="utf-8")
    assert "fetch(" not in html
    assert "src=\"http" not in html            # nessuno script esterno
    assert "\"valore_futuro\"" in html          # i dati sono incorporati


def test_c11_la_pagina_e_online():
    try:
        with urllib.request.urlopen(PAGINA_ONLINE, timeout=10) as r:
            assert r.status == 200
            assert "Clienti che tornano" in r.read().decode("utf-8", "replace")
    except OSError as e:
        pytest.skip("niente rete: " + str(e))


def test_c12_pagina_ed_excel_leggono_gli_stessi_dati(dati):
    html = (RADICE / "index.html").read_text(encoding="utf-8")
    incorporati = re.search(r"const D\s*=\s*(\{.*?\});\s*\n", html, re.S)
    assert incorporati, "non trovo i dati incorporati nella pagina"
    import json
    assert json.loads(incorporati.group(1)) == dati


def test_c13_fogli_e_matrici_dell_excel(dati):
    excel = carica_10_excel()
    assert excel.verifica(dati) == []


def test_c17_niente_pareggio_nell_excel(excel):
    testo = _testo_excel(excel).lower()
    trovati = [r for r in RITIRATI if r in testo]
    assert not trovati, "l'Excel mostra ancora il pareggio ritirato: %s" % trovati
    assert "Valore" in excel.sheetnames


def test_c17_il_foglio_valore_mostra_i_numeri_del_2_ottobre(excel):
    t = _testo_excel(excel, fogli={"Valore", "Leggimi"})
    for cifra in ["756", "150", "548", "1.025", "-67", "374"]:
        assert cifra in t, cifra


def carica_10_excel():
    from conftest import carica_modulo
    return carica_modulo("10_excel.py")
