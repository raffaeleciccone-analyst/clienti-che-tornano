-- ============================================================================
--  Il modello: uno schema a stella
-- ============================================================================
--
--  La prima versione di questo file era un modello transazionale che ricalcava
--  la sorgente — clienti, ordini, righe. Funzionava, e aveva tre difetti che si
--  vedono solo se si prova a chiamarlo con il suo nome:
--
--    1. `clienti` conteneva n_ordini e ricavo_totale. Sono MISURE dentro una
--       tabella di DIMENSIONE: derivate dai fatti, e libere di andare fuori
--       sincrono senza che nessuno se ne accorga.
--    2. La descrizione dell'articolo stava ripetuta su 776.575 righe — 19,8 MB
--       di testo per 5.254 valori diversi. E 622 codici avevano più di una
--       descrizione, cosa che nessuno era mai stato costretto a decidere.
--    3. Anno, mese e trimestre venivano ricalcolati con funzioni in ogni query
--       invece di stare scritti una volta sola.
--
--  Qui i fatti stanno nelle tabelle dei fatti e gli attributi nelle dimensioni.
--
--  ── LA GRANA, dichiarata prima delle CREATE ────────────────────────────────
--
--    fatto_riga     una riga di fattura (fattura x articolo)   776.575
--    fatto_ordine   una fattura                                 36.594
--    dim_cliente    un cliente                                   5.852
--    dim_articolo   un codice articolo                           4.619
--    dim_data       un giorno del periodo (buchi compresi)         739
--
--  «Ordine» e «fattura» restano la stessa cosa: il dataset non ha un concetto
--  di ordine separato dalla fattura, e inventarne uno vorrebbe dire decidere a
--  tavolino che due fatture dello stesso giorno sono un ordine solo.
--
--  ── PERCHÉ DUE TABELLE DEI FATTI ──────────────────────────────────────────
--
--  `fatto_riga` è la tabella atomica: più in basso di così i dati non vanno.
--  `fatto_ordine` è un AGGREGATO dichiarato, alla grana della fattura.
--
--  Non è lo stesso difetto del punto 1, ed è bene dire perché. Una tabella
--  aggregata è un oggetto con un nome, una grana scritta e un momento in cui
--  viene ricostruita: 04_carica.py la riscrive da fatto_riga e poi controlla
--  che le due quadrino, uscendo con errore se non lo fanno. Delle misure
--  nascoste dentro una dimensione, invece, non si accorge nessuno.
--
--  Esiste perché la domanda di questo progetto è sulla sequenza degli ordini
--  di un cliente, e ogni vista qui sotto parte da lì. Ricostruirla ogni volta
--  con una GROUP BY su 776.575 righe funzionerebbe, ma nasconderebbe la grana
--  vera dell'analisi dentro una sottoquery.
--
--  ── LA FATTURA È UNA DIMENSIONE DEGENERE ──────────────────────────────────
--
--  Il numero di fattura non ha attributi propri: tutto quello che si sa di una
--  fattura è il suo cliente, la sua data e i suoi importi, e stanno già
--  altrove. Quindi resta come colonna dentro i fatti, senza una dim_fattura
--  fatta di una chiave e nient'altro.
--
--  ── COSA STA IN UNA DIMENSIONE E COSA NO ───────────────────────────────────
--
--  `dim_cliente` tiene primo_ordine e coorte, che sono pur sempre derivati dai
--  fatti. La differenza con n_ordini non è un cavillo: la coorte è un
--  attributo su cui si RAGGRUPPA e si filtra, non una quantità che si somma,
--  e non cambia mai più una volta che il cliente è entrato. n_ordini invece
--  cambia a ogni acquisto, e va contato dai fatti quando serve.
--
--  Le righe che entrano qui sono già pulite secondo DATI-SPORCHI.md. Il file
--  grezzo non viene mai toccato: se una decisione di pulizia cambia, si
--  ricarica, non si aggiusta il database a mano.
-- ============================================================================

DROP VIEW  IF EXISTS v_funnel_riacquisto;
DROP VIEW  IF EXISTS v_retention_coorte;
DROP VIEW  IF EXISTS v_coorte_mese;
DROP VIEW  IF EXISTS v_ordini_sequenza;
DROP TABLE IF EXISTS fatto_riga;
DROP TABLE IF EXISTS fatto_ordine;
DROP TABLE IF EXISTS dim_articolo;
DROP TABLE IF EXISTS dim_cliente;
DROP TABLE IF EXISTS dim_data;
-- le tabelle del modello precedente, se il database viene da quella versione
DROP TABLE IF EXISTS righe;
DROP TABLE IF EXISTS ordini;
DROP TABLE IF EXISTS clienti;


