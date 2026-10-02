# Le risposte

Misurate il 27 agosto 2026 da `05_analisi.py`, sul database costruito in `MODELLO.md`.
Ogni cifra qui sotto esce da quello script: si rilancia e si ricontano.

Le cinque sotto-domande sono quelle di `DOMANDA.md`, nello stesso ordine. Due hanno
avuto una risposta diversa da quella che si aspettava, e stanno scritte cosi'.

---

## In una frase

> **La retention di questo negozio non e' una curva di abbandono, e' un calendario.**
> Il mese dell'anno spiega il doppio dell'eta' del cliente (34,8% contro 16,6%).
> Novembre 25%, febbraio 12%.
>
> **Chi torna presto spende di piu' anche dopo, ma lo prevede gia' quanto ha speso.**
> A parita' di primo ordine, chi e' tornato entro 90 giorni spende £756 in piu' nei
> nove mesi dopo; a parita' di spesa nei primi 90 giorni, £150 (da −£67 a £374).
> Lettura predittiva, non causale: sezione 9.
>
> **La soglia di silenzio oltre la quale il cliente e' perso non esiste**, e
> arrivare al secondo ordine non mette al sicuro.
>
> **Su chi:** clienti **identificati**. Il 22,8% delle righe non ha un `Customer ID`
> (sezione 7).

Le sezioni 6 e 8 sono la versione del 27 agosto, superata dalla sezione 9: restano
perche' si veda il ragionamento. Le correzioni stanno in `CHANGELOG.md`.

---

## 1. Di cento clienti nuovi, quanti tornano dopo 1, 3, 6, 12 mesi

**23 coorti utili** (gennaio 2010 – novembre 2011), **253 celle osservate**. La matrice
intera sta in `risultati/matrice_retention.csv`; qui le colonne che la domanda chiede,
dal panel bilanciato della sezione 3 — le stesse 11 coorti in ogni riga, cosi' che le
righe si possano confrontare fra loro.

| dopo | tornano |
|---|---:|
| 1 mese | 19,8% |
| 3 mesi | 21,5% |
| 6 mesi | 17,6% |
| 12 mesi | 17,9% |

**Non e' una discesa.** Sale fino al terzo mese, scende fino al decimo (13,1%), e
risale al dodicesimo. Il perche' e' la sezione 2, ed e' la ragione per cui questa
tabella da sola non risponde a niente.

Le celle che il calendario non ha ancora raggiunto **restano vuote, non a zero**.
`mesi_osservabili` conta solo i mesi finiti: dicembre 2011 e' lungo nove giorni e non
vale come mese.

---

## 2. La retention e' stagionale, non decrescente

Non era una delle cinque domande. E' venuta fuori guardando la prima colonna della
matrice — il mese +1 della coorte di gennaio 2010 e' **21,5%**, il mese +2 e' **32,1%**
— e una curva di abbandono non risale.

Ogni cella della matrice sta a due cose insieme: un mese di vita del cliente, e un mese
del calendario. Si puo' chiedere quale delle due la spiega.

| | quanta variazione spiega |
|---|---:|
| il mese di vita del cliente (+1, +2, +3…) | 16,6% |
| **il mese del calendario** (gennaio, febbraio…) | **34,8%** |
| tutti e due insieme | 85,8% |

Media della retention per mese del calendario, su tutte le coorti:

| gen | feb | mar | apr | mag | giu | lug | ago | set | ott | **nov** | dic |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 11,3% | 12,0% | 15,9% | 15,4% | 18,4% | 17,3% | 16,5% | 15,6% | 19,6% | 21,7% | **25,0%** | 13,8% |

Novembre vale piu' del doppio di gennaio, e il picco arriva **prima** di Natale, non
durante.

La lettura piu' naturale e' che molti di questi clienti non siano consumatori ma
negozi, che si riforniscono in autunno e poi stanno fermi: la stagione sarebbe del
compratore, non del venditore. I dati la sostengono — un ordine mediano vale £303 e ha
**15 righe per 153 pezzi**, e la scheda UCI del dataset dice che *molti* clienti sono
grossisti — ma non la dimostrano: il 6,2% degli ordini sta sotto £50, e quelli non sono
riassortimenti.

**Il picco di novembre e' un fatto; il perche' e' una lettura**, e vanno tenuti
separati. Quello che segue non dipende dal perche'.

