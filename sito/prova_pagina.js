/* Fa girare lo script della pagina fuori dal browser, con un DOM finto.
 *
 * Non sostituisce l'apertura in Chrome: non disegna niente e non sa niente di
 * layout. Serve a una cosa sola, ed è quella che rompe le pagine più spesso —
 * un errore a runtime che lascia il documento vuoto senza dire perché.
 *
 * Uso:  node sito/prova_pagina.js
 */
const fs = require("fs");
const path = require("path");

const pagina = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const script = pagina.slice(pagina.lastIndexOf("<script>") + 8, pagina.lastIndexOf("</script>"));

// gli id dichiarati nel documento, presi dall'HTML vero
const idPresenti = [...pagina.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);

const scritture = {};      // id -> quanto contenuto ci è finito dentro
const ascoltatori = {};    // id -> eventi collegati

function nodo(id){
  const el = {
    _id: id, dataset: {}, style: {
      setProperty(){}, get transform(){ return this._t || ""; }, set transform(v){ this._t = v; }
    },
    setAttribute(){}, addEventListener(t){ (ascoltatori[id] ||= []).push(t); },
    set onclick(f){ (ascoltatori[id] ||= []).push("click"); },
    set innerHTML(v){ scritture[id] = String(v); },
    get innerHTML(){ return scritture[id] || ""; },
    set textContent(v){ scritture[id] = String(v); },
    get textContent(){ return scritture[id] || ""; },
    get value(){ return "20"; },
    querySelectorAll: () => [],
    querySelector: () => nodo(id + "/figlio"),
    // la larghezza di una colonna, che nel browser vera la dà il CSS
    getBoundingClientRect: () => ({ width: 26, height: 22, left: 0, right: 26, top: 0, bottom: 22 }),
  };
  return el;
}

const cache = {};
global.document = {
  documentElement: { style: { setProperty(){} } },
  getElementById(id){
    if (!idPresenti.includes(id)) throw new Error(`id inesistente nel documento: ${id}`);
    return (cache[id] ||= nodo(id));
  },
  querySelectorAll: () => [],
};
global.getComputedStyle = () => ({
  getPropertyValue(n){
    // le misure della matrice: senza queste misure() restituisce NaN e le celle
    // finiscono tutte a translateX(NaN)
    return { "--freddo": "#7f9cb4", "--tiepido": "#e9e3d5", "--caldo": "#a9741d",
             "--c": "26px", "--etichetta": "104px" }[n] || "#000000";
  }
});
// La pagina si riaggancia a resize per rimettere le celle quando cambia il passo.
global.addEventListener = (tipo) => { (ascoltatori["window"] ||= []).push(tipo); };
global.window = global;

let uscita = 0;
try {
  new Function(script)();
} catch (e) {
  console.error("ERRORE A RUNTIME:", e.message);
  console.error(e.stack.split("\n").slice(1, 4).join("\n"));
  process.exit(1);
}

// Un errore silenzioso peggiore del crash: lo script gira, ma non scrive niente.
const attesi = ["griglia", "funnel", "curva", "tab-anonimi", "quanto-spiega",
                "tab-futuro", "futuro-lettura"];
console.log("contenuto prodotto da ogni blocco:");
for (const id of attesi){
  const n = (scritture[id] || "").length;
  const ok = n > 60;
  if (!ok) uscita = 1;
  console.log(`  [${ok ? "ok" : "NO"}] ${id.padEnd(16)} ${String(n).padStart(7)} caratteri`);
}

// L'esempio che definisce la parola «coorte»: due caselle corte, sotto la soglia
// dei 60 caratteri di sopra, ma se restano vuote la definizione non definisce niente.
console.log("");
console.log("l'esempio nella definizione di coorte:");
for (const id of ["coorte-esempio", "coorte-esempio-n"]){
  const v = (scritture[id] || "").trim();
  const ok = v.length > 0;
  if (!ok) uscita = 1;
  console.log(`  [${ok ? "ok" : "NO"}] ${id.padEnd(16)} ${v || "VUOTO"}`);
}

// Senza questo la matrice resta ferma alla larghezza di partenza quando si gira il
// telefono o si stringe la finestra.
const suFinestra = (ascoltatori["window"] || []).includes("resize");
if (!suFinestra) uscita = 1;
console.log("");
console.log(`  [${suFinestra ? "ok" : "NO"}] la matrice si ridisegna al resize`);

const clic = Object.keys(ascoltatori);
console.log(`\ncomandi collegati: ${clic.join(", ") || "NESSUNO"}`);
for (const id of ["b-eta", "b-cal"]){
  const ok = clic.includes(id);
  if (!ok) uscita = 1;
  console.log(`  [${ok ? "ok" : "NO"}] ${id}`);
}

// le cifre chiave devono comparire nel testo prodotto, non solo nei dati
const dati = JSON.parse(fs.readFileSync(path.join(__dirname, "dati.json"), "utf8"));
const tutto = Object.values(scritture).join(" ");
console.log("\ncifre che devono comparire nella pagina:");
for (const [nome, atteso] of [
  ["spiegata dal calendario", String(dati.spiegata.calendario)],
  // il confronto corretto il 2/10/2026
  ["a pari partenza (91-365)", String(dati.valore_futuro.pari_partenza.stima)],
  ["a pari spesa a 90 giorni", String(dati.valore_futuro.pari_spesa_90.stima)],
]){
  const ok = tutto.includes(atteso);
  if (!ok) uscita = 1;
  console.log(`  [${ok ? "ok" : "NO"}] ${nome.padEnd(24)} ${atteso}`);
}

process.exit(uscita);
