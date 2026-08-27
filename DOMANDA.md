# La domanda, scritta prima di aprire SQL

Finche' questo file non e' deciso, il database resta vuoto.

Le ipotesi da controllare sono marcate `[V]`. Quando la verifica arriva, la riga si
riscrive e si segna `[verificato]` — anche, e soprattutto, quando la verifica smentisce
quello che c'era scritto qui.

---

## La domanda

> **Quanto vale un cliente che torna, e conviene di piu' trattenerlo o acquisirne uno
> nuovo?**

Non «Cohort Analysis», non «Customer Retention Dashboard». Il metodo non e' il titolo.

Il committente immaginabile: chi decide il budget marketing di un negozio online.
La domanda ha senso solo se la risposta sposta dei soldi da una voce all'altra —
*quanto posso spendere per far tornare un cliente, prima che convenga andarne a
cercare uno nuovo.*

## Le sotto-domande

Sono cinque. Se un grafico non serve a una di queste, non entra.

1. **Di cento clienti nuovi di un mese, quanti comprano ancora dopo 1, 3, 6, 12 mesi.**
   Coorte = mese della prima fattura. La matrice mese-di-acquisizione x mesi-successivi
   e' il cuore: senza, tutto il resto e' una media che nasconde le differenze.

2. **Quanto spende in due anni chi torna, contro chi si ferma al primo ordine.**
   Non la media secca: la media **con l'intervallo di confidenza**. Su poche migliaia
   di clienti, e con una distribuzione di spesa quasi certamente storta a destra, la
   media da sola e' un numero che sembra preciso e non lo e'.
   `[verificato]` Lo era: media 1.990, mediana 1.091 fra chi torna. Si mostrano tutte
   e due. **E la finestra e' un anno, non due:** per avere 24 mesi interi il primo
   ordine deve stare entro il 14 dicembre 2009, cioe' solo la coorte esclusa al punto 1
   di `MODELLO.md`. Dodici mesi e' la finestra piu' lunga che lasci clienti da
   misurare.

3. **Quanto tempo passa fra il primo e il secondo ordine, e dopo quanti giorni di
   silenzio un cliente non torna piu'.**
   E' la sotto-domanda che produce la leva operativa: se esiste una soglia oltre la
   quale la probabilita' di ritorno crolla, quella soglia e' il momento in cui una
   riattivazione ha senso. Se non esiste, va detto che non esiste.

   `[verificato]` **Non esiste.** La probabilita' cala in modo regolare e non crolla in
   nessun punto: entro 90 giorni e' tornato il 60,9% di chi torna entro l'anno, entro 180 l'83,3%,
   e il resto torna dopo. Resta la mediana, 64 giorni, che e' un momento ragionevole ma
   non una soglia.

4. **Il funnel di riacquisto: cento primi ordini, quanti arrivano al secondo, al terzo,
   al quarto.**
   Attenzione al nome, ed e' una precisazione che va tenuta anche nella pagina
   pubblicata: **in dati transazionali non esiste un funnel di conversione.** Non ci
   sono sessioni, pagine viste, carrelli abbandonati. Quello che esiste e' la
   sopravvivenza da un ordine al successivo. Chiamarlo «conversion funnel» sarebbe
   sbagliato, e chi legge se ne accorge.