> **Limite, dichiarato dove serve:** nella finestra dei dati c'e' **un dicembre solo**
> (2010) e **un gennaio solo** (2011). I due estremi della tabella sono anche i meno
> sostenuti. I mesi centrali hanno due anni a testa e reggono; sui due estremi si dice
> la direzione, non la cifra.

### Cosa cambia in pratica

**Due coorti non si confrontano se non hanno vissuto gli stessi mesi.** Chi entra a
ottobre ha il Natale davanti, chi entra a gennaio ha undici mesi di attesa. Una
classifica delle coorti per retention — il grafico che questo tipo di analisi produce
per primo — misurerebbe il mese di ingresso e lo chiamerebbe qualita' dei clienti.

E la coorte di dicembre 2010 lo mostra da sola: 76 clienti, **9% al mese +1**, contro
il 26% di ottobre. Non sono clienti peggiori. Sono persone che hanno comprato un
regalo.

---

## 3. Quanto scende davvero

Nella tabella per mese di vita ogni riga e' fatta di coorti diverse: al mese +12
arrivano solo le coorti vecchie. Rifatto sulle **11 coorti che hanno tutti i dodici
mesi** — sempre le stesse in ogni riga:

| +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 | +10 | +11 | +12 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 19,8 | 20,7 | 21,5 | 18,6 | 18,2 | 17,6 | 17,4 | 15,2 | 14,3 | **13,1** | 13,6 | 17,9 |

Lo scarto rispetto alla versione sbilanciata sta **sotto il punto percentuale** (−0,8
al mese +1, +0,0 al mese +12): il difetto c'era e non mordeva. E' un controllo passato,
non un problema risolto — ma andava fatto prima di saperlo.

La risalita al dodicesimo mese non e' un ritorno di fiamma: per una coorte del 2010 il
mese +12 e' **lo stesso mese del calendario un anno dopo**. E' la stagionalita' che
rientra dalla finestra.

---

## 4. Il funnel di riacquisto — e la risposta smentisce la Fase 2

Non e' un funnel di conversione: in dati transazionali non esistono sessioni ne'
carrelli abbandonati. E' la sopravvivenza da un ordine al successivo.

Sui **3.334 clienti** che hanno avuto 365 giorni interi davanti (vedi sezione 6):

| gradino | clienti | quota | sopravvive dal precedente |
|---|---:|---:|---:|
| 1º | 3.334 | 100% | |
| 2º | 2.373 | 71,2% | 71,2% |
| 3º | 1.715 | 51,4% | 72,3% |
| 4º | 1.249 | 37,5% | 72,8% |
| 5º | 905 | 27,1% | 72,5% |
| 6º | 657 | 19,7% | 72,6% |
| 7º | 488 | 14,6% | 74,3% |
| 8º | 371 | 11,1% | 76,0% |

**La colonna di destra non si muove: 72,3% a ogni gradino.**

`MODELLO.md` aveva registrato il contrario — 72%, poi 78%, 80%, 81%, cioe' una fedelta'
che cresce a ogni acquisto, e il primo salto come il piu' duro. Quel conto guardava
*tutta la vita* di ogni cliente, e le vite non sono lunghe uguali: chi e' entrato a
gennaio 2010 ha avuto due anni per arrivare all'ottavo ordine, chi e' entrato a
settembre 2011 ne ha avuti tre mesi. **La sopravvivenza che saliva era il tempo in piu'
di chi era arrivato in fondo.** A tempo fissato, la salita sparisce.

Quindi: **il processo non ha memoria.** Arrivare al secondo ordine non mette al sicuro.
«Portali al secondo acquisto e sono tuoi» qui e' falso.

### Una riscrittura, non una prova

Se la sopravvivenza e' davvero costante, il numero di ordini per cliente deve seguire
una geometrica con quel `p`:

| ordini | attesa | osservata |
|---|---:|---:|
| 1 | 27,7% | 28,8% |
| 2 | 20,0% | 19,7% |
| 3 | 14,5% | 14,0% |
| 4 | 10,5% | 10,3% |
| 5 | 7,6% | 7,4% |
| 6 | 5,5% | 5,1% |

Ordini medi per cliente: **3,61 attesi contro 3,81 osservati.**

