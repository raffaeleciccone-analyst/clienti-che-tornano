# La domanda, scritta prima di aprire SQL

Finché questo file non è deciso, il database resta vuoto.

Le ipotesi da controllare sono marcate `[V]`. Quando la verifica arriva, la riga si
riscrive e si segna `[verificato]` — anche, e soprattutto, quando la verifica smentisce
quello che c'era scritto qui.

---

## La domanda

> **Quanto vale un cliente che torna, e conviene di più trattenerlo o acquisirne uno
> nuovo?**

Non «Cohort Analysis», non «Customer Retention Dashboard». Il metodo non è il titolo.

Il committente immaginabile: chi decide il budget marketing di un negozio online.
La domanda ha senso solo se la risposta sposta dei soldi da una voce all'altra —
*quanto posso spendere per far tornare un cliente, prima che convenga andarne a
cercare uno nuovo.*

## Le sotto-domande

Sono cinque. Se un grafico non serve a una di queste, non entra.

1. **Di cento clienti nuovi di un mese, quanti comprano ancora dopo 1, 3, 6, 12 mesi.**
   Coorte = mese della prima fattura. La matrice mese-di-acquisizione x mesi-successivi
   è il cuore: senza, tutto il resto è una media che nasconde le differenze.

2. **Quanto spende in due anni chi torna, contro chi si ferma al primo ordine.**
   Non la media secca: la media **con l'intervallo di confidenza**. Su poche migliaia
   di clienti, e con una distribuzione di spesa quasi certamente storta a destra, la
   media da sola è un numero che sembra preciso e non lo è.
   `[verificato]` Lo era: media 1.990, mediana 1.091 fra chi torna. Si mostrano tutte
   e due. **E la finestra è un anno, non due:** per avere 24 mesi interi il primo
   ordine deve stare entro il 14 dicembre 2009, cioè solo la coorte esclusa al punto 1
   di `MODELLO.md`. Dodici mesi è la finestra più lunga che lasci clienti da
   misurare.

3. **Quanto tempo passa fra il primo e il secondo ordine, e dopo quanti giorni di
   silenzio un cliente non torna più.**
   È la sotto-domanda che produce la leva operativa: se esiste una soglia oltre la
   quale la probabilità di ritorno crolla, quella soglia è il momento in cui una
   riattivazione ha senso. Se non esiste, va detto che non esiste.

   `[verificato]` **Non esiste.** La probabilità cala in modo regolare e non crolla in
   nessun punto: entro 90 giorni è tornato il 60,9% di chi torna entro l'anno, entro 180 l'83,3%,
   e il resto torna dopo. Resta la mediana, 64 giorni, che è un momento ragionevole ma
   non una soglia.

4. **Il funnel di riacquisto: cento primi ordini, quanti arrivano al secondo, al terzo,
   al quarto.**
   Attenzione al nome, ed è una precisazione che va tenuta anche nella pagina
   pubblicata: **in dati transazionali non esiste un funnel di conversione.** Non ci
   sono sessioni, pagine viste, carrelli abbandonati. Quello che esiste è la
   sopravvivenza da un ordine al successivo. Chiamarlo «conversion funnel» sarebbe
   sbagliato, e chi legge se ne accorge.

5. **Il punto di pareggio: sotto quale spesa conviene trattenere.**
   È la riga che risponde alla domanda del titolo, e la forma della risposta è stata
   scelta apposta.

   La tentazione era rispondere «trattenere conviene più che acquisire». Non si può:
   questi dati non hanno il costo di acquisizione, e nemmeno i costi di prodotto. Ma il
   buco non si tappa dichiarandolo — **si chiude cambiando cosa si consegna**.

   Invece del verdetto, la soglia:

   > Riattivare un cliente conviene finché costa meno di **margine × ΔRicavo**, dove
   > ΔRicavo è il ricavo in più di un cliente portato al secondo ordine, misurato qui
   > con il suo intervallo.

   Chi decide mette il proprio margine e il proprio costo, e legge la risposta. È
   più utile di un verdetto, perché regge anche quando i loro numeri cambiano — e
   soprattutto è l'unica risposta che questi dati possono sostenere davvero.

   Due cose restano parametri dichiarati, non risultati: **il margine** (senza costo
   del venduto, quello che si misura è ricavo, non profitto) e **il costo dell'azione
   di riattivazione**. Vanno scritti come manopole, con un valore d'esempio, non
   nascosti in una formula.

