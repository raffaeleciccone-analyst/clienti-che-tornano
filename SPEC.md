# Quanto vale un cliente che torna — SPEC (cosa e perché)

> Questo file dice COSA deve fare l'analisi, non COME. Il come sta in PIANO.md.
> La domanda e il ragionamento completo sono in `DOMANDA.md`, i risultati in `RISULTATI.md`:
> questa spec ne ricava funzioni e criteri controllabili.
> Stato: **APPROVATA il 21/11/2026**, ricostruita da un progetto già esistente.

## 1. Problema
Chi decide il budget marketing di un negozio online vuole sapere **quanto vale un cliente che torna**
e se conviene spendere per farlo tornare o per trovarne uno nuovo. Senza misure oneste si rischia di
pagare per "far tornare" clienti che sarebbero tornati comunque, o che valevano di più già da prima.

## 2. Uso principale
- U1. Chi decide apre la pagina interattiva o il file Excel e capisce in pochi minuti quanti clienti
  tornano, quando, quanto valgono, e cosa i dati non possono dire.
- U2. Un selezionatore o un docente apre il repository, legge risultati e limiti, e può rifare tutto
  dal file originale.

## 3. Cosa fa
- F1. Pulisce il file originale con passaggi dichiarati, contando le righe tolte a ogni passaggio.
- F2. Costruisce la matrice di retention per coorte (mese della prima fattura × mesi successivi).
- F3. Mostra che la retention dipende dal mese del calendario più che dall'età del cliente.
- F4. Misura la sopravvivenza da un ordine al successivo (non un "funnel di conversione").
- F5. Misura il tempo fra primo e secondo ordine e verifica se esiste una soglia di abbandono.
- F6. Misura quanto spende dopo chi torna presto, a parità di partenza e a parità di spesa iniziale,
  con intervalli di confidenza.
- F7. Dichiara il limite dei clienti anonimi e quanto sposta il risultato principale.
- F8. Consegna una **pagina web interattiva** (online su GitHub Pages) e un **file Excel**, che leggono
  gli stessi dati.
- F9. Ricontrolla da sola ogni cifra pubblicata e le conclusioni scritte nei documenti.

## 3b. Da dove arrivano i dati
- D1. Online Retail II, UCI Machine Learning Repository (dataset 502), file originale nel repository in
  `dati_grezzi/`, con impronta sha256 dichiarata (confermato).
- D2. Database MySQL 8 locale, caricato da `04_carica.py` (confermato).

## 4. Cosa NON fa
- Non dice se trattenere convenga più che acquisire: manca il costo di acquisizione.
- Misura ricavo, non profitto: manca il costo del venduto.
- Non dice perché un cliente torna: non ci sono campagne, canali, visite.
- Non dimostra un rapporto di causa (servirebbe un esperimento con la riattivazione a caso).
- Non misura il valore a 24 mesi: nessuna coorte utile ha 24 mesi interi.
- Non descrive un "e-commerce internazionale": il 92% delle righe è Regno Unito.
- Non calcola una soglia di spesa per la riattivazione (punto di pareggio): ritirata il 2/10, i dati non
  la sostengono.

## 5. Criteri di controllo
Ogni criterio diventa un test automatico. "Finito" = tutti i test passano.
I numeri attesi sono quelli di `DATI-SPORCHI.md` e `RISULTATI.md` (sezione 9 per il valore).

**Pulizia (F1)**
- C1. Dal file originale: 1.067.371 righe → 1.033.034 senza duplicati → 797.883 con cliente →
  779.493 senza storni e quantità negative → 779.405 senza prezzi sotto un penny → 776.577 senza codici
  che non sono prodotti (lista chiusa in `regole.py`; SP1002 e PADS restano, vedi R1).
- C2. L'impronta sha256 del file originale è quella scritta nel README: nessuno script lo modifica.
- C3. Le 1.088 fatture presenti in tutti e due i fogli contano una volta sola.

**Retention (F2, F3)**
- C4. 23 coorti utili, 253 celle osservate; le celle che il calendario non ha ancora raggiunto sono
  **vuote, non zero**; dicembre 2011 (9 giorni) non conta come mese.
- C5. Retention media per mese del calendario: novembre 25%, febbraio 12%; il mese del calendario spiega
  il 34,8% della variazione, l'età del cliente il 16,6%.

**Riacquisto e tempi (F4, F5)**
- C6. Sui 3.334 clienti entrati nel 2010: al 2º ordine arrivano 2.373 (71,2%); dal 2º in poi a ogni
  gradino sopravvive circa il 72,3%.
- C7. Tempo fra primo e secondo ordine: mediana 64 giorni; di chi torna entro l'anno, il 60,9% è tornato
  entro 90 giorni e l'83,3% entro 180. Nessun punto in cui la probabilità di ritorno crolla.

**Valore (F6)**
- C8. Tornati entro 90 giorni: 1.446 su 3.334 (43,4%). Spesa dal giorno 91 al 365: £1.355 contro £432.
- C9. Differenza a parità di primo ordine e coorte: £756 (intervallo £548–£1.025); a parità di spesa
  nei primi 90 giorni: £150 (da −£67 a £374).

**Limite dei clienti anonimi (F7)**
- C10. 22,8% delle righe senza `Customer ID` (8.752 fatture); il tasso di chi torna sta fra il 29,0% e
  il 72,4% a seconda di chi sono gli anonimi (4.234 clienti che tornano su 5.852 identificati;
  fino al 21/11 era scritto a mano «72,3%», un arrotondamento sbagliato di 72,35%).

