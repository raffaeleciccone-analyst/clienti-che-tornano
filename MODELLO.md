# Il modello, e le tre trappole della finestra di osservazione

Costruito il 27 agosto 2026. Lo schema sta in `03_schema.sql`, il caricamento in
`04_carica.py`. Database: `retail_clienti` su MySQL 8.

---

## La grana, dichiarata prima delle `CREATE`

| tabella | una riga è | righe |
|---|---|---:|
| `fatto_riga` | una riga di fattura (fattura × articolo) | 776.575 |
| `fatto_ordine` | una fattura | 36.594 |
| `dim_cliente` | un cliente | 5.852 |
| `dim_articolo` | un codice articolo | 4.619 |
| `dim_data` | un giorno del periodo, buchi compresi | 739 |

### Perché uno schema a stella, e cosa c'era prima

La prima versione era un modello transazionale che ricalcava la sorgente: `clienti`,
`ordini`, `righe`. Funzionava — tutti i numeri di `RISULTATI.md` sono usciti da lì — e
aveva **tre difetti che si vedono solo provando a chiamarlo con il suo nome**:

1. **`clienti` conteneva `n_ordini` e `ricavo_totale`.** Sono misure dentro una tabella
   di dimensione: derivate dai fatti, e libere di andare fuori sincrono senza che
   nessuno se ne accorga. Al momento del cambio coincidevano ancora, ma niente lo
   garantiva.
2. **La descrizione dell'articolo stava ripetuta su 776.575 righe** — 19,8 MB di testo
   per 5.254 valori diversi. E **622 codici avevano più di una descrizione**, una cosa
   che nessuno era mai stato costretto a decidere finché non è esistita una
   dimensione a cui serviva una riga sola per codice.
3. **Anno, mese e trimestre venivano ricalcolati con funzioni in ogni query** invece di
   stare scritti una volta sola.

Il modello nuovo separa i fatti dalle dimensioni, e tiene la fattura come **dimensione
degenere** — resta una colonna dentro i fatti, perché non ha attributi propri e una
`dim_fattura` fatta di una chiave e nient'altro non servirebbe a niente.

`fatto_ordine` è un **aggregato dichiarato** alla grana della fattura, e non è lo
stesso difetto del punto 1: è un oggetto con un nome, una grana scritta e un momento
in cui viene ricostruito. `04_carica.py` lo riscrive da `fatto_riga` e poi controlla che
le due quadrino, uscendo con errore se non lo fanno. Delle misure nascoste dentro una
dimensione non se ne accorge nessuno.

`dim_cliente` tiene `primo_ordine` e `coorte`, che sono pur sempre derivati dai fatti.
La differenza con `n_ordini` non è un cavillo: **la coorte è un attributo su cui si
raggruppa, non una quantità che si somma**, e non cambia mai più una volta che il
cliente è entrato.

> **La prova che il cambio è corretto: nessun numero si è mosso.** Dopo la
> ristrutturazione `06_ricontrollo.py` passa gli stessi 63 controlli con gli stessi
> valori, e `07_audit.py` resta a zero allarmi. Un modello si può rifare; i risultati
> no, se non c'era un errore — e qui non c'era.

**«Ordine» e «fattura» qui sono la stessa cosa.** Il dataset non ha un concetto di
ordine separato dalla fattura, e inventarne uno — per esempio unendo due fatture dello
stesso giorno — vorrebbe dire decidere a tavolino una cosa che i dati non dicono. Si usa
quello che c'è e lo si chiama col suo nome.

Il caricamento ripete i passaggi di `DATI-SPORCHI.md` con gli stessi nomi e stampa
quante righe toglie ognuno. Se un giorno i due documenti non coincidono più, se ne
accorge chi lancia lo script.

Controlli dopo il caricamento, tutti passati: nessun ordine orfano, nessuna riga
orfana, e la somma dei valori d'ordine quadra con la somma delle righe
(17.068.016,12 da tutte e due le parti).

---

## Le viste

| vista | risponde a |
|---|---|
| `v_ordini_sequenza` | ogni ordine col suo posto nella storia del cliente |
| `v_coorte_mese` | quanti clienti entrano ogni mese |
| `v_retention_coorte` | la matrice coorte × mesi successivi |
| `v_funnel_riacquisto` | quanti arrivano al secondo ordine, al terzo… |

Il lavoro lo fanno le funzioni finestra: `ROW_NUMBER` per il numero d'ordine, `LAG`
per i giorni dal precedente, `MIN(...) OVER` per la data del primo ordine. Restano nel
database e non in pandas, così chi legge la query vede la definizione insieme al
risultato.

### Una correzione, `migrazioni/2026-08-27_mese_relativo.sql`

La prima versione contava il mese di coorte con `TIMESTAMPDIFF(MONTH, ...)`, che conta
i **mesi interi passati**, non la distanza fra due caselle del calendario:

```
TIMESTAMPDIFF(MONTH, '2010-01-20', '2010-02-03')  ->  0
distanza fra caselle                              ->  1
```

Un cliente entrato il 20 gennaio che ricompra il 3 febbraio finiva nel mese 0 della sua
coorte, **insieme al suo primo acquisto**. Succede a **10.257 ordini su 36.594: il
28%.** «Mese di coorte» vuol dire distanza fra caselle: chi entra a gennaio e compra a
febbraio è al mese 1, e il giorno del mese non c'entra.