---

## I dati

**Online Retail II** (UCI Machine Learning Repository, dataset 502). Negozio online
britannico, articoli da regalo, dicembre 2009 – dicembre 2011. 1.067.371 righe.

### Perché non Olist

Il progetto Power BI usa Olist, e la scelta ovvia sarebbe stata riusarlo. **Verificato
prima di decidere, e la verifica ha escluso l'ipotesi:**

| | Olist | Online Retail II |
|---|---|---|
| clienti che tornano | **3,06%** | **75,4%** |
| clienti distinti | 95.560 | 5.942 |
| periodo | 24 mesi | 24 mesi |

Su Olist il 96,9% dei clienti compra una volta sola. Una matrice di coorte su quei dati
sarebbe una tabella di zeri: vera, e inutile. La domanda di questo progetto non è
rispondibile con quei dati, e la cosa si scopre contando, non leggendo la
documentazione.

### Lo sporco, censito prima di cominciare

`[verificato]` sul file vero:

| | righe | quota |
|---|---|---|
| senza `Customer ID` | 243.007 | **22,8%** |
| fatture di storno (`C…`) | 19.494 | 1,8% |
| quantità negative | 22.950 | 2,2% |
| prezzo ≤ 0 | 6.207 | 0,6% |

Il 92% delle righe è Regno Unito. E fra i codici articolo ce ne sono che prodotti non
sono: `POST` e `DOT` (spedizione), `M` (rettifica manuale), `BANK CHARGES`, `ADJUST`,
`S` (campioni), `D` (sconto).

Ognuna di queste quattro righe è una decisione con una conseguenza, e va scritta in
`DATI-SPORCHI.md` con il conteggio prima e dopo:

- **Le righe senza Customer ID non possono entrare in un'analisi di coorte** — non si
  sa a chi appartengono. Escluderle è obbligato, ma allora il fatturato citato in
  questa analisi **non è il fatturato del negozio**, ed è un quinto in meno. Va detto
  ogni volta che si cita una cifra assoluta.
- **Storni e quantità negative**: nettarli dal valore del cliente o escluderli sono
  due scelte diverse, e cambiano quanto vale un cliente. Va scelto e motivato.
- **I codici non-prodotto**: `POST` in un carrello è spedizione, non un acquisto.
  Contarli gonfia il numero di articoli per ordine.
- **Il 92% britannico**: questa è l'analisi di un negozio del Regno Unito. Scrivere
  «e-commerce internazionale» sarebbe falso.

---

## Come si capisce se l'analisi è servita a qualcosa

Non da un grafico. Da una frase con dentro una cifra e il suo intervallo, del tipo:

> Un cliente portato al secondo ordine vale *N* volte uno che si ferma al primo
> (intervallo da *X* a *Y*). Il secondo ordine, quando arriva, arriva entro *N* giorni:
> oltre quella soglia la probabilità di ritorno scende a *Z*. Riattivare prima di quel
> giorno vale fino a *€ K* per cliente.

Se alla fine questa frase non si può scrivere con numeri veri, l'analisi non ha
risposto alla domanda, e la pagina lo dice invece di riempirsi di grafici.

---

## Il buco vero: chi torna è già diverso

Questo è il limite serio del progetto, e non è il costo di acquisizione — quello si
aggira col punto di pareggio. È un altro, e va affrontato in mezzo all'analisi, non
in fondo.

I clienti che tornano valgono di più di quelli che si fermano al primo ordine. Ma
**non sono le stesse persone**: chi torna aveva già, al primo acquisto, qualcosa di
diverso — un ordine più grande, un prodotto diverso, forse un'intenzione diversa.
Misurare che valgono tre volte tanto **non dimostra che portarne uno al secondo ordine
lo farebbe valere tre volte tanto.** La differenza fra le due frasi è la differenza
fra un'analisi che si può usare e una che fa perdere soldi.

