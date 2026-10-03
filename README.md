# Quanto vale un cliente che torna

Analisi di coorte, retention e riacquisto su **Online Retail II** — un negozio online
britannico di articoli da regalo, dicembre 2009 – dicembre 2011, 1.067.371 righe.

La domanda è una sola, ed è stata scritta prima di aprire SQL:

> **Quanto vale un cliente che torna, e conviene di più trattenerlo o acquisirne uno
> nuovo?**

---

## Cos'è venuto fuori

**La retention di questo negozio non è una curva di abbandono: è un calendario.** Il
mese dell'anno spiega il doppio dell'età del cliente (34,8% contro 16,6% della
variazione). A novembre torna il 25% dei clienti, a febbraio il 12%. Una classifica
delle coorti per retention misurerebbe il mese di ingresso, non la qualità dei clienti.

**Chi torna presto spende di più anche dopo, ma lo prevede già quanto ha speso.** Fra i
3.334 clienti entrati nel 2010, il gruppo si decide nei primi 90 giorni e la spesa si
conta dal giorno 91 al 365. A parità di primo ordine chi è tornato spende **£756** in
più (£548–£1.025). A parità di spesa nei primi 90 giorni il vantaggio scende a **£150**
(da −£67 a £374): sapere che ha fatto più di un ordine non aggiunge quasi niente a
quanto ha speso. È una lettura predittiva, non causale: la spesa dei primi 90 giorni
contiene già il secondo ordine (`RISULTATI.md`, sezione 9).

**La sopravvivenza da un ordine al successivo è costante: 72,3% a ogni gradino.**
Arrivare al secondo ordine non mette al sicuro — «portali al secondo acquisto e sono
tuoi» qui è falso.

**La soglia di silenzio oltre la quale un cliente è perso non esiste.** La probabilità
di ritorno cala in modo regolare e non crolla mai. Resta la mediana: 64 giorni.

Due domande poste all'inizio non hanno avuto risposta, e sta scritto: il valore a 24
mesi **non è misurabile** (nessuna coorte utile ha 24 mesi interi), e la soglia di
silenzio **non c'è**.

---

## I documenti, nell'ordine in cui sono stati scritti

| file | cos'è |
|---|---|
| `DOMANDA.md` | la domanda e le cinque sotto-domande, scritte prima di guardare i dati |
| `DATI-SPORCHI.md` | otto difetti contati sul file vero, con quante righe toglie ogni pulizia |
| `MODELLO.md` | lo schema a stella, perché non era così all'inizio, e le quattro trappole della finestra di osservazione |
| `RISULTATI.md` | le risposte, con gli intervalli e ciò che i numeri non dicono |
| `CHANGELOG.md` | le correzioni dopo la pubblicazione: cosa diceva prima, perché era sbagliato, cosa dice adesso |

I documenti non sono stati riscritti quando una verifica li ha smentiti: la correzione
sta accanto a quello che diceva prima. `MODELLO.md` registrava «il salto più grande è
il primo»; era un artefatto del tempo di osservazione, e sta lì con scritto perché.

---

## Gli script, nell'ordine in cui si lanciano

```
python 01_censimento.py     conta lo sporco sul file grezzo, senza modificarlo
python 02_ricontrollo.py    riverifica le affermazioni di DATI-SPORCHI.md
python 04_carica.py         pulisce, carica MySQL, controlla dopo il caricamento
python 05_analisi.py        le misure -> risultati/misure.txt
python 06_ricontrollo.py    68 controlli sulle cifre di RISULTATI.md
python 07_audit.py          cerca errori e bias nelle DECISIONI, non nelle cifre
python 08_dati_pagina.py    quello che serve alla pagina -> sito/dati.json
python 09_pagina.py         cuce dati e modello -> index.html
python 10_excel.py          la cartella di lavoro -> clienti-che-tornano.xlsx
node   sito/prova_pagina.js fa girare lo script della pagina con un DOM finto
python anteprima_dati.py    una pagina per guardare il file grezzo senza Excel
```

### La cartella di lavoro

`clienti-che-tornano.xlsx` e la pagina web sono due consegne della stessa analisi, e
leggono lo stesso `sito/dati.json`: se una cifra non torna fra le due, il colpevole è
uno solo.

Sei fogli: il **Leggimi** con la domanda, la risposta e i limiti; **due matrici** con le
stesse celle nei due allineamenti, da confrontare; il **riacquisto** col funnel e il
tempo al secondo ordine; **valore e pareggio**; e i **dati in formato lungo**, una riga
per cella, da cui si fa una tabella pivot senza dover disfare una matrice larga.

Il foglio del pareggio contiene **formule vere**, non valori incollati: si cambia il
margine nella cella gialla e la soglia si ricalcola. Era la richiesta di `DOMANDA.md` —
il margine resta un parametro dichiarato, non un risultato — e in un foglio di calcolo
si mantiene meglio che altrove, perché chi legge può cliccare sulla cella e vedere da
dove viene il numero.