> **Onesta' su cosa vale questa tabella.** Il `p` e' stimato dalle stesse sopravvivenze
> che il modello poi riproduce: non e' una verifica indipendente, e' lo stesso fatto
> scritto in un altro modo. Quello che aggiunge e' che **un modello a un solo parametro
> basta a ricostruire l'intera distribuzione** — non che il modello sia stato messo alla
> prova. Una prova vera richiederebbe di stimare `p` su una meta' dei clienti e
> controllarlo sull'altra.

Fino al sesto ordine lo scarto sta sotto il mezzo punto. Piu' in la' la sopravvivenza
sale davvero (74% → 77%): li' non e' piu' il tempo, sono i clienti — chi ha comprato
otto volte e' un negozio che si rifornisce, e non somiglia piu' agli altri.

---

## 5. Quanto tempo passa, e la soglia che non c'e'

Fra primo e secondo ordine, per i 2.373 che ci arrivano entro l'anno:

| percentile | giorni |
|---|---:|
| 25º | 26 |
| **50º** | **64** |
| 75º | 139 |
| 90º | 231 |

Letto come leva operativa — di **chi torna entro l'anno**, quanti sono gia' tornati entro:

| 30 gg | 60 gg | 90 gg | 120 gg | 180 gg |
|---:|---:|---:|---:|---:|
| 28,4% | 48,2% | 60,9% | 70,1% | 83,3% |

> **La sotto-domanda 3 chiedeva «dopo quanti giorni di silenzio un cliente non torna
> piu'». La risposta e' che quel giorno non esiste.** La curva cala in modo regolare e
> non ha un punto in cui la probabilita' crolla. A tre mesi sono tornati sei su dieci,
> a sei mesi otto su dieci, e il restante 17% torna dopo. Chi cercava una soglia netta
> qui non la trova, e dichiararne una vorrebbe dire inventarla.
>
> Quello che si puo' dire e' piu' modesto e ancora utile: **la mediana e' 64 giorni.**
> Una riattivazione mandata al secondo mese arriva quando meta' di chi tornera' entro
> l'anno non e' ancora tornato. Non e' una soglia, e' un momento ragionevole.
>
> **Attenzione al denominatore.** Queste percentuali sono condizionate a «torna entro
> 365 giorni», perche' la finestra taglia li': chi ha fatto il secondo ordine al giorno
> 400 qui risulta non tornato. Non sono percentuali di «chi tornera'» mai — quel
> denominatore, con due anni di dati, non e' osservabile per nessuno.

---

## 6. Quanto vale chi torna (versione del 27 agosto, superata dalla sezione 9)

### La finestra, prima del numero

Confrontare «quanto ha speso finora» fra un cliente entrato a gennaio 2010 e uno
entrato a ottobre 2011 non misura il cliente: misura quanto tempo ha avuto. Si guardano
i **primi 365 giorni di ciascuno**, e restano solo i clienti che quei giorni li hanno
avuti per intero.

| | clienti |
|---|---:|
| in tutto | 5.852 |
| meno le coorti 2009-12 e 2011-12 | −979 |
| meno chi non ha 365 giorni davanti | −1.539 |
| **nell'analisi del valore** | **3.334** |

> **La domanda chiedeva due anni. Non si puo'.** Per avere 24 mesi interi il primo
> ordine deve stare entro il 14 dicembre 2009: e' solo la coorte di dicembre 2009, che
> e' esclusa perche' non e' una coorte di clienti nuovi (`MODELLO.md`, punto 1).
> **Dodici mesi e' la finestra piu' lunga che lasci in piedi dei clienti da misurare.**
>
> E i 3.334 sono **tutte coorti del 2010**. Dopo la sezione 2 questo non e' un
> dettaglio: il gruppo non e' un campione di tutti i clienti, e' un campione di chi e'
> entrato nel 2010. Vale come confronto interno, non come ritratto della base.

### Il numero

| | clienti | media | mediana |
|---|---:|---:|---:|
| chi torna | 2.373 | **£1.990** | £1.091 |
| chi si ferma al primo ordine | 961 | **£337** | £229 |

**Media e mediana sono lontane**: la distribuzione ha una coda lunga e la media la
sente. Si mostrano tutte e due — la sotto-domanda 2 lo chiedeva, ed era una previsione
giusta.