**Consegne (F8)**
- C11. La pagina `index.html` funziona aperta da file (dati incorporati, nessun `fetch`), le cifre chiave
  compaiono nel testo, ed è raggiungibile online.
- C12. Pagina ed Excel mostrano gli stessi numeri (leggono lo stesso `sito/dati.json`).
- C13. Il file Excel ha i suoi fogli; le due matrici (per età e per calendario) contengono le stesse celle
  della pagina, e ogni colonna della matrice per calendario è un solo mese vero. *(prima C13 chiedeva
  le formule del pareggio: tolte con Q1)*
- C17. *(aggiunto il 21/11, Q1)* Né il file Excel né la pagina né il README presentano una soglia di
  pareggio o la cifra ritirata (£1.125, £1.374, «margine ×»): il foglio "Valore" mostra £756 e £150 con
  gli intervalli e spiega perché una soglia non si può calcolare (serve un test con la riattivazione a caso).
  La sezione "LA RISPOSTA" dell'Excel usa la frase corretta del 2/10.

**Autocontrollo e documenti (F9)**
- C14. I 68 controlli di `06_ricontrollo.py` passano (ricalcolo dalle tabelle di base, senza le viste).
- C15. L'audit `07_audit.py` non trova niente da sistemare: le frasi di `RISULTATI.md` non dicono più di
  quanto i dati permettono.
- C16. I numeri citati nel README e in `DOMANDA.md` coincidono con quelli dei criteri (oggi `DOMANDA.md`
  parla di 63 controlli, sono 68).

## 5b. Regole di calcolo
*(aggiunte il 21/11/2026 dopo una ricostruzione alla cieca: un agente che aveva solo i documenti ha
dovuto indovinarle. Erano scritte solo nel codice.)*

- R1. **Pulizia:** le regole stanno in `regole.py` e solo lì. Duplicato = uguale nelle sei colonne di
  `CHIAVE`. Prezzo minimo £0,01 (sotto non è una vendita). La lista dei codici non-prodotto è chiusa e
  ogni codice ha il suo motivo; `SP1002` (lavagnetta) e `PADS` (imbottiture) **sono prodotti**.
- R2. **Giorni:** si contano fra date del calendario, non fra istanti. Le finestre includono gli estremi:
  "entro 90 giorni" = giorno 0-90, la spesa "dopo" = giorni 91-365, l'anno = giorni 0-365.
- R3. **Coorti:** la coorte è il mese della prima fattura; dicembre 2009 e dicembre 2011 sono fuori. Una
  cella esiste solo se il mese è finito; le 253 celle osservate non contano il mese +0 (che vale sempre 100%).
- R4. **Media per mese del calendario:** media semplice delle celle di quel mese, non pesata per clienti.
- R5. **Quota di variazione spiegata:** 1 − (scarti dal modello)² / (scarti dalla media)². Per età e per
  calendario il modello è la media del gruppo; per "insieme" è la somma dei due effetti (minimi quadrati),
  non il raggruppamento per coppia.
- R6. **Sopravvivenza media:** media semplice della quota che sopravvive dal 2º al 6º gradino.
- R7. **Confronti a parità (£756 e £150):** i decili si calcolano su tutti i 3.334 clienti; lo strato è
  decile × coorte; uno strato entra solo se ha **almeno 3 clienti da ogni parte** (tornati e non); la
  differenza è la media delle differenze degli strati pesata per la dimensione dello strato. Intervallo:
  2.000 ricampionamenti dentro ogni strato, tornati e non tornati ricampionati separatamente, percentili 2,5 e 97,5, generatore con seme
  fisso 20260827. Con un altro generatore gli estremi cambiano: una ricostruzione indipendente
  è "uguale" se le stime coincidono e ogni estremo sta entro £25 da quello pubblicato.
- R7b. Strati validi: 110 (98,6% dei clienti) a parità di primo ordine, 89 (84,3%) a parità di spesa a
  90 giorni. *(i "105 strati, 95%" di RISULTATI §6 sono del metodo ritirato il 2/10)*
- R7c. **Dettagli del valore:** il "primo ordine" per i decili è il valore della prima fattura; un cliente
  "ha 365 giorni davanti" se l'ultima data del file meno la data del primo ordine è almeno 365; una seconda
  fattura nello stesso giorno della prima conta come ritorno.
- R7d. **Buoni regalo:** tutti i codici che cominciano con `gift_0001_`. **Curva del secondo ordine:** punti
  ogni 10 giorni fino a 360; percentili con il metodo lineare (quello predefinito di numpy).
- R8. **Arrotondamento:** percentuali al decimale più vicino, sterline all'unità. Nessun numero si scrive a
  mano negli script che producono i dati: si calcola.

## 6. Vincoli
- MySQL 8 (funzioni finestra), password in `DB_PASSWORD`. Python per pulizia, analisi, Excel e pagina.
- I test che usano il database girano solo se MySQL è raggiungibile, altrimenti si saltano e lo dicono.
- La pagina deve funzionare anche scaricata e aperta senza server.

## 7. Domande aperte
- ~~Q1~~ Risolta il 21/11: il calcolo del pareggio si toglie dall'Excel (e dal README); il ragionamento
  vecchio resta solo in `RISULTATI.md` §8, segnato come ritirato. Vedi C17.