-- ── dim_data ────────────────────────────────────────────────────────────────
--  Un giorno per riga, per tutto il periodo coperto — giorni senza vendite
--  compresi, se no un raggruppamento per mese salterebbe i buchi in silenzio.
CREATE TABLE dim_data (
  data_key         INT          NOT NULL PRIMARY KEY,   -- AAAAMMGG
  data             DATE         NOT NULL,
  anno             SMALLINT     NOT NULL,
  mese             TINYINT      NOT NULL,
  nome_mese        VARCHAR(10)  NOT NULL,
  trimestre        TINYINT      NOT NULL,
  anno_mese        CHAR(7)      NOT NULL,               -- '2010-03'
  giorno_settimana TINYINT      NOT NULL,               -- 1 = lunedì
  nome_giorno      VARCHAR(10)  NOT NULL,
  fine_settimana   TINYINT      NOT NULL,
  UNIQUE KEY uq_dim_data (data),
  KEY idx_dim_data_mese (anno_mese)
) ENGINE=InnoDB;


-- ── dim_cliente ─────────────────────────────────────────────────────────────
CREATE TABLE dim_cliente (
  cliente_key     INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
  cliente_id      INT           NOT NULL,               -- chiave naturale
  paese           VARCHAR(40)   NOT NULL,
  -- Il paese è quello della prima fattura. Un cliente può comparire con
  -- paesi diversi (spedizioni a indirizzi diversi): prendere il primo è una
  -- scelta, ed è scritta qui perché si veda.
  primo_ordine    DATE          NOT NULL,
  coorte          CHAR(7)       NOT NULL,               -- '2010-03'
  UNIQUE KEY uq_dim_cliente (cliente_id),
  KEY idx_dim_cliente_coorte (coorte),
  KEY idx_dim_cliente_paese (paese)
) ENGINE=InnoDB;


-- ── dim_articolo ────────────────────────────────────────────────────────────
--  Costruirla ha costretto a decidere una cosa che prima nessuno decideva:
--  622 codici compaiono con più di una descrizione. Si tiene la più
--  frequente, e si scrive quante ne sono state viste — così chi guarda la
--  dimensione sa che c'era una scelta, invece di crederla un dato.
CREATE TABLE dim_articolo (
  articolo_key    INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
  codice          VARCHAR(30)   NOT NULL,
  descrizione     VARCHAR(120)  NULL,
  n_descrizioni   SMALLINT      NOT NULL DEFAULT 1,
  UNIQUE KEY uq_dim_articolo (codice)
) ENGINE=InnoDB;


-- ── fatto_riga ──────────────────────────────────────────────────────────────
--  La tabella atomica. `fattura` è la dimensione degenere.
CREATE TABLE fatto_riga (
  riga_key        BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fattura         VARCHAR(20)   NOT NULL,
  cliente_key     INT           NOT NULL,
  articolo_key    INT           NOT NULL,
  data_key        INT           NOT NULL,
  data_ora        DATETIME      NOT NULL,
  quantita        INT           NOT NULL,
  prezzo          DECIMAL(10,2) NOT NULL,
  valore          DECIMAL(12,2) NOT NULL,
  CONSTRAINT fk_riga_cliente  FOREIGN KEY (cliente_key)  REFERENCES dim_cliente(cliente_key),
  CONSTRAINT fk_riga_articolo FOREIGN KEY (articolo_key) REFERENCES dim_articolo(articolo_key),
  CONSTRAINT fk_riga_data     FOREIGN KEY (data_key)     REFERENCES dim_data(data_key),
  KEY idx_riga_fattura (fattura),
  KEY idx_riga_cliente (cliente_key),
  -- Le pulizie sono già state fatte a monte, ma un vincolo che le ripete
  -- costa niente e impedisce che una ricarica sbagliata rimetta dentro quello
  -- che DATI-SPORCHI.md dice di aver tolto.
  CONSTRAINT chk_riga_positiva CHECK (quantita > 0 AND prezzo > 0)
) ENGINE=InnoDB;


-- ── fatto_ordine ────────────────────────────────────────────────────────────
--  Aggregato dichiarato alla grana della fattura, ricostruito da fatto_riga a
--  ogni caricamento e poi confrontato con essa. Vedi la nota in testa al file.
CREATE TABLE fatto_ordine (
  fattura         VARCHAR(20)   NOT NULL PRIMARY KEY,
  cliente_key     INT           NOT NULL,
  data_key        INT           NOT NULL,
  data_ora        DATETIME      NOT NULL,
  n_righe         INT           NOT NULL,
  n_pezzi         INT           NOT NULL,
  valore          DECIMAL(12,2) NOT NULL,
  CONSTRAINT fk_ordine_cliente FOREIGN KEY (cliente_key) REFERENCES dim_cliente(cliente_key),
  CONSTRAINT fk_ordine_data    FOREIGN KEY (data_key)    REFERENCES dim_data(data_key),
  KEY idx_ordine_cliente_data (cliente_key, data_ora)
) ENGINE=InnoDB;


-- ============================================================================
--  Le viste
-- ============================================================================

