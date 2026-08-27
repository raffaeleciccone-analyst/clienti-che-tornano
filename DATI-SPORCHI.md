# Cosa e' rotto nei dati, e cosa se ne fa

Contato il 27 agosto 2026 leggendo `dati_grezzi/online_retail_II.xlsx` senza
modificarlo. I numeri qui sotto li produce `01_censimento.py`: se il dataset viene
riscaricato, si rilancia e si ricontano.

Il file grezzo resta come e' arrivato. Ogni decisione elencata qui diventa un passaggio
con un nome nello script di caricamento, e i nomi sono quelli in grassetto.

**Il punto di questo documento non e' che i dati erano sporchi.** E' che ogni pulizia
toglie qualcosa, e chi legge un numero alla fine ha diritto di sapere cosa e' stato
tolto per produrlo.

---

## Il file com'e' arrivato

| | |
|---|---:|
| righe | 1.067.371 |
| fatture distinte | 53.628 |
| clienti con identificativo | 5.942 |
| codici articolo | 5.305 |
| periodo | 2009-12-01 → 2011-12-09 |

Due fogli: `Year 2009-2010` (525.461 righe) e `Year 2010-2011` (541.910).

Il file sta nel repo, in `dati_grezzi/`, **esattamente come e' arrivato da UCI** —
45.622.278 byte, `sha256:bcbe73b3…2df2e980`. Chi lo riscarica puo' controllare di avere
lo stesso file prima di stupirsi che i conti non tornino.

**Va tenuto in due fogli, e non e' un dettaglio di formato.** Il §1 qui sotto — la
sovrapposizione fra le due annate, che e' il difetto piu' grosso del dataset — si puo'
contare solo sapendo da quale foglio viene ogni riga. Incollandoli in un CSV unico quel
conto non e' piu' rifacibile, e resterebbe solo la nostra parola.

---

## 1. I due fogli si sovrappongono (1.067.371 → 1.033.034)

**Il problema che si nota per ultimo e che sporca tutto il resto.** I due fogli non
sono due periodi separati: **1.088 fatture stanno in tutti e due**, per 45.046 righe,
il 4,2% del file. Incollarli uno sotto l'altro conta due volte dicembre 2010.

Non e' un dettaglio contabile: una fattura contata due volte diventa un cliente che ha
ordinato due volte. Su un'analisi che misura *quante volte un cliente torna*, questo
difetto spinge il risultato esattamente nella direzione che si spera di trovare.

Le righe identiche in tutto sono 34.337 (3,2%), e **tutte e 45.046 le righe delle
fatture in comune sono duplicati esatti**: la sovrapposizione e' una riesportazione
pulita, non due versioni discordanti della stessa fattura. Controllato apposta, perche'
se i due fogli avessero avuto valori diversi per la stessa riga la deduplica avrebbe
dovuto scegliere quale tenere.

**Ma i duplicati non vengono tutti da li'.** Dei gruppi di righe ripetute, 22.202
stanno a cavallo dei due fogli e **10.707 sono interni a un foglio solo**: righe
identiche ripetute dentro la stessa annata. Sono due difetti diversi che lo stesso
passaggio risolve, e vale la pena saperlo — se un giorno arriva un file di un anno
solo, il problema c'e' lo stesso.

**Passaggio: `Togli le righe duplicate` — per fattura, articolo, quantita', data,
prezzo e cliente.** Va fatto per primo: finche' le copie sono dentro, ogni conteggio a
valle e' gonfiato senza dirlo.

### Nota sul tipo della colonna

`Invoice` arriva con due tipi diversi: **1.047.871 numeri interi e 19.500 stringhe**.
Le stringhe sono gli storni, che cominciano per `C`. Basta un confronto o una join per
inciamparci, e l'errore non da' errore: da' meno righe. Si converte tutto a testo in
lettura.

## 2. Il 22,8% delle righe non ha un cliente (1.033.034 → 797.883)

243.007 righe senza `Customer ID`, su 8.752 fatture. Sono vendite reali — hanno
articolo, quantita' e prezzo — ma non si sa a chi appartengono.

**Per un'analisi di coorte non c'e' scelta: senza cliente non esiste un «primo
ordine», e la riga non puo' entrare.** La conseguenza va detta ogni volta che si cita
una cifra assoluta:

