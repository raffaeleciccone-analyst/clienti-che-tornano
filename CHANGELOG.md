# Correzioni dopo la pubblicazione

Ogni correzione dice cosa si leggeva prima, perché era sbagliato e cosa si legge adesso.
I numeri vecchi restano qui, non nel README.

---

## 2 ottobre 2026: il valore di chi torna girava in tondo

**Prima.** «Fra i clienti entrati nel 2010, chi arriva al secondo ordine spende nel primo
anno £1.990 contro £337. Appaiati per primo ordine e coorte il divario resta £1.374
(£1.125–£1.658). Riattivare conviene finché costa meno di margine × £1.125, cioè £225
con un margine del 20%.»

**Perché era sbagliato.** «Chi torna» era definito dagli ordini dei primi 365 giorni, e
la spesa confrontata era quella degli stessi 365 giorni: la differenza conteneva, per
costruzione, i soldi degli ordini che facevano contare il cliente come uno che torna.
L'ha notato una revisione fatta con l'IA.

**Adesso.** Il gruppo si decide nei primi 90 giorni, la spesa si conta dal giorno 91 al
365 (`valore_futuro.py`, ricontato a parte in `06_ricontrollo.py`). A parità di primo
ordine: £756 (£548–£1.025). A parità di spesa nei primi 90 giorni: £150 (da −£67 a
£374). La soglia di £225 è ritirata. Dettagli in `RISULTATI.md`, sezione 9.

**Nello stesso giro:**
- l'intervallo appaiato ricampiona i clienti dentro gli strati, non le differenze fra
  strati;
- nel testo il mese basso di riferimento è febbraio (12%, due anni di dati), non
  gennaio (11%, un anno solo);
- gli script cercavano la password del database in una cartella rinominata
  (`serie-a-index-engine`, ora `football-index-engine`);
- la correzione delle intestazioni della matrice esisteva solo nella pagina pubblicata e
  la rigenerazione l'avrebbe cancellata: ora sta nel modello della pagina.

### Il testo di testa del 27 agosto, com'era

> **Corretto il 2 ottobre 2026.** Il confronto qui sotto girava in tondo: «chi torna»
> era definito dagli ordini del primo anno, e la spesa confrontata era quella dello
> stesso anno, quindi conteneva gli ordini del ritorno. Rifatto tagliando il tempo in
> due (sezione 9): i primi 90 giorni decidono il gruppo, la spesa si conta dal giorno 91
> al 365. **A parità di primo ordine chi è tornato presto spende £756 in più nei nove
> mesi dopo; a parità di quanto aveva già comprato nei primi tre mesi, solo £150, con
> un intervallo che comprende lo zero. Conta il volume, non il ritorno in sé.** Cade la
> soglia di £225: riportare indietro un cliente piccolo non lo rende grande.
>
> Il testo che segue è quello del 27 agosto, lasciato com'era.


> Fra i clienti entrati nel 2010, chi arriva al secondo ordine spende nel suo primo
> anno **£1.990 contro £337** — sei volte tanto. Confrontando solo clienti che al primo
> acquisto erano uguali, il divario resta **£1.374** (intervallo £1.125–£1.658): **ne
> sopravvive l'83%.** Se un cliente riattivato si comportasse come chi torna da solo,
> riattivarlo converrebbe finché costa meno di **margine × £1.125**, cioè £225 con un
> margine del 20%. È un'ipotesi, non un risultato: vedi la sezione 8.
>
> **La soglia di silenzio oltre la quale il cliente è perso non esiste**: la
> probabilità di ritorno cala piano, senza mai crollare. Chi torna lo fa a metà entro
> due mesi, ma il 17% arriva dopo il sesto.
>
> **Su chi:** clienti **identificati**. Il 22,8% delle righe non ha un `Customer ID`, e
> quelle fatture restano fuori da ogni conteggio — vedi la sezione 7, che dice cosa
> questo cambia e cosa no.

E il risultato che non era in programma:

> **La retention di questo negozio non è una curva di abbandono, è un calendario.**
> Il mese dell'anno spiega il doppio dell'età del cliente (34,8% contro 16,6%).
> Novembre 25%, gennaio 11%. Leggere la matrice come una discesa vuol dire leggere il
> Natale e chiamarlo fedeltà.

---

### L'apertura del README del 27 agosto, com'era

**Corretto il 2 ottobre 2026.** La prima versione diceva che chi torna vale £1.374 in più
nel primo anno. Quel confronto girava in tondo: misurava la spesa dello stesso anno in cui
si decideva chi torna. Rifatto con il gruppo deciso nei primi 90 giorni e la spesa contata
dopo: **a parità di quanto il cliente aveva già comprato nei primi tre mesi, essere
tornato aggiunge solo £150 (intervallo da −£67 a £374). Conta il volume, non il ritorno.**
Dettagli in `RISULTATI.md`, sezione 9. Il paragrafo qui sotto è quello originale.

**Fra i clienti entrati nel 2010**, chi arriva al secondo ordine spende nel primo anno
**£1.990 contro £337**. Confrontando solo clienti che al primo acquisto erano uguali —
appaiati per decile di primo ordine e coorte — il divario resta **£1.374**
(£1.125–£1.658): ne sopravvive l'83%. È un'associazione, non un effetto: dice quanto
valgono i clienti che tornano, non quanto renderebbe farli tornare. **Se** un cliente
riattivato si comportasse come chi torna da solo, riattivarlo converrebbe finché costa
meno di **margine × £1.125**, cioè £225 con un margine del 20%. Quel «se» lo verifica
solo un test con la riattivazione assegnata a caso (`RISULTATI.md`, sezione 8).
