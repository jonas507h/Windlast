// footer.js  (als ES Module laden)
import { configureMeldungen, setupMeldungenUI } from "./modal/meldungen.js";
import { configureErgebnisse, setupErgebnisseUI } from "./modal/ergebnisse.js";
import { displayAltName } from "./utils/formatierung.js";
import { getNorminfo } from "./modal/norminfo.js";

const NORM_ID = {
  "EN_13814_2005": "en13814_2005",
  "EN_17879_2024": "en17879_2024",
  "EN_1991_1_4_2010": "en1991_2010",
};
const COLS = ["EN_13814_2005", "EN_17879_2024", "EN_1991_1_4_2010"];
const ROWS = [
  { key: "kipp",    label: "Kippsicherheit",   isSafety: true  },
  { key: "gleit",   label: "Gleitsicherheit",  isSafety: true  },
  { key: "abhebe",  label: "Abhebesicherheit", isSafety: true  },
  { key: "ballast", label: "erforderlicher Ballast", isSafety: false },
];

function buildModal(titleText, bodyNodeOrHtml) {
  const wrap = document.createElement("div");
  const h = document.createElement("h3");
  h.textContent = titleText;
  h.className = "modal-title";
  wrap.appendChild(h);

  if (typeof bodyNodeOrHtml === "string") {
    const div = document.createElement("div");
    div.innerHTML = bodyNodeOrHtml;
    wrap.appendChild(div);
  } else if (bodyNodeOrHtml instanceof Node) {
    wrap.appendChild(bodyNodeOrHtml);
  }
  return wrap;
}

let ResultsVM = null; // hält das von ResultsIndex.build(...) erzeugte ViewModel

function severityFromCounts(c) {
  if (!c) return "info";
  if (c.error > 0) return "error";
  if (c.warn  > 0) return "warn";
  if (c.hint  > 0) return "hint";
  return "info";
}
function totalFromCounts(c) {
  return (c?.error ?? 0) + (c?.warn ?? 0) + (c?.hint ?? 0) + (c?.info ?? 0);
}

function updateHeaderBadge(th, counts) {
  if (!th) return;
  // Badge holen/erzeugen
  let badge = th.querySelector(".count-badge");
  if (!badge) {
    badge = document.createElement("span");
    badge.className = "count-badge";
    th.appendChild(badge);
    // Platz rechts reservieren, falls nötig
    th.classList.add("has-count-badge");
  }

  const total = totalFromCounts(counts);
  const sev   = severityFromCounts(counts);

  // Optional: bei 0 ausblenden (oder `.muted` anzeigen – Geschmackssache)
  if (!total) {
    badge.hidden = true;
    return;
  }
  badge.hidden = false;
  badge.textContent = String(total);

  // Severity-Klassen setzen
  badge.classList.remove("badge-error","badge-warn","badge-hint","badge-info");
  badge.classList.add(`badge-${sev}`);
}

function refreshHeaderBadges() {
  // Hauptberechnung pro Norm (thead)
  document.querySelectorAll(".results-table thead th[data-norm-key]").forEach(th => {
    const c = getCountsEffective(th.dataset.normKey, null);
    updateHeaderBadge(th, c);
  });

  // Alternativen-Zeilen (pro Norm + Szenario)
  document.querySelectorAll(".results-table .alt-title th[data-norm-key][data-szenario]").forEach(th => {
    const c = getCountsEffective(th.dataset.normKey, th.dataset.szenario);
    updateHeaderBadge(th, c);
  });
}

function attachNormKeysToHeader() {
  // ordnet thead-ths der COLS-Reihenfolge zu
  const ths = document.querySelectorAll('.results-table thead th');
  // th[0] ist der Stub "Nachweis"
  for (let i = 1; i < ths.length && i <= COLS.length; i++) {
    const th = ths[i];
    th.dataset.normKey = COLS[i - 1]; // "EN_13814_2005" etc.
  }
}

function klassifizierung_anwenden(el, good) {
  if (!el) return;
  el.classList.remove("val-ok", "val-bad");
  el.classList.add(good ? "val-ok" : "val-bad");
}

function sicherheit_klassifizieren(val) {
  if (val === "INF") return true;
  if (val === "-INF") return false;
  let num = typeof val === "string" ? Number(val) : val;
  if (num === null || num === undefined || Number.isNaN(num)) return false;
  num = Math.floor(num * 100) / 100;
  return num >= 1.0;
}

