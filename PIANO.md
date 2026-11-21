# Quanto vale un cliente che torna — PIANO (come)

> Il COSA sta in SPEC.md. Qui c'è il COME.
> Ogni scelta tecnica cita la frase della spec che la giustifica.
> Se una scelta qui contraddice la spec, vince la spec: si corregge il piano.
> Stato: 21/11/2026, prima stesura (progetto esistente portato "by spec").

## 1. Architettura

```
dati_grezzi/online_retail_II.xlsx  (nel repo, sola lettura — D1, C2)
   │
   ├─ 01_censimento.py, 02_ricontrollo.py   lo sporco contato sul grezzo (DATI-SPORCHI.md)
   ├─ 04_carica.py  pulisci() ─> MySQL 8 (schema a stella, 03_schema.sql)          F1, C1
   │                                 │
   │      05_analisi.py, valore_futuro.py ── misure ──> RISULTATI.md               F2-F7
   │      06_ricontrollo.py  68 cifre rifatte dalle tabelle di base                C14
   │      07_audit.py        attacca le decisioni e le frasi di RISULTATI.md       C15
   │      08_dati_pagina.py ─> sito/dati.json ─┬─> 09_pagina.py ─> index.html       C11
   │                                           └─> 10_excel.py  ─> .xlsx           C12, C13, C17
   │
   └─ tests/  (pytest) — un test per criterio
```

## 2. Scelte e motivi
- **I criteri C4-C10 si controllano su `sito/dati.json`, non sul database.** Motivo: è il file che
  pagina ed Excel mostrano davvero (C12), è nel repository e i test girano anche senza MySQL.
  Che `dati.json` dica la verità lo controlla un test a parte: rigenerarlo dal database non cambia
  niente (stesso principio del report Power BI).
- **I test che toccano MySQL si saltano se il database non risponde** (SPEC §6), dicendo perché.
- **La pulizia esce da `main()` di `04_carica.py` in una funzione `pulisci()`** che restituisce le righe
  rimaste e i conteggi di ogni passaggio. Motivo: C1 deve poter contare i passaggi senza caricare il
  database. Il comportamento di `04_carica.py` non cambia.
- **C1 segue l'ordine dei passaggi del codice**; il conteggio intermedio di `DATI-SPORCHI.md` §3
  (779.493, storni e quantità insieme) si controlla a parte, applicando le due regole insieme.
- **C11 usa `sito/prova_pagina.js` (Node)**, che esiste già, più una lettura dell'HTML (niente `fetch`)
  e una richiesta alla pagina online (saltata se non c'è rete).
- **Il pareggio esce da `10_excel.py` (Q1, C17).** Il foglio si chiama "Valore" e mostra la sezione 9
  di `RISULTATI.md`: £1.355 contro £432, £756 (548–1.025), £150 (−67–374), con una frase su perché
  una soglia non si può calcolare. La sezione "LA RISPOSTA" del foglio Leggimi usa la frase corretta.
  `verifica()` smette di cercare le formule del pareggio e controlla invece che le cifre ritirate non
  compaiano.

## 3. Struttura dei test

```
tests/
  conftest.py          percorsi; fixture dati.json; connessione MySQL (salta se assente)
  test_pulizia.py      C1, C2, C3
  test_analisi.py      C4-C10 su dati.json; rigenerare dati.json dal DB non cambia niente
  test_consegne.py     C11, C12, C13, C17 (Excel e pagina)
  test_documenti.py    C14 (06_ricontrollo), C15 (07_audit), C16 (README, DOMANDA), C17 (README)
requirements-test.txt  pytest
```

```
python -m pytest tests -v
```

## 4. Da fare
- [ ] Test (prima rossi dove il codice non rispetta la spec: C1 senza `pulisci()`, C16, C17).
- [ ] `pulisci()` in `04_carica.py`; foglio "Valore" in `10_excel.py`; `DOMANDA.md` (68 controlli); README.
- [ ] Prova che i test valgono: rompo una regola e controllo che se ne accorgano.
