# Criteri C4-C10 di SPEC.md, controllati su sito/dati.json (quello che pagina ed Excel mostrano).
# L'ultimo test controlla che dati.json sia davvero quello che esce dal database.
import shutil
import subprocess
import sys

import pytest

from conftest import RADICE


def test_c4_coorti_e_celle(dati):
    coorti = dati["coorti"]
    assert len(coorti) == 23
    osservate = sum(1 for c in coorti for v in c["celle"][1:] if v is not None)
    assert osservate == 253
    # le celle non ancora raggiungibili sono vuote, non zero: l'ultima coorte ha solo il mese 0
    assert coorti[-1]["coorte"] == "2011-11" and coorti[-1]["celle"] == [100.0]
    assert all(v is None or v > 0 for c in coorti for v in c["celle"])


def test_c4_dicembre_2011_non_conta(dati):
    for c in dati["coorti"]:
        ultimo = (c["anno"] * 12 + c["mese"] - 1) + len(c["celle"]) - 1
        assert ultimo <= 2011 * 12 + 10, c["coorte"]   # novembre 2011 = ultimo mese intero


def test_c5_stagionalita(dati):
    quota = {m["mese"]: m["quota"] for m in dati["per_mese_calendario"]}
    assert round(quota[11]) == 25 and round(quota[2]) == 12
    assert dati["spiegata"]["calendario"] == 34.8 and dati["spiegata"]["eta"] == 16.6


def test_c6_sopravvivenza_da_un_ordine_al_successivo(dati):
    f = {g["gradino"]: g for g in dati["funnel"]}
    assert f[1]["clienti"] == 3_334
    assert f[2]["clienti"] == 2_373 and f[2]["quota"] == 71.2
    assert dati["sopravvivenza_media"] == 72.3


def test_c7_tempo_al_secondo_ordine_e_nessuna_soglia(dati):
    t = dati["tempo_secondo"]
    assert t["percentili"]["50"] == 64
    cum = {p["giorni"]: p["quota"] for p in t["cumulata"]}
    assert cum[90] == 60.9 and cum[180] == 83.3
    # nessun crollo: la quota cumulata cresce sempre, e ogni salto di 10 giorni resta piccolo
    valori = [p["quota"] for p in t["cumulata"]]
    assert all(b >= a for a, b in zip(valori, valori[1:]))


def test_c8_spesa_dopo_i_primi_90_giorni(dati):
    f = dati["valore_futuro"]
    assert (f["clienti"], f["tornati"], f["quota_tornati"]) == (3_334, 1_446, 43.4)
    assert (f["tornati_media"], f["altri_media"]) == (1_355, 432)


def test_c9_differenze_con_intervalli(dati):
    f = dati["valore_futuro"]
    assert f["pari_partenza"]["stima"] == 756 and f["pari_partenza"]["ic"] == [548, 1_025]
    assert f["pari_spesa_90"]["stima"] == 150 and f["pari_spesa_90"]["ic"] == [-67, 374]


def test_c10_clienti_anonimi(dati):
    a = dati["anonimi"]
    assert a["fatture"] == 8_752
    assert (a["quota_bassa"], a["quota_alta"]) == (29.0, 72.3)


@pytest.mark.skipif(shutil.which("git") is None, reason="git non disponibile")
def test_dati_json_e_quello_che_esce_dal_database(mysql):
    sporco = subprocess.run(["git", "status", "--porcelain", "--", "sito/dati.json"], cwd=RADICE,
                            capture_output=True, text=True).stdout
    if sporco.strip():
        pytest.skip("sito/dati.json ha modifiche non salvate")
    subprocess.run([sys.executable, "08_dati_pagina.py"], cwd=RADICE, check=True, capture_output=True)
    dopo = subprocess.run(["git", "diff", "--stat", "--", "sito/dati.json"], cwd=RADICE,
                          capture_output=True, text=True).stdout
    assert dopo.strip() == "", "dati.json rigenerato dal database è diverso:\n" + dopo