Nella stessa migrazione cambia anche `mesi_osservabili`, che contava dicembre 2011 come
un mese osservato pur essendo lungo nove giorni. Ora conta **solo i mesi finiti**.

Le definizioni corrette stanno anche in `03_schema.sql`: se restassero solo nella
migrazione, una ricarica rimetterebbe dentro il difetto.

---

## Le tre trappole della finestra di osservazione

Guardando la prima colonna della matrice si vede subito qualcosa che non torna, e
sono tre problemi diversi. **Nessuno dei tre è un difetto dei dati: sono difetti del
modo di guardarli**, e vanno risolti prima di ricavarne una conclusione.

### 1. Dicembre 2009 non è una coorte di clienti nuovi

| coorte | clienti entrati |
|---|---:|
| **2009-12** | **951** |
| 2010-01 | 368 |
| 2010-02 | 375 |
| media feb–nov 2010 | 292 |

Dicembre 2009 è **3,2 volte** la media dei mesi successivi. Non è un mese di
acquisizione straordinario: è il **primo mese del file**. Chiunque fosse già cliente
del negozio compare lì per la prima volta, e viene registrato come «nuovo».

E si vede anche nel comportamento: quella coorte torna al mese +1 nel **37,6%** dei
casi, contro il 29,4% di gennaio e il 23,5% di febbraio. Ovvio: dentro ci sono clienti
affezionati da anni, mescolati ai nuovi veri.

**Se restasse dentro, alzerebbe la retention media di tutto il progetto — nella
direzione che fa comodo.**

**Decisione: la coorte 2009-12 esce dall'analisi delle coorti.** Resta nel database,
perché i suoi ordini sono ordini veri e contano per il fatturato; esce dai conti sul
ritorno, dove sarebbe una risposta a una domanda diversa.

### 2. Dicembre 2011 è mezzo mese

I dati finiscono il **9 dicembre 2011**. La coorte 2011-12 ha 28 clienti perché il
mese è lungo nove giorni.

**Decisione: la coorte 2011-12 esce.** Restano **23 coorti utili, da gennaio 2010 a
novembre 2011**.

### 3. Le coorti si rimpiccioliscono da sole

| | clienti nuovi al mese |
|---|---:|
| 2010, feb–nov | 292 |
| 2011, feb–nov | **144** |

Sembra un'azienda che dimezza l'acquisizione. **Può anche non esserlo.** Un cliente
entra in una coorte una volta sola: chi ha comprato nel 2010 non può essere «nuovo»
nel 2011. Più la finestra va avanti, più si restringe il bacino di chi non è ancora
mai comparso, e il numero di nuovi cala **per costruzione**.

Le due spiegazioni — meno acquisizione vera, oppure artefatto della finestra —
**con questi dati non si distinguono.** Servirebbe sapere chi era già cliente prima
di dicembre 2009, e non si sa.

**Decisione: non si commenta l'andamento dell'acquisizione.** Non è una domanda a cui
questo dataset può rispondere, e una riga in discesa che sembra un calo di vendite è
esattamente il tipo di grafico che fa prendere decisioni sbagliate.

### E una quarta, già scritta nella vista

Le coorti recenti hanno meno mesi di vita: la colonna `mesi_osservabili` in
`v_retention_coorte` dice quanti ne sono passati davvero. Un valore basso a +12 per una
coorte di novembre 2011 non vuol dire clienti peggiori, vuol dire che **il dodicesimo
mese non è ancora arrivato**. Le celle senza abbastanza osservazione restano vuote,
non a zero.

---

## Quello che si vede già

Il funnel di riacquisto, sull'intera base (le esclusioni qui sopra valgono per le
coorti, non per questo conteggio):

| gradino | clienti | quota | giorni dal precedente |
|---|---:|---:|---:|
| 1º ordine | 5.852 | 100% | — |
| 2º | 4.234 | **72,3%** | 99,0 |
| 3º | 3.289 | 56,2% | 83,7 |
| 4º | 2.630 | 44,9% | 73,4 |
| 5º | 2.141 | 36,6% | 66,0 |
| 6º | 1.786 | 30,5% | 57,4 |
| 8º | 1.290 | 22,0% | 49,5 |

Letta così, sembra che **il salto più grande sia il primo**: si perde il 27,7% fra
primo e secondo ordine, e poi solo il 22%, il 20%, il 19%. Sembra una fedeltà che
cresce a ogni acquisto.

> ⚠️ **Non è vero, ed è la quarta trappola della finestra.** Questa tabella guarda
> *tutta la vita* di ogni cliente, e le vite non sono lunghe uguali: chi è entrato a
> gennaio 2010 ha avuto due anni per arrivare all'ottavo ordine, chi è entrato a
> settembre 2011 ne ha avuti tre. La sopravvivenza che sale è il tempo in più di chi
> è arrivato in fondo.
>
> A tempo fissato — primi 365 giorni, solo per chi quei giorni li ha avuti — **la
> salita sparisce: si sopravvive al 72% a ogni gradino, sempre lo stesso.** Il conto
> sta nella sezione 5 di `RISULTATI.md`.
>
> Resta scritto qui invece di essere cancellato perché è esattamente lo stesso errore
> dei tre punti qui sopra, in un posto dove non lo si cercava.

Regge invece l'altro fatto: il tempo fra un ordine e l'altro **si accorcia mano a
mano**, 99 giorni per arrivare al secondo e 50 per arrivare all'ottavo.
