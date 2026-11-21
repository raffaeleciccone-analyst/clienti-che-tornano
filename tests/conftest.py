# Fixture comuni. I test che usano MySQL si saltano se il database non risponde (SPEC §6).
import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))


def carica_modulo(nome_file):
    """Gli script cominciano con un numero (04_carica.py): si importano dal percorso."""
    spec = importlib.util.spec_from_file_location(nome_file.replace(".py", "").lstrip("0123456789_"),
                                                  RADICE / nome_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def dati():
    return json.loads((RADICE / "sito" / "dati.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def mysql():
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("localhost", 3306))
    except OSError:
        pytest.skip("MySQL non raggiungibile su localhost:3306")
    finally:
        s.close()
    try:
        carica_modulo("04_carica.py").url()
    except SystemExit as e:
        pytest.skip(str(e))
    return True


@pytest.fixture(scope="session")
def pulizia():
    """Il grezzo letto e pulito una volta sola (il file è da 45 MB)."""
    carica = carica_modulo("04_carica.py")
    if not hasattr(carica, "pulisci"):
        pytest.fail("04_carica.py non ha ancora la funzione pulisci() (PIANO §2)")
    grezzo = carica.leggi_grezzo(con_foglio=True)
    pulito, passaggi = carica.pulisci(grezzo, stampa=False)
    return grezzo, pulito, passaggi, carica