Con questi dati la domanda non si chiude: servirebbe un esperimento, due gruppi e una
riattivazione mandata a uno solo. Si può però fare due cose, e si fanno:

1. **Restringere il confronto a clienti simili.** Non «chi torna contro chi non
   torna», ma clienti appaiati per dimensione del primo ordine, mese di ingresso e
   paese. Quello che resta della differenza è più credibile di quella grezza.
   `[verificato, poi corretto il 2 ottobre]` Il primo conto dava **da 1.653 a 1.374**
   (−17%), ma misurava la spesa degli stessi mesi che decidono chi torna: il confronto
   girava in tondo (`CHANGELOG.md`). Rifatto con il gruppo deciso nei primi 90 giorni e
   la spesa contata dopo: a parità di primo ordine il divario è **£756** (£548–£1.025).
   L'appaiamento è per decile di primo ordine e coorte (105 strati, il 95% dei
   clienti); il paese è rimasto fuori perché il 92% è Regno Unito e gli strati
   esteri sarebbero stati troppo piccoli per stare in piedi.

2. **Scrivere il verbo giusto.** «I clienti che tornano valgono N volte» è vero.
   «Farli tornare li fa valere N volte» non è dimostrato qui. La pagina usa il primo,
   sempre.

## Cosa questa analisi non potrà dire

Scritto adesso, non alla fine, così non diventa una giustificazione a posteriori.

- **Non dice se trattenere convenga più che acquisire**, perché manca il costo di
  acquisizione. Dice a quale prezzo le due cose si equivalgono. Vedi sotto-domanda 5.
- **Non misura profitto ma ricavo**, perché manca il costo del venduto. Il margine
  resta una manopola dichiarata.
- **Manca tutto quello che sta prima dell'acquisto**: nessuna sessione, nessuna
  campagna, nessun canale. Non si può dire *perché* un cliente è tornato, solo
  quanti sono tornati.
- **Il 22,8% dei dati resta fuori.**
- **Due anni sono pochi per un valore a 24 mesi**: le coorti dell'ultimo anno non hanno
  ancora avuto il tempo di maturare, e vanno lette per quello che sono — incomplete,
  non basse.
- **I dati sono del 2009-2011.** Le soglie che ne escono descrivono quel negozio in
  quegli anni. Il metodo si trasferisce, i numeri no.

---

## Com'è finita

Le risposte stanno in `RISULTATI.md`, ricontrollate una a una da `06_ricontrollo.py`
(63 controlli, rifatti dalle tabelle di base senza passare dalle viste).

Due cose sono andate diversamente da come erano scritte qui, e una non era prevista:

- **il valore a 24 mesi non si può misurare** — nessuna coorte utile ha 24 mesi;
- **la soglia di silenzio non esiste** — la probabilità di ritorno non crolla mai;
- **non previsto:** la retention di questo negozio è stagionale. Il mese del calendario,
  preso da solo, spiega il doppio della variazione rispetto all'età del cliente (34,8% contro 16,6%), e leggere la matrice come
  una curva di abbandono vuol dire leggere il Natale e chiamarlo fedeltà.

La frase che questo file chiedeva di poter scrivere alla fine, con numeri veri:

> Fra i clienti entrati nel 2010, chi torna entro 90 giorni spende dal giorno 91 al 365
> **£1.355 contro £432**. A parità di primo ordine il divario resta **£756**
> (£548–£1.025); a parità di spesa nei primi 90 giorni scende a **£150** (da −£67 a
> £374), e l'intervallo comprende lo zero: per prevedere la spesa futura basta quella
> iniziale. Il secondo ordine arriva a metà entro **64 giorni**, ma una soglia oltre la
> quale il cliente è perso non c'è. Quanto valga riattivarlo lo può dire solo un test
> con la riattivazione assegnata a caso.
>
> *Corretto il 2 ottobre 2026: la prima versione diceva 1.374 e un pareggio a margine × 1.125, poi ritirati (`CHANGELOG.md`).*