Lo script riapre il file dopo averlo scritto e lo confronta con i dati di partenza:
openpyxl scrive senza lamentarsi anche quando il risultato è sbagliato — una cella
spostata di una riga, una formula diventata testo, una matrice allineata male.

### La pagina

`index.html` è la pagina pubblicata. I dati sono **incorporati**, non caricati con
`fetch`: `fetch` su `file://` è bloccato dal browser, e una pagina che funziona solo
quando sta su un server è una pagina che chi la scarica vede rotta senza capire
perché.

Il problema di progetto era uno solo: **impedire che la matrice si legga come una
discesa**. Quindi la matrice non è un'illustrazione, è l'interazione centrale — le
stesse celle, allineabili per età del cliente o per mese del calendario. Nel secondo
allineamento ogni riga parte dal suo mese vero e le colonne si accendono tutte insieme:
la stagionalità si vede invece di doverla credere. Nessun dato viene rimaneggiato per
ottenere l'effetto, cambiano solo le posizioni.

`sito/prova_pagina.js` fa girare lo script della pagina fuori dal browser con un DOM
finto. Non disegna niente e non sa niente di layout: serve a intercettare l'errore che
rompe le pagine più spesso, cioè quello che lascia il documento vuoto senza dire
perché. Controlla anche che le cifre chiave compaiano davvero nel testo prodotto, non
solo nei dati.

`03_schema.sql` lo applica `04_carica.py`. Serve **MySQL 8** (funzioni finestra) e la
password in `DB_PASSWORD`.

### Perché due script di verifica separati

`06_ricontrollo.py` rifà i conti **dalle tabelle di base, senza passare dalle viste**:
se una vista è sbagliata, la differenza salta fuori. Non rilancia `05_analisi.py`,
perché rifarebbe gli stessi passaggi e confermerebbe gli stessi errori.

`07_audit.py` fa un'altra cosa: attacca le decisioni. Le pulizie che potevano aver tolto
troppo, i confronti che potevano essere ancora sbilanciati, le interpretazioni che
potevano non reggere. Cinque dei suoi nove controlli **leggono `RISULTATI.md`**: se un
giorno quelle frasi vengono riscritte in modo più generoso di quanto i dati permettano,
lo script torna rosso. Ha già trovato quattro cose, tutte corrette — la più grossa è
in fondo a questa pagina.

---

## I dati

**Online Retail II**, UCI Machine Learning Repository, [dataset 502](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
Il file sta in `dati_grezzi/`, **come è arrivato**:

```
online_retail_II.xlsx   45.622.278 byte
sha256                  bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980
```

**Sta nel repo apposta, e va tenuto in due fogli.** Il difetto più grosso del dataset —
1.088 fatture presenti in tutte e due le annate, che raddoppiano dicembre 2010 — si può
contare solo sapendo da quale foglio viene ogni riga. Convertendolo in un CSV unico quel
conto non sarebbe più rifacibile da nessuno, e resterebbe solo la nostra parola.

Il file è in sola lettura. Nessuno script lo modifica: se una decisione di pulizia
cambia, si ricarica il database, non si aggiusta il file.

---

## Il limite più grosso, e non è fra quelli previsti

**Il 22,8% delle righe non ha un `Customer ID`** — 8.752 fatture. `DATI-SPORCHI.md` lo
dichiarava, ma l'avvertenza era stata applicata solo al fatturato, non alla cifra che
apre tutto: il 72,3% di clienti che tornano.

| ipotesi sugli anonimi | clienti | tornano |
|---|---:|---:|
| sono gli stessi già contati | 5.852 | 72,3% |
| ognuno un cliente diverso mai più tornato | 14.604 | **29,0%** |

**Il tasso vero sta fra il 29% e il 72%**, e con questi dati non si stringe. Quindi si
scrive «tre clienti **identificati** su quattro tornano», mai «tre clienti su quattro».

Le altre conclusioni reggono, e non è un salvataggio: sono confronti *interni* — chi
torna contro chi non torna, novembre contro gennaio, gradino contro gradino. Gli anonimi
non stanno su nessuno dei due lati, quindi non li inclinano.

## Cosa questa analisi non può dire

- **Non dice se trattenere convenga più che acquisire**: manca il costo di acquisizione.
  Dice a che prezzo le due cose si equivalgono.
- **Misura ricavo, non profitto**: manca il costo del venduto. Il margine è una manopola
  dichiarata, non un risultato.
- **Non dice perché un cliente è tornato**: non ci sono sessioni, campagne, canali.
- **Non dimostra un rapporto di causa.** «I clienti che tornano valgono N volte» è vero;
  «farli tornare li fa valere N volte» non è dimostrato qui, e servirebbe un esperimento
  con la riattivazione assegnata a caso. La differenza fra le due frasi è la differenza
  fra un'analisi che si può usare e una che fa perdere soldi.
- **Età del cliente + coorte = mese del calendario, per costruzione.** Con due anni di
  dati le tre cose non si separano: si può dire che il calendario spiega più dell'età,
  non che l'età non conti.
- **I dati sono del 2009-2011.** Il metodo si trasferisce, i numeri no.
