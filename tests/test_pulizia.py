# Criteri C1-C3 di SPEC.md: la pulizia del file originale.
import hashlib
import re

from conftest import RADICE


def test_c1_catena_di_pulizia(pulizia):
    grezzo, pulito, passaggi, _ = pulizia
    assert len(grezzo) == 1_067_371
    conta = dict(passaggi)
    assert conta["Togli le righe duplicate"] == 1_033_034
    assert conta["Tieni solo le righe con cliente"] == 797_883
    assert conta["Togli le quantita non positive"] == 779_423
    assert len(pulito) == 776_575


def test_c1_storni_e_quantita_insieme_come_in_dati_sporchi(pulizia):
    grezzo, _, _, carica = pulizia
    df = grezzo[~grezzo.duplicated(subset=carica.CHIAVE)]
    df = df[df["Customer ID"].notna()]
    df = df[~df["Invoice"].str.startswith("C") & (df["Quantity"] > 0)]
    assert len(df) == 779_493          # DATI-SPORCHI §3
    assert int((df["Price"] > 0).sum()) == 779_423     # §4


def test_c1_nessun_codice_non_prodotto_resta(pulizia):
    _, pulito, _, carica = pulizia
    for codice in ["POST", "DOT", "M", "BANK CHARGES", "ADJUST", "S", "D"]:
        assert codice in carica.NON_PRODOTTI
    assert not pulito["StockCode"].isin(carica.NON_PRODOTTI).any()


def test_c2_il_file_originale_non_e_stato_toccato():
    readme = (RADICE / "README.md").read_text(encoding="utf-8")
    atteso = re.search(r"sha256\s+([0-9a-f]{64})", readme).group(1)
    h = hashlib.sha256((RADICE / "dati_grezzi" / "online_retail_II.xlsx").read_bytes()).hexdigest()
    assert h == atteso


def test_c3_fatture_nei_due_fogli_contano_una_volta(pulizia):
    grezzo, _, _, carica = pulizia
    fogli = grezzo.groupby("Invoice")["foglio"].nunique()
    assert int((fogli > 1).sum()) == 1_088
    dopo = grezzo[~grezzo.duplicated(subset=carica.CHIAVE)]
    assert not dopo.duplicated(subset=carica.CHIAVE).any()