5. **Il punto di pareggio: sotto quale spesa conviene trattenere.**
   E' la riga che risponde alla domanda del titolo, e la forma della risposta e' stata
   scelta apposta.

   La tentazione era rispondere «trattenere conviene piu' che acquisire». Non si puo':
   questi dati non hanno il costo di acquisizione, e nemmeno i costi di prodotto. Ma il
   buco non si tappa dichiarandolo — **si chiude cambiando cosa si consegna**.

   Invece del verdetto, la soglia:

   > Riattivare un cliente conviene finche' costa meno di **margine × ΔRicavo**, dove
   > ΔRicavo e' il ricavo in piu' di un cliente portato al secondo ordine, misurato qui
   > con il suo intervallo.

   Chi decide mette il proprio margine e il proprio costo, e legge la risposta. E'
   piu' utile di un verdetto, perche' regge anche quando i loro numeri cambiano — e
   soprattutto e' l'unica risposta che questi dati possono sostenere davvero.

   Due cose restano parametri dichiarati, non risultati: **il margine** (senza costo
   del venduto, quello che si misura e' ricavo, non profitto) e **il costo dell'azione
   di riattivazione**. Vanno scritti come manopole, con un valore d'esempio, non
   nascosti in una formula.

---

## I dati

**Online Retail II** (UCI Machine Learning Repository, dataset 502). Negozio online
britannico, articoli da regalo, dicembre 2009 – dicembre 2011. 1.067.371 righe.

### Perche' non Olist

Il progetto Power BI usa Olist, e la scelta ovvia sarebbe stata riusarlo. **Verificato
prima di decidere, e la verifica ha escluso l'ipotesi:**

| | Olist | Online Retail II |
|---|---|---|
| clienti che tornano | **3,06%** | **75,4%** |
| clienti distinti | 95.560 | 5.942 |
| periodo | 24 mesi | 24 mesi |

Su Olist il 96,9% dei clienti compra una volta sola. Una matrice di coorte su quei dati
sarebbe una tabella di zeri: vera, e inutile. La domanda di questo progetto non e'
rispondibile con quei dati, e la cosa si scopre contando, non leggendo la
documentazione.

### Lo sporco, censito prima di cominciare

`[verificato]` sul file vero:

| | righe | quota |
|---|---|---|
| senza `Customer ID` | 243.007 | **22,8%** |
| fatture di storno (`C…`) | 19.494 | 1,8% |
| quantita' negative | 22.950 | 2,2% |
| prezzo ≤ 0 | 6.207 | 0,6% |

Il 92% delle righe e' Regno Unito. E fra i codici articolo ce ne sono che prodotti non
sono: `POST` e `DOT` (spedizione), `M` (rettifica manuale), `BANK CHARGES`, `ADJUST`,
`S` (campioni), `D` (sconto).

Ognuna di queste quattro righe e' una decisione con una conseguenza, e va scritta in
`DATI-SPORCHI.md` con il conteggio prima e dopo:

- **Le righe senza Customer ID non possono entrare in un'analisi di coorte** — non si
  sa a chi appartengono. Escluderle e' obbligato, ma allora il fatturato citato in
  questa analisi **non e' il fatturato del negozio**, ed e' un quinto in meno. Va detto
  ogni volta che si cita una cifra assoluta.
- **Storni e quantita' negative**: nettarli dal valore del cliente o escluderli sono
  due scelte diverse, e cambiano quanto vale un cliente. Va scelto e motivato.
- **I codici non-prodotto**: `POST` in un carrello e' spedizione, non un acquisto.
  Contarli gonfia il numero di articoli per ordine.
- **Il 92% britannico**: questa e' l'analisi di un negozio del Regno Unito. Scrivere
  «e-commerce internazionale» sarebbe falso.

---

## Come si capisce se l'analisi e' servita a qualcosa

Non da un grafico. Da una frase con dentro una cifra e il suo intervallo, del tipo:

> Un cliente portato al secondo ordine vale *N* volte uno che si ferma al primo
> (intervallo da *X* a *Y*). Il secondo ordine, quando arriva, arriva entro *N* giorni:
> oltre quella soglia la probabilita' di ritorno scende a *Z*. Riattivare prima di quel
> giorno vale fino a *€ K* per cliente.

Se alla fine questa frase non si puo' scrivere con numeri veri, l'analisi non ha
risposto alla domanda, e la pagina lo dice invece di riempirsi di grafici.

---

## Il buco vero: chi torna e' gia' diverso

Questo e' il limite serio del progetto, e non e' il costo di acquisizione — quello si
aggira col punto di pareggio. E' un altro, e va affrontato in mezzo all'analisi, non
in fondo.

I clienti che tornano valgono di piu' di quelli che si fermano al primo ordine. Ma
**non sono le stesse persone**: chi torna aveva gia', al primo acquisto, qualcosa di
diverso — un ordine piu' grande, un prodotto diverso, forse un'intenzione diversa.
Misurare che valgono tre volte tanto **non dimostra che portarne uno al secondo ordine
lo farebbe valere tre volte tanto.** La differenza fra le due frasi e' la differenza
fra un'analisi che si puo' usare e una che fa perdere soldi.

Con questi dati la domanda non si chiude: servirebbe un esperimento, due gruppi e una
riattivazione mandata a uno solo. Si puo' pero' fare due cose, e si fanno:

1. **Restringere il confronto a clienti simili.** Non «chi torna contro chi non
   torna», ma clienti appaiati per dimensione del primo ordine, mese di ingresso e
   paese. Quello che resta della differenza e' piu' credibile di quella grezza.
   `[verificato]` **Si riduce del 17%: da 1.653 a 1.374.** Non si dimezza. La
   dimensione del primo ordine spiega una fetta del divario, e non la fetta grossa.
   L'appaiamento e' per decile di primo ordine e coorte (105 strati, il 95% dei
   clienti); il paese e' rimasto fuori perche' il 92% e' Regno Unito e gli strati
   esteri sarebbero stati troppo piccoli per stare in piedi.

2. **Scrivere il verbo giusto.** «I clienti che tornano valgono N volte» e' vero.
   «Farli tornare li fa valere N volte» non e' dimostrato qui. La pagina usa il primo,
   sempre.

## Cosa questa analisi non potra' dire

Scritto adesso, non alla fine, cosi' non diventa una giustificazione a posteriori.

- **Non dice se trattenere convenga piu' che acquisire**, perche' manca il costo di
  acquisizione. Dice a quale prezzo le due cose si equivalgono. Vedi sotto-domanda 5.
- **Non misura profitto ma ricavo**, perche' manca il costo del venduto. Il margine
  resta una manopola dichiarata.
- **Manca tutto quello che sta prima dell'acquisto**: nessuna sessione, nessuna
  campagna, nessun canale. Non si puo' dire *perche'* un cliente e' tornato, solo
  quanti sono tornati.
- **Il 22,8% dei dati resta fuori.**
- **Due anni sono pochi per un valore a 24 mesi**: le coorti dell'ultimo anno non hanno
  ancora avuto il tempo di maturare, e vanno lette per quello che sono — incomplete,
  non basse.
- **I dati sono del 2009-2011.** Le soglie che ne escono descrivono quel negozio in
  quegli anni. Il metodo si trasferisce, i numeri no.

---

## Com'e' finita

Le risposte stanno in `RISULTATI.md`, ricontrollate una a una da `06_ricontrollo.py`
(63 controlli, rifatti dalle tabelle di base senza passare dalle viste).

Due cose sono andate diversamente da come erano scritte qui, e una non era prevista:

- **il valore a 24 mesi non si puo' misurare** — nessuna coorte utile ha 24 mesi;
- **la soglia di silenzio non esiste** — la probabilita' di ritorno non crolla mai;
- **non previsto:** la retention di questo negozio e' stagionale. Il mese del calendario
  spiega il doppio dell'eta' del cliente (34,8% contro 16,6%), e leggere la matrice come
  una curva di abbandono vuol dire leggere il Natale e chiamarlo fedelta'.

La frase che questo file chiedeva di poter scrivere alla fine, con numeri veri:

> I clienti che arrivano al secondo ordine spendono nel primo anno **1.990 contro 337**.
> Fra clienti che al primo acquisto erano uguali il divario resta **1.374**
> (1.125–1.658). Il secondo ordine arriva a meta' entro **64 giorni**, ma una soglia
> oltre la quale il cliente e' perso non c'e'. Riattivare vale fino a **margine ×
> 1.125**: 225 con un margine del 20%.