-- ── 1. Ogni ordine con il suo posto nella storia del cliente ────────────────
--  È la vista su cui poggiano tutte le altre. Le funzioni finestra fanno il
--  lavoro che in pandas sarebbe un groupby con shift: qui restano dentro il
--  database, e chi legge la query vede la definizione insieme al risultato.
CREATE VIEW v_ordini_sequenza AS
SELECT
  o.fattura,
  c.cliente_id,
  d.data,
  o.valore,
  c.paese,
  ROW_NUMBER() OVER (PARTITION BY o.cliente_key ORDER BY o.data_ora, o.fattura)
    AS n_ordine,
  DATEDIFF(d.data, LAG(d.data) OVER (PARTITION BY o.cliente_key ORDER BY o.data_ora, o.fattura))
    AS giorni_dal_precedente,
  c.primo_ordine AS data_primo_ordine,
  -- La coorte arriva dalla dimensione, non si ricalcola qui: è un attributo
  -- del cliente, e deve dare lo stesso valore ovunque venga chiesto.
  CONCAT(c.coorte, '-01') AS coorte,
  -- Distanza fra caselle del calendario, non mesi interi passati.
  -- TIMESTAMPDIFF(MONTH, '2010-01-20', '2010-02-03') fa 0, e metterebbe un
  -- riacquisto di febbraio nel mese 0 insieme al primo acquisto: succedeva al
  -- 28% degli ordini. Vedi migrazioni/2026-08-27_mese_relativo.sql.
  (d.anno - YEAR(c.primo_ordine)) * 12 + (d.mese - MONTH(c.primo_ordine))
    AS mese_relativo,
  COUNT(*) OVER (PARTITION BY o.cliente_key)
    AS ordini_totali_cliente
FROM fatto_ordine o
JOIN dim_cliente c ON c.cliente_key = o.cliente_key
JOIN dim_data    d ON d.data_key    = o.data_key;

-- ── 2. Quanti clienti entrano ogni mese ─────────────────────────────────────
CREATE VIEW v_coorte_mese AS
SELECT
  CONCAT(coorte, '-01')        AS coorte,
  COUNT(*)                     AS clienti_entrati
FROM dim_cliente
GROUP BY coorte;

-- ── 3. La matrice di retention ──────────────────────────────────────────────
--  Di cento clienti entrati nel mese X, quanti hanno ordinato nel mese X+n.
--  «Attivo» qui vuol dire «ha fatto almeno un ordine in quel mese», non «è
--  ancora cliente»: sono due cose diverse e la seconda non è osservabile.
--
--  ATTENZIONE alla lettura: le coorti recenti hanno pochi mesi di vita. Un
--  valore basso a +12 per la coorte di novembre 2011 non vuol dire che quei
--  clienti sono peggiori, vuol dire che il dodicesimo mese non è ancora
--  arrivato. `mesi_osservabili` serve a non confondere le due cose, e conta
--  solo i mesi FINITI: dicembre 2011 è lungo nove giorni e non vale.
CREATE VIEW v_retention_coorte AS
SELECT
  s.coorte,
  s.mese_relativo,
  COUNT(DISTINCT s.cliente_id)                    AS clienti_attivi,
  c.clienti_entrati,
  ROUND(COUNT(DISTINCT s.cliente_id) * 100.0 / c.clienti_entrati, 2)
                                                  AS quota_attivi,
  (YEAR(u.ultimo_mese_intero)  - YEAR(s.coorte))  * 12
  + (MONTH(u.ultimo_mese_intero) - MONTH(s.coorte))
                                                  AS mesi_osservabili
FROM v_ordini_sequenza s
JOIN v_coorte_mese c ON c.coorte = s.coorte
CROSS JOIN (
  -- L'ultimo mese di cui si sono visti tutti i giorni. Se i dati finissero
  -- proprio all'ultimo giorno del mese quel mese sarebbe intero: si controlla,
  -- invece di togliere sempre un mese e perderne uno buono.
  SELECT CASE WHEN MAX(d.data) = LAST_DAY(MAX(d.data))
              THEN DATE_FORMAT(MAX(d.data), '%Y-%m-01')
              ELSE DATE_FORMAT(DATE_SUB(DATE_FORMAT(MAX(d.data), '%Y-%m-01'), INTERVAL 1 DAY), '%Y-%m-01')
         END AS ultimo_mese_intero
  FROM fatto_ordine o JOIN dim_data d ON d.data_key = o.data_key
) u
GROUP BY s.coorte, s.mese_relativo, c.clienti_entrati, u.ultimo_mese_intero;

-- ── 4. Il funnel di riacquisto ──────────────────────────────────────────────
--  Non è un funnel di conversione: in dati transazionali non esistono
--  sessioni né carrelli abbandonati. È la sopravvivenza da un ordine al
--  successivo — su cento clienti che ne fanno uno, quanti arrivano al secondo.
CREATE VIEW v_funnel_riacquisto AS
SELECT
  n_ordine                                        AS gradino,
  COUNT(DISTINCT cliente_id)                      AS clienti_arrivati,
  ROUND(COUNT(DISTINCT cliente_id) * 100.0 /
        (SELECT COUNT(*) FROM dim_cliente), 2)    AS quota_sul_totale,
  ROUND(AVG(giorni_dal_precedente), 1)            AS giorni_medi_dal_precedente,
  ROUND(AVG(valore), 2)                           AS valore_medio_ordine
FROM v_ordini_sequenza
GROUP BY n_ordine;