**Differenza grezza: £1.653**, intervallo al 95% **£1.453 – £1.915**. Sei volte tanto.

L'intervallo viene da 2.000 ricampionamenti dei **clienti**, non degli ordini:
ricampionare gli ordini tratterebbe due acquisti dello stesso cliente come due
osservazioni indipendenti, e darebbe un intervallo troppo stretto.

### Fra clienti che partivano uguali

Chi torna era gia' diverso il primo giorno. Confronto ristretto a clienti appaiati per
**decile del primo ordine** e **coorte** — 105 strati, che coprono il 95% dei clienti:

| | differenza | intervallo 95% |
|---|---:|---|
| grezza | £1.653 | £1.453 – £1.915 |
| **appaiata** | **£1.374** | **£1.125 – £1.658** |

> **Quale intervallo e' questo.** Per la cifra appaiata ci sono due bootstrap possibili,
> e danno due larghezze diverse: ricampionare **gli strati** da' £1.129–£1.683 (ampiezza
> 554), ricampionare **i clienti dentro strati fermi** da' £1.186–£1.602 (ampiezza 416).
> Qui si pubblica il primo, che e' il piu' largo dei due. Non perche' sia piu' giusto —
> gli strati sono una griglia decisa da noi, non un campione — ma perche' fra due
> risposte difendibili si prende quella che promette meno.

`DOMANDA.md` chiedeva quanto si riduce il divario, «se si riduce di poco e' un conto,
se si dimezza e' un altro». **Si riduce del 17%: ne sopravvive l'83%.** Non si dimezza.
La dimensione del primo ordine spiega una fetta del divario, e non la fetta grossa.

### Da dove arrivano i soldi

Per cliente che torna, il maggior ricavo si divide cosi':

| | £ |
|---|---:|
| il secondo ordine | 348 |
| dal terzo in poi | 1.202 |

**Il secondo ordine porta solo il 22%.** E si incastra con la sezione 4: se la
sopravvivenza e' la stessa a ogni gradino, un cliente portato al secondo ordine non ha
comprato una volta in piu' — e' entrato in una fila dove ogni passo ha la stessa
probabilita' di averne un altro dietro. Quello che si compra riattivandolo non e' il
secondo ordine, **e' la coda che gli si apre dietro**, e li' stanno i quattro quinti
dei soldi.

---

## 7. Il limite piu' grosso, che non era stato applicato dove serviva

`DATI-SPORCHI.md` dichiara che il **22,8% delle righe non ha un `Customer ID`** — 8.752
fatture — e avverte che il fatturato citato non e' quello del negozio. Giusto. Ma quella
avvertenza era stata applicata **solo ai soldi**, e non alla cifra che apre tutto il
progetto: il 72,3% di clienti che tornano.

Quel 72,3% e' calcolato su chi ha un identificativo. Chi non ce l'ha e' fuori dal conto,
e non e' un pezzo neutro: se le fatture anonime fossero clienti occasionali, sarebbero
tutti «uno e basta».

| ipotesi sugli anonimi | clienti | tornano |
|---|---:|---:|
| sono gli stessi gia' contati (nessun cliente in piu') | 5.852 | **72,3%** |
| ogni fattura anonima e' un cliente diverso mai piu' tornato | 14.604 | **29,0%** |

**Il tasso di ritorno vero sta fra il 29% e il 72%**, e con questi dati non si stringe:
non c'e' modo di sapere chi sono gli anonimi.

C'e' anche una spinta nella direzione opposta, e va detta perche' non e' ovvia: se un
cliente identificato ha comprato **qualche volta anche senza farsi identificare**, i suoi
ordini anonimi non gli vengono attribuiti, e il suo numero di ordini risulta piu' basso
del vero. Quella parte fa **sottostimare** il ritorno. Le due distorsioni tirano da parti
opposte e non si compensano in modo calcolabile.

### Cosa cade e cosa resta

**Cade** ogni frase del tipo «tre clienti su quattro di questo negozio tornano». La
formulazione corretta e' **«tre clienti identificati su quattro tornano»**, ed e' cosi'
che va scritta anche nella pagina pubblicata.

