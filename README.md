# Quanto vale un cliente che torna

Analisi di coorte, retention e riacquisto sul dataset **Online Retail II**: un negozio
online britannico di articoli da regalo, da dicembre 2009 a dicembre 2011, 1.067.371 righe.

**Domanda:** quanto vale un cliente che torna? Conviene di più trattenerlo o acquisirne
uno nuovo?

**Strumenti:** MySQL 8 (funzioni finestra), Python, Excel.

**[Apri la pagina interattiva](https://raffaeleciccone-analyst.github.io/clienti-che-tornano/)**

---

## Risultati

- **La retention segue il calendario, non l'anzianità del cliente.** Il mese dell'anno
  spiega il doppio della variazione rispetto all'età del cliente (34,8% contro 16,6%).
  A novembre torna il 25% dei clienti, a febbraio il 12%. Confrontare le coorti per
  retention vuol dire confrontare il mese in cui sono entrate, non la qualità dei clienti.
- **Chi torna presto spende di più anche dopo, ma lo si capisce già da quanto ha speso.**
  Sui 3.334 clienti entrati nel 2010: a parità di primo ordine, chi torna nei primi 90
  giorni spende **£756 in più** nei mesi successivi (intervallo £548–£1.025). A parità di
  spesa nei primi 90 giorni il vantaggio scende a **£150** (da −£67 a £374). Il numero di
  ordini aggiunge poco a quanto il cliente ha già speso.
- **A ogni ordine torna il 72,3% dei clienti, sempre uguale.** Arrivare al secondo
  acquisto non rende il cliente più fedele: "portali al secondo ordine e sono tuoi" qui
  non vale.
- **Non c'è un momento in cui il cliente è perso.** La probabilità di ritorno cala
  piano, senza un crollo. Il tempo mediano tra un ordine e l'altro è 64 giorni.

Due domande iniziali sono rimaste senza risposta: il valore del cliente a 24 mesi non si
può misurare (nessuna coorte ha 24 mesi completi di dati) e una soglia di abbandono non
esiste.

---

## Il limite più importante

**Il 22,8% delle righe non ha il codice cliente** (8.752 fatture). Questo cambia la cifra
principale:

| se i clienti anonimi... | clienti | tornano |
|---|---:|---:|
| sono gli stessi già contati | 5.852 | 72,4% |
| sono tutti clienti diversi, mai tornati | 14.604 | **29,0%** |

Il tasso vero sta tra il 29% e il 72%, e con questi dati non si può stringere. Quindi
la frase corretta è "tre clienti **identificati** su quattro tornano".

Gli altri risultati restano validi perché sono confronti interni (chi torna contro chi
non torna, novembre contro gennaio), e i clienti anonimi non stanno da nessuna delle due
parti.

## Cosa l'analisi non può dire

- **Se convenga trattenere o acquisire:** manca il costo di acquisizione.
- **Fino a quanto conviene spendere per far tornare un cliente:** chi torna da solo è
  soprattutto chi spendeva già di più, quindi non si può assumere che un cliente riportato
  con una campagna si comporti come lui. Serve un test con la riattivazione assegnata a caso.
- **Il profitto:** manca il costo del venduto, quindi si misura il ricavo.
- **Perché un cliente torna:** non ci sono dati su campagne, canali o visite al sito.
- **Un rapporto di causa:** "i clienti che tornano valgono di più" è vero; "farli tornare
  li fa valere di più" andrebbe provato con un esperimento.
- **Età del cliente e calendario non si separano del tutto** con soli due anni di dati:
  il calendario pesa di più, ma questo non vuol dire che l'età non conti.
- **I dati sono del 2009-2011:** il metodo si può riusare, i numeri no.

---

## Cosa contiene il progetto

- **`clienti-che-tornano.xlsx`**: cartella Excel con sei fogli: istruzioni, le due matrici
  di retention (per età e per calendario), riacquisto, valore (con gli intervalli), dati in
  formato lungo pronti per una tabella pivot.
- **`index.html`**: la [pagina interattiva](https://raffaeleciccone-analyst.github.io/clienti-che-tornano/). La matrice di retention si
  può allineare per età del cliente o per mese del calendario, così la stagionalità si
  vede direttamente.

Excel e pagina leggono gli stessi dati (`sito/dati.json`), quindi i numeri coincidono.

Ho usato un assistente IA per scrivere il codice. La domanda, il metodo e la verifica dei
numeri sono miei. Per esempio, il primo confronto dava £1.374 di differenza: era falsato,
e l'ho rifatto decidendo chi "torna" nei primi 90 giorni e contando la spesa solo dopo.

### Documenti

| File | Contenuto |
|---|---|
| [`DOMANDA.md`](DOMANDA.md) | la domanda e le cinque sotto-domande, scritte prima di aprire i dati |
| [`DATI-SPORCHI.md`](DATI-SPORCHI.md) | otto problemi trovati nei dati e quante righe toglie ogni pulizia |
| [`MODELLO.md`](MODELLO.md) | lo schema a stella e le trappole della finestra di osservazione |
| [`RISULTATI.md`](RISULTATI.md) | i risultati completi, con intervalli e limiti |
| [`CHANGELOG.md`](CHANGELOG.md) | le correzioni fatte dopo la pubblicazione |

### Script, nell'ordine in cui si lanciano

| Script | Cosa fa |
|---|---|
| `01_censimento.py` | conta i problemi nel file grezzo, senza modificarlo |
| `02_ricontrollo.py` | ricontrolla quanto scritto in `DATI-SPORCHI.md` |
| `04_carica.py` | pulisce i dati, crea lo schema (`03_schema.sql`) e carica MySQL |
| `05_analisi.py` | calcola le misure |
| `06_ricontrollo.py` | 68 controlli sui numeri di `RISULTATI.md`, rifatti dalle tabelle di base |
| `07_audit.py` | controlla le scelte di analisi: pulizie eccessive, confronti sbilanciati, conclusioni troppo forti |
| `08_dati_pagina.py` | prepara i dati per la pagina e per Excel |
| `09_pagina.py` | genera `index.html` |
| `10_excel.py` | genera la cartella Excel e la ricontrolla |
| `sito/prova_pagina.js` | prova la pagina fuori dal browser (Node) |

Serve **MySQL 8** e la password del database nella variabile `DB_PASSWORD`.

### Requisiti e test

Cosa deve fare l'analisi e come si controlla è scritto in [`SPEC.md`](SPEC.md) (17 criteri) e
[`PIANO.md`](PIANO.md). Ogni criterio ha un test in `tests/`:

```
pip install -r requirements-test.txt
python -m pytest tests -v
```

Senza MySQL i test che rifanno i conti sul database si saltano; gli altri controllano la
pulizia sul file originale, i numeri della pagina e dell'Excel, e i documenti.

---

## I dati

**Online Retail II**, UCI Machine Learning Repository,
[dataset 502](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
Il file originale è in `dati_grezzi/`, non modificato:

```
online_retail_II.xlsx   45.622.278 byte
sha256                  bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980
```

L'ho lasciato in Excel con i suoi due fogli apposta: 1.088 fatture compaiono in tutti e
due i fogli e raddoppierebbero dicembre 2010. Si possono contare solo sapendo da quale
foglio viene ogni riga, cosa che un unico CSV non permetterebbe.