function formatBallast(val_kg) {
  if (val_kg === "INF" || val_kg === "-INF") return val_kg === "INF" ? "∞" : "−∞";
  const n = typeof val_kg === "string" ? Number(val_kg) : val_kg;
  if (!isFinite(n)) return "—";
  if (n <= 0) return "0 kg";

  // < 1000 kg -> in kg, Mindestschritt 10 kg, immer aufrunden
  if (n < 1000) {
    const rounded = Math.ceil(n / 10 ) * 10;
    return `${rounded.toLocaleString("de-DE")} kg`;
  }

  // 1000-9999 kg -> x,x t, Mindestschritt 0,1 t, immer aufrunden
  if (n < 10000) {
    const t = n / 1000;
    const rounded = Math.ceil(t * 10) / 10;
    return `${rounded.toLocaleString("de-DE")} t`;
  }

  // >= 10000 kg -> 3 signifikante Stellen in t, immer aufrunden
  const t = n / 1000;
  const magnitude = Math.pow(10, Math.floor(Math.log10(t)) - 2);
  const rounded = Math.ceil(t / magnitude) * magnitude;
  return `${rounded.toLocaleString("de-DE")} t`;
}

//=== Zell-Setter ===
function hasErrorFor(normKey, szenario = null) {
  const counts = szenario
    ? ResultsVM?.getCounts(normKey, szenario)
    : ResultsVM?.getCountsMainOnly(normKey);
  return (counts?.error ?? 0) > 0;
}

function getScenarioForCell(el) {
  // Zellen in Alternativenzeilen tragen meist data-alt auf der Zelle
  // oder data-szenario am Zeilen-Header:
  return el.dataset.alt || el.closest("tr")?.dataset.szenario || null;
}

function applySafetyToCell(td, val, { allowBlank=false } = {}) {
  if (!td) return;
  if (val === "INF" || val === "-INF") {
    td.textContent = val === "INF" ? "∞" : "−∞";
    td.title = "";
    klassifizierung_anwenden(td, sicherheit_klassifizieren(val));
    return;
  }
  const num = typeof val === "string" ? Number(val) : val;
  if (!Number.isFinite(num)) {
    td.textContent = allowBlank ? "" : "—";
    td.title = "";
    td.classList.remove("val-ok", "val-bad");
    return;
  }
  td.textContent = (Math.floor(num * 100) / 100).toFixed(2);
  td.title = "";
  klassifizierung_anwenden(td, sicherheit_klassifizieren(num));
}

function applyBallastToCell(td, valKg, { allowBlank=false } = {}) {
  if (!td) return;
  if (valKg === "INF" || valKg === "-INF") {
    td.textContent = valKg === "INF" ? "∞" : "−∞";
    td.title = "";
    td.classList.remove("val-ok", "val-bad"); // bei Ballast keine Klassifizierung
    return;
  }
  const n = typeof valKg === "string" ? Number(valKg) : valKg;
  if (!Number.isFinite(n)) {
    td.textContent = allowBlank ? "" : "—";
    td.title = "";
    td.classList.remove("val-ok", "val-bad");
    return;
  }
  td.textContent = formatBallast(n);
  td.title = "";
}

function _clearAltRows() {
  const tbody = document.querySelector(".results-table tbody");
  if (!tbody) return;
  tbody.querySelectorAll('tr[data-alt-row="1"]').forEach(tr => tr.remove());
}

function parseCellId(id) {
  const m = /^([a-z]+)_(.+)$/.exec(id || "");
  if (!m) return null;
  const key = m[1];
  const suf = m[2];
  const normKey = Object.entries(NORM_ID).find(([, v]) => v === suf)?.[0] || null;
  return { key, suf, normKey };
}

function setDatasetFromId(el, id) {
  const parsed = parseCellId(id);
  if (!parsed) return;
  const { key, normKey } = parsed;
  if (normKey) el.dataset.normKey = normKey;
  el.dataset.nachweis =
    key === "ballast" ? "BALLAST" :
    key === "kipp"    ? "KIPP"    :
    key === "gleit"   ? "GLEIT"   :
    key === "abhebe"  ? "ABHEBE"   : "";
  if (el.dataset.alt) delete el.dataset.alt;
}

function setBallastCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  // Norm/Nachweis in die Datenattribute schreiben (falls noch nicht passiert)
  try { setDatasetFromId(el, id); } catch {}
  el.dataset.openable = "ergebnisse";

  // Szenario ermitteln & vor der Darstellung auf Fehler prüfen
  const normKey  = el.dataset.normKey || null;
  const szenario = getScenarioForCell(el);
  if (normKey && hasErrorFor(normKey, szenario)) {
    el.textContent = "--";
    el.title = "";
    el.classList.remove("val-ok");
    el.classList.add("val-bad");
    return;
  }
  applyBallastToCell(el, val, { allowBlank:false });
}

function setCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;

  // Norm/Nachweis zuerst setzen, damit wir normKey/szenario kennen
  try { setDatasetFromId(el, id); } catch {}
  el.dataset.openable = "ergebnisse";
  const normKey  = el.dataset.normKey || null;
  const szenario = getScenarioForCell(el);

  // Fehler? → alles unterdrücken
  if (normKey && hasErrorFor(normKey, szenario)) {
    el.textContent = "--";
    el.title = "";
    el.classList.remove("val-ok");
    el.classList.add("val-bad");
    return;
  }

  // Kein Fehler → normal formatieren
  applySafetyToCell(el, val, { allowBlank:false });
  // Falls applySafetyToCell nicht selbst klassifiziert, dann:
  klassifizierung_anwenden(el, sicherheit_klassifizieren(val));
}

function _setSafetyOnTdAlt(td, val) {
  const normKey  = td.dataset.normKey || null;
  const szenario = getScenarioForCell(td);
  const hasAlt   = !!td.dataset.alt; // nur echte Alternative markieren

  if (hasAlt && normKey && hasErrorFor(normKey, szenario)) {
    td.textContent = "--";
    td.title = "";
    td.classList.remove("val-ok");
    td.classList.add("val-bad");
    return;
  }
  // Leere Slots (ohne Alternative) dürfen wirklich leer bleiben
  applySafetyToCell(td, val, { allowBlank:true });
}

function _setBallastOnTdAlt(td, valKg) {
  const normKey  = td.dataset.normKey || null;
  const szenario = getScenarioForCell(td);
  const hasAlt   = !!td.dataset.alt;

  if (hasAlt && normKey && hasErrorFor(normKey, szenario)) {
    td.textContent = "--";
    td.title = "";
    td.classList.remove("val-ok");
    td.classList.add("val-bad");
    return;
  }
  applyBallastToCell(td, valKg, { allowBlank:true });
}