**Resta in piedi tutto il resto**, e non e' un salvataggio: le altre conclusioni sono
confronti *interni* ai clienti identificati — chi torna contro chi non torna, novembre
contro gennaio, gradino contro gradino. Gli anonimi non entrano in nessuno dei due lati
del confronto, quindi non lo inclinano. Sposterebbero il livello di una percentuale, non
il segno di una differenza.

**E il confronto con Olist regge lo stesso.** In `DOMANDA.md` la scelta del dataset si
appoggia a 72,3% contro 3,1%. Olist non ha ordini anonimi, quindi i due denominatori non
sono la stessa cosa e il paragone e' generoso verso questo dataset. Anche prendendo
l'estremo pessimista — **29% contro 3,1%** — la conclusione non cambia: li' una matrice
di coorte sarebbe stata una tabella di zeri, qui no.

---

## 8. Il punto di pareggio (ritirato il 2 ottobre, vedi sezione 9)

Riattivare conviene finche' costa meno di **margine × £1.374**.

Il margine non sta nei dati — manca il costo del venduto, quindi qui si misura ricavo,
non profitto — e resta una manopola dichiarata.

| margine | soglia sulla stima | **soglia prudente** |
|---:|---:|---:|
| 10% | £137 | **£112** |
| 20% | £275 | **£225** |
| 30% | £412 | **£337** |
| 40% | £550 | **£450** |
| 50% | £687 | **£562** |

La colonna di destra usa il capo basso dell'intervallo: e' la soglia che regge **anche
se la stima e' ottimista**, ed e' quella da portare a una riunione.

### Cosa questo numero non dice

L'appaiamento toglie il pezzo di divario dovuto al fatto che certi clienti partivano
gia' piu' grossi. **Non toglie quello che non si e' misurato**: chi torna magari aveva
un bisogno ricorrente fin dall'inizio, e sarebbe tornato comunque.

Il conto vale **se** un cliente convinto a tornare poi si comporta come i clienti che
tornano da soli. E' un'ipotesi, non un risultato, e con dati osservativi non si
dimostra: servirebbe un test in cui la riattivazione viene assegnata a caso.

Per questo la pagina scrive sempre **«i clienti che tornano valgono N volte»** e mai
«farli tornare li fa valere N volte». Sono due frasi diverse, e la differenza fra loro
e' la differenza fra un'analisi che si puo' usare e una che fa perdere soldi.

---

## 9. Corretto il 2 ottobre 2026: il gruppo nei primi 90 giorni, la spesa dopo

Una revisione esterna ha notato che le sezioni 6 e 8 misuravano la propria definizione.
«Chi torna» voleva dire «piu' di un ordine nei primi 365 giorni», e la spesa confrontata
era quella degli stessi 365 giorni: la differenza conteneva, per costruzione, i soldi
degli ordini che facevano contare il cliente come uno che torna. L'appaiamento per primo
ordine non toglieva il cerchio.

Rifatto in `valore_futuro.py`, ricontato a parte in `06_ricontrollo.py`:

- i **primi 90 giorni** dal primo ordine decidono il gruppo (tornato o no);
- la spesa si misura **dal giorno 91 al 365**, e non contiene piu' gli ordini che
  definiscono il gruppo.

Stessi 3.334 clienti entrati nel 2010. Tornati entro 90 giorni: 1.446 (43,4%).

| spesa dal giorno 91 al 365 | media | mediana | compra ancora |
|---|---:|---:|---:|
| tornati entro 90 giorni | £1.355 | £554 | 77,2% |
| non tornati | £432 | £0 | 49,1% |

| confronto | differenza | intervallo 95% |
|---|---:|---:|
| grezzo | £922 | £674 – £1.257 |
| a parita' di primo ordine e coorte | £756 | £548 – £1.025 |
| **a parita' di spesa nei primi 90 giorni e coorte** | **£150** | **−£67 – £374** |

**Cosa dice.** Chi torna presto spende di piu' anche dopo, a parita' di partenza: questo
regge. Ma a parita' di quanto il cliente aveva gia' speso nei primi tre mesi, sapere che
ha fatto piu' di un ordine aggiunge £150 alla previsione, e l'intervallo comprende lo
zero. Per prevedere la spesa futura basta la spesa iniziale.

**Cosa non dice.** La spesa dei primi 90 giorni contiene gia' il secondo ordine:
appaiare su di lei toglie anche una parte del ritorno. Quindi e' una lettura
predittiva, non causale. Non dimostra che il ritorno «non conti»: dice che, come
segnale per chi deve scegliere su quali clienti investire, la spesa iniziale basta.

