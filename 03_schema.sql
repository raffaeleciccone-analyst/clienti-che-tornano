-- ============================================================================
--  Il modello: tre tabelle e le viste che rispondono alle sotto-domande
-- ============================================================================
--
--  Grana, dichiarata prima di scrivere le CREATE, perche' e' la decisione che
--  poi non si cambia piu':
--
--    righe    una riga di fattura   (fattura x articolo)
--    ordini   una fattura           (= un ordine, per questo negozio)
--    clienti  un cliente
--
--  «Ordine» e «fattura» qui sono la stessa cosa: il dataset non ha un concetto
--  di ordine separato dalla fattura, e inventarne uno vorrebbe dire decidere a
--  tavolino che due fatture dello stesso giorno sono un ordine solo. Non si fa:
--  si usa quello che c'e' e lo si chiama col suo nome.
--
--  Le righe che entrano qui sono gia' pulite secondo DATI-SPORCHI.md. Il file
--  grezzo non viene mai toccato: se una decisione di pulizia cambia, si
--  ricarica, non si aggiusta il database a mano.
-- ============================================================================

DROP VIEW IF EXISTS v_funnel_riacquisto;
DROP VIEW IF EXISTS v_retention_coorte;
DROP VIEW IF EXISTS v_coorte_mese;
DROP VIEW IF EXISTS v_ordini_sequenza;
DROP TABLE IF EXISTS righe;
DROP TABLE IF EXISTS ordini;
DROP TABLE IF EXISTS clienti;

-- ── clienti ─────────────────────────────────────────────────────────────────
CREATE TABLE clienti (
  cliente_id      INT           NOT NULL PRIMARY KEY,
  paese           VARCHAR(40)   NOT NULL,
  -- Il paese del cliente e' quello della sua prima fattura. Un cliente puo'
  -- comparire con paesi diversi (spedizioni a indirizzi diversi): prendere il
  -- primo e' una scelta, ed e' scritta qui perche' si veda.
  primo_ordine    DATE          NOT NULL,
  ultimo_ordine   DATE          NOT NULL,
  n_ordini        INT           NOT NULL,
  ricavo_totale   DECIMAL(12,2) NOT NULL,
  KEY idx_clienti_primo (primo_ordine),
  KEY idx_clienti_paese (paese)
) ENGINE=InnoDB;

-- ── ordini ──────────────────────────────────────────────────────────────────
CREATE TABLE ordini (
  fattura         VARCHAR(20)   NOT NULL PRIMARY KEY,
  cliente_id      INT           NOT NULL,
  data_ora        DATETIME      NOT NULL,
  data            DATE          NOT NULL,
  n_righe         INT           NOT NULL,
  n_pezzi         INT           NOT NULL,
  valore          DECIMAL(12,2) NOT NULL,
  paese           VARCHAR(40)   NOT NULL,
  CONSTRAINT fk_ordini_cliente FOREIGN KEY (cliente_id)
    REFERENCES clienti(cliente_id) ON DELETE CASCADE,
  KEY idx_ordini_cliente_data (cliente_id, data_ora),
  KEY idx_ordini_data (data)
) ENGINE=InnoDB;

-- ── righe ───────────────────────────────────────────────────────────────────
CREATE TABLE righe (
  id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fattura         VARCHAR(20)   NOT NULL,
  cliente_id      INT           NOT NULL,
  articolo        VARCHAR(30)   NOT NULL,
  descrizione     VARCHAR(120)  NULL,
  quantita        INT           NOT NULL,
  prezzo          DECIMAL(10,2) NOT NULL,
  valore          DECIMAL(12,2) NOT NULL,
  data_ora        DATETIME      NOT NULL,
  CONSTRAINT fk_righe_ordine FOREIGN KEY (fattura)
    REFERENCES ordini(fattura) ON DELETE CASCADE,
  KEY idx_righe_cliente (cliente_id),
  KEY idx_righe_articolo (articolo),
  -- Le pulizie sono gia' state fatte a monte, ma un vincolo che le ripete
  -- costa niente e impedisce che una ricarica sbagliata rimetta dentro quello
  -- che DATI-SPORCHI.md dice di aver tolto.
  CONSTRAINT chk_righe_positive CHECK (quantita > 0 AND prezzo > 0)
) ENGINE=InnoDB;


-- ============================================================================
--  Le viste
-- ============================================================================