| | |
|---|---:|
| ricavo del file intero | 19.287.251 |
| ricavo delle righe senza cliente | 2.638.958 |
| **quota di ricavo che esce** | **13,7%** |

Il 22,8% delle righe vale il 13,7% del ricavo: **gli ordini senza cliente sono piu'
piccoli della media.** Non e' un caso da ignorare — se fossero stati ordini grandi,
escluderli avrebbe distorto l'analisi molto di piu'.

**Passaggio: `Tieni solo le righe con cliente`.**

## 3. Storni e quantita' negative (797.883 → 779.493)

| | righe |
|---|---:|
| fatture di storno (`C…`) | 19.494 |
| quantita' negative | 22.950 |
| negative **fuori** dagli storni | 3.457 |
| storni con quantita' positiva | 1 |

Il valore degli storni e' **−1.526.668**, il 7,9% del ricavo lordo.

Le 3.457 negative fuori dagli storni non sono resi: hanno descrizioni come `check`,
`damages`, `damaged`, `?`. Sono rettifiche di magazzino. **Verificato: sono tutte e
3.457 su righe senza cliente**, quindi escono gia' col passaggio 2 — ma andavano
guardate, perche' se anche una sola avesse avuto un cliente sarebbe entrata
nell'analisi come un acquisto negativo.

