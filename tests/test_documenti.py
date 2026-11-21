# Criteri C14-C17 di SPEC.md: l'autocontrollo e i documenti.
import re
import subprocess
import sys

from conftest import RADICE


def lancia(script):
    p = subprocess.run([sys.executable, script], cwd=RADICE, capture_output=True, text=True,
                       encoding="utf-8", timeout=900)
    return p.returncode, p.stdout + p.stderr


def test_c14_i_68_controlli_passano(mysql):
    codice, out = lancia("06_ricontrollo.py")
    assert "controlli: 68 su 68 passati" in out, out[-2000:]


def test_c15_l_audit_non_trova_niente(mysql):
    codice, out = lancia("07_audit.py")
    assert "DA SISTEMARE: 0" in out, out[-2000:]


def test_c16_il_readme_cita_i_numeri_giusti(dati):
    readme = (RADICE / "README.md").read_text(encoding="utf-8")
    f, a = dati["valore_futuro"], dati["anonimi"]
    attesi = ["1.067.371", "34,8%", "16,6%", "25%", "12%", "72,3%", "64 giorni", "3.334",
              "£756", "£548–£1.025", "£150", "−£67 a £374", "22,8%", "8.752", "29,0%", "5.852",
              "14.604"]
    mancanti = [x for x in attesi if x not in readme]
    assert not mancanti, mancanti
    assert str(f["pari_partenza"]["stima"]) in readme and str(a["fatture"])[:1] in readme


def test_c16_domanda_dice_quanti_sono_i_controlli():
    domanda = (RADICE / "DOMANDA.md").read_text(encoding="utf-8")
    numeri = re.findall(r"\((\d+) controlli", domanda)
    assert numeri and all(n == "68" for n in numeri), numeri


def test_c17_niente_pareggio_nel_readme():
    readme = (RADICE / "README.md").read_text(encoding="utf-8").lower()
    assert "pareggio" not in readme
    assert "si cambia il\n  margine" not in readme and "cambia il margine" not in readme