-- ── 1. Ogni ordine con il suo posto nella storia del cliente ────────────────
--  E' la vista su cui poggiano tutte le altre. Le funzioni finestra fanno il
--  lavoro che in pandas sarebbe un groupby con shift: qui restano dentro il
--  database, e chi legge la query vede la definizione insieme al risultato.
CREATE VIEW v_ordini_sequenza AS
SELECT
  o.fattura,
  o.cliente_id,
  o.data,
  o.valore,
  o.paese,
  ROW_NUMBER() OVER (PARTITION BY o.cliente_id ORDER BY o.data_ora, o.fattura)
    AS n_ordine,
  DATEDIFF(o.data, LAG(o.data) OVER (PARTITION BY o.cliente_id ORDER BY o.data_ora, o.fattura))
    AS giorni_dal_precedente,
  MIN(o.data) OVER (PARTITION BY o.cliente_id)
    AS data_primo_ordine,
  DATE_FORMAT(MIN(o.data) OVER (PARTITION BY o.cliente_id), '%Y-%m-01')
    AS coorte,
  -- distanza fra caselle del calendario, non mesi interi passati: vedi sopra
  (YEAR(o.data)  - YEAR(MIN(o.data)  OVER (PARTITION BY o.cliente_id))) * 12
  + (MONTH(o.data) - MONTH(MIN(o.data) OVER (PARTITION BY o.cliente_id)))
    AS mese_relativo,
  COUNT(*) OVER (PARTITION BY o.cliente_id)
    AS ordini_totali_cliente
FROM ordini o;

-- ── 2. Quanti clienti entrano ogni mese ─────────────────────────────────────
CREATE VIEW v_coorte_mese AS
SELECT
  DATE_FORMAT(primo_ordine, '%Y-%m-01') AS coorte,
  COUNT(*)                              AS clienti_entrati,
  ROUND(AVG(ricavo_totale), 2)          AS ricavo_medio_a_oggi
FROM clienti
GROUP BY DATE_FORMAT(primo_ordine, '%Y-%m-01');

-- ── 3. La matrice di retention ──────────────────────────────────────────────
--  Di cento clienti entrati nel mese X, quanti hanno ordinato nel mese X+n.
--  «Attivo» qui vuol dire «ha fatto almeno un ordine in quel mese», non «e'
--  ancora cliente»: sono due cose diverse e la seconda non e' osservabile.
--
--  ATTENZIONE alla lettura: le coorti recenti hanno pochi mesi di vita. Un
--  valore basso a +12 per la coorte di novembre 2011 non vuol dire che quei
--  clienti sono peggiori, vuol dire che il dodicesimo mese non e' ancora
--  arrivato. La colonna `mesi_osservabili` serve a non confondere le due cose,
--  e conta solo i mesi FINITI: dicembre 2011 e' lungo nove giorni e non vale.
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
  SELECT CASE WHEN MAX(data) = LAST_DAY(MAX(data))
              THEN DATE_FORMAT(MAX(data), '%Y-%m-01')
              ELSE DATE_FORMAT(DATE_SUB(DATE_FORMAT(MAX(data), '%Y-%m-01'), INTERVAL 1 DAY), '%Y-%m-01')
         END AS ultimo_mese_intero
  FROM ordini
) u
GROUP BY s.coorte, s.mese_relativo, c.clienti_entrati, u.ultimo_mese_intero;

-- ── 4. Il funnel di riacquisto ──────────────────────────────────────────────
--  Non e' un funnel di conversione: in dati transazionali non esistono
--  sessioni ne' carrelli abbandonati. E' la sopravvivenza da un ordine al
--  successivo — su cento clienti che ne fanno uno, quanti arrivano al secondo.
CREATE VIEW v_funnel_riacquisto AS
SELECT
  n_ordine                                        AS gradino,
  COUNT(DISTINCT cliente_id)                      AS clienti_arrivati,
  ROUND(COUNT(DISTINCT cliente_id) * 100.0 /
        (SELECT COUNT(*) FROM clienti), 2)        AS quota_sul_totale,
  ROUND(AVG(giorni_dal_precedente), 1)            AS giorni_medi_dal_precedente,
  ROUND(AVG(valore), 2)                           AS valore_medio_ordine
FROM v_ordini_sequenza
GROUP BY n_ordine;