**La decisione, e non e' ovvia.** Uno storno si puo' nettare dal valore del cliente
(chi rende merce vale meno) oppure escludere (l'acquisto c'e' stato lo stesso). Le due
strade danno due valori diversi per lo stesso cliente.

**Si esclude, e il motivo e' la domanda.** Qui si misura *se un cliente torna*, non
quanto margine lascia. Un reso non cancella la visita: chi ha comprato ed e' tornato a
rendere e' comunque un cliente che e' tornato. Nettare gli storni farebbe scendere il
valore di chi ha reso, mescolando due cose diverse — la frequenza e la soddisfazione.

**Passaggio: `Togli le fatture di storno`.** Il valore stornato resta scritto qui, e
va citato quando si parla di ricavo.

## 4. Prezzi non positivi (779.493 → 779.423)

- **6.202 righe a prezzo zero**, di cui solo 71 con cliente noto: sono in larghissima
  parte campioni e rettifiche gia' escluse al passaggio 2.
- **5 righe a prezzo negativo**, tutte con codice `B` e descrizione **`Adjust bad
  debt`**: fino a −53.594 in una riga sola. Sono crediti inesigibili, cioe' scritture
  contabili. Un credito inesigibile non e' un acquisto.

**Passaggio: `Togli i prezzi non positivi` (70 righe residue).**

## 5. Codici che non sono prodotti (779.423 → 776.575)

Fra i 5.305 codici articolo ce ne sono che prodotti non sono:

| codice | righe | cos'e' |
|---|---:|---|
| `POST` | 2.122 | spedizione |
| `DOT` | 1.446 | spedizione dotcom |
| `M` | 1.421 | rettifica manuale |
| `C2` | 282 | trasporto |
| `D` | 177 | sconto |
| `S` | 104 | campioni |
| `BANK CHARGES` | 102 | commissione bancaria |
| `ADJUST` | 67 | rettifica («Adjustment by john on 26/01/2010») |
| `AMAZONFEE` | 43 | commissione Amazon |
| `gift_0001_*` | 100 | buoni regalo |

`POST` in un carrello e' spedizione, non un articolo comprato: contarlo gonfia il
numero di articoli per ordine e altera il valore medio dello scontrino.

Il loro valore complessivo e' **negativo (−96.456)**, perche' fra gli storni ci sono
molte spedizioni rimborsate.

**Attenzione a non fidarsi della regola.** «Il codice non comincia con cinque cifre»
prende anche `DCGS0058` (*MISO PRETTY GUM*), `DCGSSGIRL`, `DCGSSBOY`: quelli sono
prodotti veri con una sigla diversa. L'elenco dei non-prodotti e' scritto a mano dopo
averli guardati, non dedotto da un'espressione regolare.

**Passaggio: `Togli i codici non-prodotto` (2.848 righe).**

## 6. Valori fuori scala — che vanno tenuti

| | quantita' | prezzo |
|---|---:|---:|
| minimo | −80.995 | −53.594,36 |
| mediana | 3 | 2,10 |
| 99,9° percentile | 500 | 217,02 |
| massimo | 80.995 | 38.970,00 |

Il massimo e il minimo della quantita' sono lo stesso numero con il segno opposto:
80.995 pezzi di `PAPER CRAFT , LITTLE BIRDIE` comprati e poi stornati per intero. Lo
storno esce al passaggio 3, **l'acquisto resta**.

**Non si toglie.** E' un ordine vero di un cliente vero, e togliere le code perche'
sono grandi e' il modo piu' rapido di far dire a una media quello che si vuole. Se
sposta i risultati, si mostra il risultato con e senza, e si dice di quanto sposta.

## 7. Descrizioni mancanti

4.382 righe senza descrizione, **tutte e 4.382 anche senza cliente**. Escono al
passaggio 2. Nessun passaggio dedicato.

## 8. Paesi: 43, ma quattro non sono paesi

| | righe | |
|---|---:|---|
| United Kingdom | 981.330 | **91,9%** |
| EIRE | 17.866 | 1,7% |
| Germany | 17.624 | 1,7% |
| France | 14.330 | 1,3% |

Quattro etichette non sono paesi: `Unspecified`, `European Community`,
`Channel Islands`, `RSA`.

**Non si filtra per paese**, ma si dichiara: **questa e' l'analisi di un negozio
britannico.** Scrivere «e-commerce internazionale» sarebbe falso, e un 8% di righe
estere non basta a dire niente sui mercati esteri.

---

## Cosa resta

| passaggio | righe | tolte |
|---|---:|---:|
| il file com'e' | 1.067.371 | |
| 1 — via i duplicati | 1.033.034 | −34.337 |
| 2 — via le righe senza cliente | 797.883 | −235.151 |
| 3 — via gli storni | 779.493 | −18.390 |
| 4 — via i prezzi non positivi | 779.423 | −70 |
| 5 — via i codici non-prodotto | **776.575** | −2.848 |

| | |
|---|---:|
| righe che restano | 776.575 (**72,8%**) |
| clienti | 5.852 |
| fatture | 36.594 |
| ricavo | 17.068.016 |

**Rispetto a quale ricavo, pero'.** Il totale del file grezzo e' 19.287.251, ma quella
cifra contiene le righe duplicate: e' gonfiata dallo stesso difetto che il passaggio 1
corregge. Il paragone onesto e' contro il lordo *deduplicato*.

| denominatore | quota che resta | quota persa |
|---|---:|---:|
| lordo cosi' com'e' (con le copie) | 88,5% | 11,5% |
| **lordo deduplicato** | **90,5%** | **9,5%** |

**Il 27,2% delle righe esce, ma solo il 9,5% del ricavo.** Quello che si toglie e'
piccolo, e questo e' l'unico motivo per cui le pulizie qui sopra non riscrivono la
risposta.

---

## E la domanda regge

Il controllo che valeva la pena fare per primo, perche' se falliva il progetto non
esisteva:

| | |
|---|---:|
| clienti | 5.852 |
| **clienti con piu' di un ordine** | **4.234 (72,3%)** |
| un ordine solo | 1.618 (27,7%) |
| due | 945 (16,2%) |
| tre | 659 (11,3%) |

> ⚠️ **Questo 72,3% e' fra i clienti IDENTIFICATI.** Le 8.752 fatture senza
> `Customer ID` del §2 non entrano nel conto, e se fossero clienti occasionali sarebbero
> tutti «uno e basta»: il tasso vero sta **fra il 29% e il 72%**. La stessa avvertenza
> del §2 vale qui, non solo sul fatturato — ci era sfuggito, e l'ha trovato
> `07_audit.py`. Il ragionamento completo sta nella sezione 7 di `RISULTATI.md`.

Per confronto, su Olist — il dataset dell'altro progetto — chi torna e' il **3,1%**.
Olist non ha ordini anonimi, quindi i due denominatori non sono la stessa cosa e il
paragone e' generoso verso questo dataset. Anche al 29%, pero', la conclusione tiene: la
stessa analisi su Olist avrebbe prodotto una tabella di zeri.
