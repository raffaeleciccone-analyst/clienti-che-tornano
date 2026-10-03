-- ============================================================================
--  Il mese relativo era contato con TIMESTAMPDIFF, e non è il mese di coorte
-- ============================================================================
--
--  TIMESTAMPDIFF(MONTH, a, b) conta i mesi INTERI passati, non la distanza fra
--  due caselle del calendario:
--
--    TIMESTAMPDIFF(MONTH, '2010-01-20', '2010-02-03')  ->  0
--    (YEAR/MONTH)                                      ->  1
--
--  Un cliente entrato il 20 gennaio che ricompra il 3 febbraio finiva nel mese
--  0 della sua coorte, insieme al suo primo acquisto. Succede a 10.257 ordini
--  su 36.594: il 28%.
--
--  L'effetto ha una direzione sola: gonfia la colonna 0 e svuota la colonna 1,
--  cioè fa sembrare che i clienti tornino meno di quanto tornano. E la colonna
--  1 è quella su cui poggia tutta l'analisi.
--
--  «Mese di coorte» vuol dire distanza fra caselle del calendario: chi entra a
--  gennaio e compra a febbraio è al mese 1, il giorno del mese non c'entra.
--  Questa è la definizione che usa la matrice, e ora è anche quella scritta
--  nella vista.
-- ============================================================================

DROP VIEW IF EXISTS v_funnel_riacquisto;
DROP VIEW IF EXISTS v_retention_coorte;
DROP VIEW IF EXISTS v_ordini_sequenza;

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

-- ── la matrice ──────────────────────────────────────────────────────────────
--  Cambia anche `mesi_osservabili`, per lo stesso motivo. Prima usava
--  MAX(data) = 2011-12-09, cioè contava dicembre 2011 come un mese osservato:
--  ma dicembre 2011 è lungo nove giorni. Un mese vale solo se è finito, e
--  l'ultimo mese finito nei dati è novembre 2011.
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