function renderAlternativenBlocksVM(vm) {
  const tbody = document.querySelector(".results-table tbody");
  if (!tbody) return;

  _clearAltRows();

  // Pro Norm: Liste alternativer Namen
  const altLists = {};
  let maxCount = 0;
  for (const normKey of COLS) {
    const names = vm.listAlternativen(normKey);
    altLists[normKey] = names;
    if (names.length > maxCount) maxCount = names.length;
  }

  for (let i = 0; i < maxCount; i++) {
    // Titelzeile für diesen Alternativen-Index
    const trTitle = document.createElement("tr");
    trTitle.setAttribute("data-alt-row", "1");
    trTitle.className = "alt-title";

    const thHead = document.createElement("th");
    thHead.scope = "col";
    thHead.className = "rowhead";
    thHead.textContent = "Nachweis";
    trTitle.appendChild(thHead);

    for (const normKey of COLS) {
      const th = document.createElement("th");
      th.scope = "col";
      th.className = "colhead-alt";
      const rawName = (altLists[normKey] && altLists[normKey][i]) ? altLists[normKey][i] : "";
      th.textContent = vm.getAltLabel(normKey, rawName);
      // optional: dem Alt-Titel das Norm-Key + Szenario mitgeben (kannst du später für Tooltips nutzen)
      if (rawName) { th.dataset.normKey = normKey; th.dataset.szenario = rawName; }
      trTitle.appendChild(th);
    }
    tbody.appendChild(trTitle);

    // Vier Zeilen: Kipp/Gleit/Abhebe/Ballast
    for (const row of ROWS) {
      const tr = document.createElement("tr");
      tr.setAttribute("data-alt-row", "1");

      const th = document.createElement("th");
      th.scope = "row";
      th.className = "rowhead";
      th.textContent = row.label;
      tr.appendChild(th);

      for (const normKey of COLS) {
        const td = document.createElement("td");
        td.className = "value";
        const altName = (altLists[normKey] && altLists[normKey][i]) ? altLists[normKey][i] : null;
        const v = altName ? vm.getAltValue(normKey, altName, row.key) : undefined;

        // data-* für Klick-Handler
        td.dataset.normKey  = normKey;
        td.dataset.nachweis =
          row.key === "ballast" ? "BALLAST" :
          row.key === "kipp"    ? "KIPP"    :
          row.key === "gleit"   ? "GLEIT"   :
          row.key === "abhebe"  ? "ABHEBE"   : "";
        if (altName) {
          td.dataset.alt = altName;         // (falls noch woanders genutzt)
          td.dataset.szenario = altName;
        } else {
          delete td.dataset.alt;
          delete td.dataset.szenario;
        }
        td.dataset.openable = "ergebnisse";

        if (row.isSafety) _setSafetyOnTdAlt(td, v);
        else _setBallastOnTdAlt(td, v);

        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
  }
}

function attachNorminfoHandlers() {
  // Titelzellen: Haupt + Alternativen
  const selector = `
    .results-table thead th[data-norm-key],
    .results-table .alt-title th[data-norm-key]
  `.trim();

  document.querySelectorAll(selector).forEach((th) => {
    if (th.dataset.norminfoBound === "1") return;
    th.dataset.norminfoBound = "1";

    th.addEventListener("click", (ev) => {
      // Badge-Klick weiterhin ignorieren
      if (ev.target.closest(".count-badge")) return;

      const normKey  = th.dataset.normKey;
      const szenario = th.dataset.szenario || null;
      if (!normKey) return;

      // NEU: direkt das Wiki aufrufen
      if (window.HELP && typeof window.HELP.openNorm === "function") {
        window.HELP.openNorm(normKey, szenario);
      }

      ev.preventDefault();
      ev.stopImmediatePropagation();
    });
  });
}

// --- NEU: Direktfunktion anbieten (für tor.js Variante 1)
window.updateFooterResults = function(payload){
  updateFooter(payload);
};

// --- NEU: CustomEvent-Listener (für tor.js Variante 2)
document.addEventListener("results:update", (ev) => {
  updateFooter(ev.detail);
});

function updateFooter(payload) {
  // ViewModel bauen
  ResultsVM = ResultsIndex.build(payload);

  // Header-Zellen einmal markieren (falls noch nicht)
  attachNormKeysToHeader();

  // Hauptwerte setzen (über VM, nicht direkt aus payload)
  for (const normKey of COLS) {
    const suf = NORM_ID[normKey];
    if (!suf) continue;

    setCell(`kipp_${suf}`,   ResultsVM.getMainValue(normKey, "kipp"));
    setCell(`gleit_${suf}`,  ResultsVM.getMainValue(normKey, "gleit"));
    setCell(`abhebe_${suf}`, ResultsVM.getMainValue(normKey, "abhebe"));
    setBallastCell(`ballast_${suf}`, ResultsVM.getMainValue(normKey, "ballast"));
  }

  // Alternativen rendern (neu: auf Basis der VM)
  renderAlternativenBlocksVM(ResultsVM);

  refreshHeaderBadges();

  attachNorminfoHandlers();

  configureMeldungen({
    vm: ResultsVM,
    buildModal,
    Modal,
    Tooltip,
  });
  configureErgebnisse({
    vm: ResultsVM,
    Modal,
    Tooltip, 
    buildModal,
  });

  setupMeldungenUI();
  setupErgebnisseUI();
}

window.addEventListener("message", (ev) => {
  const msg = ev.data;
  if (msg?.type === "results/update" || msg?.type === "results") {
    updateFooter(msg.payload);
  }
});

//Helper
function countsClass(c) {
  if (!c) return "tt-info";
  if (c.error > 0) return "tt-error";
  if (c.warn  > 0) return "tt-warn";
  if (c.hint  > 0) return "tt-hint";
  return "tt-info";
}

function mkCountsNode(c, headerText) {
  const wrap = document.createElement("div");
  if (headerText) {
    const header = document.createElement("div");
    header.style.fontWeight = "600";
    header.textContent = headerText;
    wrap.appendChild(header);
  }
  const mk = (cls, label, n) => {
    const div = document.createElement("div");
    div.className = `tt-line ${cls}`;
    div.textContent = `${n} ${label}`;
    return div;
  };
  wrap.appendChild(mk("error", "Fehler",    c?.error ?? 0));
  wrap.appendChild(mk("warn",  "Warnungen", c?.warn  ?? 0));
  wrap.appendChild(mk("hint",  "Hinweise",  c?.hint  ?? 0));
  wrap.appendChild(mk("info",  "Infos",     c?.info  ?? 0));

  // Trennlinie + Hinweis unten
  const divider = document.createElement("div");
  divider.style.borderTop = "1px solid #ddd";
  divider.style.margin = "6px 0 3px 0";
  wrap.appendChild(divider);

  const clickHint = document.createElement("div");
  clickHint.style.fontSize = "0.8rem";
  clickHint.style.color = "#666";
  clickHint.textContent = "Zum Anzeigen klicken";
  wrap.appendChild(clickHint);

  return wrap;
}

function _normSev(s) {
  s = (s || "").toLowerCase();
  return (s === "error" || s === "warn" || s === "hint" || s === "info") ? s : "info";
}
function _computeCountsFromMessages(msgs) {
  const out = { error: 0, warn: 0, hint: 0, info: 0 };
  for (const m of (msgs || [])) out[_normSev(m?.severity)]++;
  return out;
}
function _dedupeByText(msgs) {
  const seen = new Set();
  const out = [];
  for (const m of (msgs || [])) {
    const key = String(m?.text ?? "").replace(/\s+/g, " ").trim();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(m);
  }
  return out;
}

/** Effektive Counts für Header/Tooltip – berücksichtigt show_doppelte_meldungen */
function getCountsEffective(normKey, szenario = null) {
  const showDup = !!(window.APP_STATE?.flags?.show_doppelte_meldungen);
  if (showDup) {
    return szenario
      ? ResultsVM?.getCounts(normKey, szenario)
      : ResultsVM?.getCountsMainOnly(normKey);
  }
  // Deduplizieren nach angezeigtem Text (erstes Vorkommen zählt)
  const msgs = szenario
    ? (ResultsVM?.listMessages ? ResultsVM.listMessages(normKey, szenario) : [])
    : (ResultsVM?.listMessagesMainOnly ? ResultsVM.listMessagesMainOnly(normKey) : []);
  return _computeCountsFromMessages(_dedupeByText(msgs));
}

function registerCountsTooltip(selector, { getCounts, getHeaderText, predicate, priority=50, delay=120 } = {}) {
  const TT = window.Tooltip;
  if (!TT) return;
  TT.register(selector, {
    predicate: predicate || (() => true),
    content: (_ev, el) => {
      if (!ResultsVM) return "Keine Daten";
      const c = getCounts(el);
      return mkCountsNode(c, getHeaderText ? getHeaderText(el) : undefined);
    },
    className: (el) => {
      if (!ResultsVM) return "tt-info";
      const c = getCounts(el);
      return countsClass(c);
    },
    priority,
    delay
  });
}

// Register normale Berechnung
registerCountsTooltip('.results-table thead th .count-badge', {
  predicate: (el) => !!el.closest('th[data-norm-key]'),
  getCounts: (el) => {
    const th = el.closest('th[data-norm-key]');
    if (!th) return null;
    return getCountsEffective(th.dataset.normKey, null);
  },
  getHeaderText: () => "Hauptberechnung"
});

// Register Alternativen-Berechnung
registerCountsTooltip('.results-table .alt-title th[data-szenario] .count-badge', {
  predicate: (el) => !!el.closest('th[data-norm-key][data-szenario]'),
  getCounts: (el) => {
    const th = el.closest('th[data-norm-key][data-szenario]');
    if (!th) return null;
    return getCountsEffective(th.dataset.normKey, th.dataset.szenario);
  },
  getHeaderText: (el) => {
    const th  = el.closest('th[data-szenario]');
    const raw = th?.dataset.szenario;
    const nice = ResultsVM.getAltLabel(th.dataset.normKey, raw);
    return `Alternative: ${nice}`;
  }
});

// Tooltip auf Ergebnis-Zellen: "Für Details klicken"
(function(){
  const TT = window.Tooltip;
  if (!TT) return;

  // Tooltip auf Titelzeilen: "Für Info klicken"
  TT.register(
    '.results-table thead th[data-norm-key], .results-table .alt-title th[data-norm-key]',
    {
      predicate: (el) => true,
      content: () => "Für Info klicken",
      className: () => "tt-info",
      priority: 10,
      delay: 200
    }
  );

  // Tooltip auf Ergebnis-Zellen: "Für Details klicken"
  TT.register('.results-table td.value[data-openable="ergebnisse"]', {
    predicate: (el) => {
      // nur wenn sinnvoller Inhalt vorhanden & nicht als Fehler markiert
      const txt = (el.textContent || "").trim();
      if (!txt || txt === "—" || txt === "--") return false;
      return true;
    },
    content: () => "Für Details klicken",
    className: () => "tt-info",
    priority: 20,
    delay: 120
  });
})();