Gli intervalli ricampionano i clienti dentro ogni strato, 2.000 volte.

**Cosa cade.** La soglia della sezione 8 assumeva che un cliente riportato al secondo
ordine si comportasse come chi torna da solo. Questi numeri dicono che chi torna da solo
e' soprattutto chi spende gia' di piu', quindi quell'ipotesi non ha appoggio. La soglia
di £225 e' ritirata; la sezione 8 resta per mostrare cosa diceva.

**Cosa resta da fare, se ci fosse un committente.** La domanda giusta per la
riattivazione e' «quanto rende riattivare un cliente di questo volume», e si risponde
solo con un test: riattivazione assegnata a caso, a parita' di volume.

---

## Quello che e' cambiato rispetto a come era stato pianificato

| previsto in `DOMANDA.md` | com'e' andata |
|---|---|
| valore a 24 mesi | **impossibile**: nessuna coorte utile ha 24 mesi. Fatto a 12. |
| «la soglia di silenzio oltre cui non torna piu'» | **non esiste**: nessun crollo. Si riporta la mediana, 64 giorni. |
| mediana accanto alla media se la distribuzione e' storta | **lo era**: £1.990 contro £1.091. Fatto. |
| quanto si riduce il divario appaiando | **−17%**, non si dimezza |
| il primo salto e' il piu' duro (Fase 2) | **falso**: era il tempo di osservazione. La sopravvivenza e' costante al 72%. |
| — | **non previsto**: la retention e' stagionale, e il calendario spiega il doppio dell'eta' del cliente |

## E quello che ha trovato l'audit

`07_audit.py` non ricontrolla le cifre — lo fa `06_ricontrollo.py`. Attacca le
**decisioni**: le pulizie che potevano aver tolto troppo, i confronti che potevano
essere ancora sbilanciati, le interpretazioni che potevano non reggere. Nove controlli,
quattro cose da sistemare, tutte sistemate qui sopra:

| trovato | com'era | com'e' adesso |
|---|---|---|
| il 22,8% senza cliente non era mai stato applicato al tasso di ritorno | «il 72,3% torna» | «il 72,3% dei clienti **identificati** torna», con l'intervallo 29–72% — sezione 7 |
| i percentili del tempo sono tagliati a 365 giorni | «di chi tornera'» | «di chi torna **entro l'anno**» |
| la geometrica usa il `p` stimato dagli stessi dati | «il controllo» | «una riscrittura, non una prova» |
| per la cifra appaiata ci sono due bootstrap possibili | un intervallo senza dire quale | dichiarati tutti e due, pubblicato il piu' largo |

E cinque controlli passati, che vale la pena elencare perche' potevano andare male:

- **l'appaiamento e' bilanciato**: dentro ogni decile lo squilibrio residuo sul primo
  ordine e' −0,4% in media, e rifacendo il conto sulla spesa **dopo** il primo ordine la
  differenza viene £1.391 invece di £1.374 — l'1,2%, rumore;
- **la stagionalita' regge pesando le celle** per dimensione della coorte (33,5% contro
  15,6%), e regge **dentro** le coorti: il calo di dicembre si vede in **10 coorti su
  11**, quindi non e' un effetto di composizione;
- **il confronto sui gradi di liberta' e' sfavorevole al calendario**: «mese di vita» ha
  22 livelli contro 12, partiva avvantaggiato, e perde lo stesso;
- **la conclusione non dipende dalla finestra**: a 180, 270, 365 e 450 giorni la
  differenza appaiata vale £895, £1.134, £1.374, £1.581 — cresce come deve, e non cambia
  mai segno;
- **la deduplica non ha buttato righe legittime**: toglie il 2,2% del valore lordo, e le
  10 combinazioni fattura+articolo con orari diversi sopravvivono, perche' non sono copie.

### Il limite che l'audit ha confermato e nessuno puo' togliere

Eta' del cliente + coorte = mese del calendario, **per costruzione**. Con due anni di
dati le tre cose non si separano davvero. Quello che si puo' dire, e che si dice, e' che
**il calendario spiega piu' dell'eta'**. Non che l'eta' non conti.
