"""Le regole di pulizia, scritte in un posto solo (SPEC C1, DATI-SPORCHI.md §4-§5).

Fino al 21/11/2026 la lista dei codici non-prodotto era copiata in tre script, e
DATI-SPORCHI.md ne nominava solo una parte: una ricostruzione alla cieca partita
dai soli documenti è arrivata a 776.607 righe invece di 776.575. Adesso c'è una
sola lista, e ogni codice ha accanto il motivo.
"""

# Le righe uguali in queste sei colonne sono la stessa riga contata due volte (§1).
CHIAVE = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"]

# Sotto un penny non è una vendita: sono segnaposto e omaggi (es. PADS a £0,001).
# Aggiunta il 21/11/2026; prima la regola era «prezzo > 0».
PREZZO_MINIMO = 0.01

# Scritti a mano dopo aver guardato i codici, non dedotti da una regola: «non comincia
# con cinque cifre» prenderebbe anche DCGS0058, che è un prodotto vero.
NON_PRODOTTI = {
    "POST": "spedizione",
    "DOT": "spedizione (dotcom postage)",
    "C2": "spedizione (carriage)",
    "C3": "spedizione",
    "M": "rettifica manuale",
    "m": "rettifica manuale",
    "D": "sconto",
    "S": "campioni",
    "B": "rettifica del debito",
    "BANK CHARGES": "commissioni bancarie",
    "AMAZONFEE": "commissione Amazon",
    "CRUK": "commissione a un ente benefico",
    "ADJUST": "rettifica",
    "ADJUST2": "rettifica manuale («Adjustment by Peter on Jun 25 2010»)",
    "TEST001": "prodotto di prova («This is a test product.»)",
    "TEST002": "prodotto di prova",
    "gift_0001_10": "buono regalo",
    "gift_0001_20": "buono regalo",
    "gift_0001_30": "buono regalo",
    "gift_0001_40": "buono regalo",
    "gift_0001_50": "buono regalo",
}
# Non sono in lista, di proposito (21/11/2026): SP1002 è una lavagnetta per bambini
# venduta a £2,95; PADS sono imbottiture per cuscini (le sue righe a £0,001 escono con
# PREZZO_MINIMO, non perché il codice non sia un prodotto).
