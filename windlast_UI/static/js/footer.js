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
// Anzeige-Aliase für Alternativ-Namen
const ALT_LABELS = {
  IN_BETRIEB: "mit Schutzmaßnahmen",
};

// === Reihenfolge für Severity-Sortierung ===
const SEVERITY_ORDER = ["error", "warn", "hint", "info"];

// ===== Offizielle Anzeigenamen für Normen =====
const NORM_DISPLAY_NAMES = {
  EN_13814_2005: "DIN EN 13814:2005-06",
  EN_17879_2024: "DIN EN 17879:2024-08",
  EN_1991_1_4_2010: "DIN EN 1991-1-4:2010-12"
};

// Fallback, falls mal keine Zuordnung existiert
function getNormDisplayName(normKey) {
  return NORM_DISPLAY_NAMES[normKey] || normKey.replace(/_/g, " ");
}

// Wunschreihenfolge für Kontext-Felder (anpassbar)
const CONTEXT_ORDER = [
  "anzahl_windrichtungen",
  "windrichtung", "winkel_deg",
  "szenario", "scenario",
  "nachweis",
  "abschnitt",
  "phase",
  "komponente", "element", "bauteil",
  "einwirkungsart", "stelle",
  "element_index",
  "id", "element_id", "element_id_intern",
  "objekttyp",
  "objekt_name",
  "objekt_name_intern",
  "funktion",
  "norm", "norm_label",
  "methode",
];

// Anzeigenamen/Aliase für Kontext-Keys
const CONTEXT_ALIASES = {
  funktion: "Funktion",
  norm: "Norm",
  nachweis: "Nachweis",
  abschnitt: "Abschnitt",
  komponente: "Komponente",
  element: "Element",
  bauteil: "Bauteil",
  element_id: "Element-ID",
  element_id_intern: "Element-ID (intern)",
  bodenplatte_name_intern: "Bodenplatte",
  szenario: "Szenario",
  scenario: "Szenario",
  einwirkungsart: "Einwirkungsart",
  stelle: "Stelle",
  id: "ID",
  gesamt_hoehe: "Gesamthöhe",
  gesamthoehe: "Gesamthöhe",
  h_bau: "Gesamthöhe",
  h_max: "Max. gültige Höhe",
  windzone: "Windzone",
  winkel_deg: "Windrichtung (°)",
  paarung: "Materialpaarung",
  norm_used: "Verwendete Norm",
};

// Key → hübscher Labeltext
function prettyKey(k) {
  if (!k || typeof k !== "string") return String(k);
  if (CONTEXT_ALIASES[k]) return CONTEXT_ALIASES[k];
  // snake_case → "Snake Case" (erstes Zeichen jedes Wortes groß)
  return k.replace(/_/g, " ").replace(/\b\p{L}/gu, (c) => c.toUpperCase());
}

// Werte ggf. hübscher darstellen
function prettyVal(k, v) {
  if (v === null || v === undefined) return "—";

  // Norm-Schlüssel hübsch machen, falls im Kontext als Key "norm" steckt
  /*if ((k === "norm" || k === "norm_used") && typeof v === "string") {
    return getNormDisplayName(v);
  }*/

  // Szenario-Namen ggf. durch ALT_LABELS mappen
  if ((k === "szenario" || k === "scenario") && typeof v === "string") {
    return displayAltName(v) || v;
  }

  // Booleans auf Deutsch
  if (typeof v === "boolean") return v ? "Ja" : "Nein";

  // Arrays als kommagetrennte Liste
  if (Array.isArray(v)) return v.map((x) => prettyVal(k, x)).join(", ");

  // Objekte kompakt serialisieren
  if (v && typeof v === "object") {
    try { return JSON.stringify(v); } catch { return String(v); }
  }

  // Standard: Wert direkt
  return String(v);
}


// Sortiert Kontext-Einträge: erst laut CONTEXT_ORDER, dann Rest in Quell-Reihenfolge
function orderContextEntries(ctx, pref = CONTEXT_ORDER) {
  if (!ctx || typeof ctx !== "object") return [];

  // Quell-Reihenfolge sichern (stabil, kein Object.entries mit Sort)
  const withIndex = [];
  let i = 0;
  for (const k in ctx) {
    if (!Object.hasOwn(ctx, k)) continue;
    withIndex.push([k, ctx[k], i++]); // [key, value, originalIndex]
  }

  const rank = new Map(pref.map((k, idx) => [k, idx]));
  withIndex.sort((a, b) => {
    const ra = rank.has(a[0]) ? rank.get(a[0]) : Infinity;
    const rb = rank.has(b[0]) ? rank.get(b[0]) : Infinity;
    if (ra !== rb) return ra - rb;     // bevorzugte zuerst
    return a[2] - b[2];                // Originalreihenfolge unter gleicher Priorität
  });

  return withIndex.map(([k, v]) => [k, v]);
}

let ResultsVM = null; // hält das von ResultsIndex.build(...) erzeugte ViewModel

function attachNormKeysToHeader() {
  // ordnet thead-ths der COLS-Reihenfolge zu
  const ths = document.querySelectorAll('.results-table thead th');
  // th[0] ist der Stub "Nachweis"
  for (let i = 1; i < ths.length && i <= COLS.length; i++) {
    const th = ths[i];
    th.dataset.normKey = COLS[i - 1]; // "EN_13814_2005" etc.
  }
}

function displayAltName(name) {
  return (name && ALT_LABELS[name]) || name || "";
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

  // > 1000 kg -> in kg, Mindestschritt 10 kg, immer aufrunden
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

function setBallastCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = formatBallast(val);
  el.title = "";
}

function setCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;

  // Text setzen
  if (val === "INF" || val === "-INF") {
    el.textContent = val === "INF" ? "∞" : "−∞";
    el.title = "";
  } else {
    const num = typeof val === "string" ? Number(val) : val;
    if (num === null || num === undefined || Number.isNaN(num)) {
      el.textContent = "—";
      el.title = "";
    } else {
      el.textContent = (Math.floor(num * 100) / 100).toFixed(2);
      el.title = "";
    }
  }

  // Klasse setzen (grün/rot)
  klassifizierung_anwenden(el, sicherheit_klassifizieren(val));
}

// --- NEU: Helpers für dynamisch erzeugte Zellen (Alternativen) ---
function _clearAltRows() {
  const tbody = document.querySelector(".results-table tbody");
  if (!tbody) return;
  tbody.querySelectorAll('tr[data-alt-row="1"]').forEach(tr => tr.remove());
}

function _setSafetyOnTdAlt(td, val) {
  // Alternative: fehlende Werte -> leer & keine Klasse
  if (val === "INF" || val === "-INF") {
    td.textContent = val === "INF" ? "∞" : "−∞";
    klassifizierung_anwenden(td, sicherheit_klassifizieren(val));
    return;
  }
  const num = typeof val === "string" ? Number(val) : val;
  if (num === null || num === undefined || Number.isNaN(num)) {
    td.textContent = "";
    td.title = "";
    td.classList.remove("val-ok", "val-bad");
  } else {
    td.textContent = (Math.floor(num * 100) / 100).toFixed(2);
    td.title = "";
    klassifizierung_anwenden(td, sicherheit_klassifizieren(num));
  }
}

function _setBallastOnTdAlt(td, valKg) {
  // Alternative: fehlende Werte -> leer & keine Klasse
  if (valKg === null || valKg === undefined) {
    td.textContent = "";
    td.title = "";
    td.classList.remove("val-ok", "val-bad");
    return;
  }
  if (typeof valKg === "string" && Number.isNaN(Number(valKg))) {
    td.textContent = "";
    td.title = "";
    td.classList.remove("val-ok", "val-bad");
    return;
  }
  td.textContent = formatBallast(valKg);
  td.title = "";
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
      th.textContent = displayAltName(rawName);
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

        if (row.isSafety) _setSafetyOnTdAlt(td, v);
        else _setBallastOnTdAlt(td, v);

        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
  }
}

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
}

window.addEventListener("message", (ev) => {
  const msg = ev.data;
  if (msg?.type === "results/update" || msg?.type === "results") {
    updateFooter(msg.payload);
  }
});

// ---- Tooltip: Summen pro Norm im Kopf anzeigen ----
// normale Berechnung
Tooltip.register('.results-table thead th', {
  predicate: el => !!el.dataset.normKey,  // nur echte Norm-Spalten
  content: (_ev, el) => {
    const key = el.dataset.normKey;
    if (!ResultsVM) return "Keine Daten";

    const c = ResultsVM.getCountsMainOnly(key); // Gesamt je Norm
    // hübsches Node bauen (mehrzeilig, gut lesbar)
    const wrap = document.createElement("div");
    const mk = (cls, label, n) => {
      const div = document.createElement("div");
      div.className = `tt-line ${cls}`;
      div.textContent = `${n} ${label}`;
      return div;
    };
    wrap.appendChild(mk("error", "Fehler",    c.error));
    wrap.appendChild(mk("warn",  "Warnungen", c.warn));
    wrap.appendChild(mk("hint",  "Hinweise",  c.hint));
    wrap.appendChild(mk("info",  "Infos",     c.info));
    return wrap;
  },
  // Rahmenfarbe = gravierendste vorhandene Meldung
  className: el => {
    const key = el?.dataset?.normKey;
    if (!ResultsVM || !key) return "tt-info";
    const c = ResultsVM.getCountsMainOnly(key);
    if (c.error > 0) return "tt-error";
    if (c.warn  > 0) return "tt-warn";
    if (c.hint  > 0) return "tt-hint";
    return "tt-info";
  },
  priority: 50,
  delay: 120
});

// Alternativen-Berechnung
Tooltip.register('.results-table .alt-title th[data-szenario]', {
  predicate: el => !!el.dataset.normKey && !!el.dataset.szenario,
  content: (_ev, el) => {
    if (!ResultsVM) return "Keine Daten";
    const normKey = el.dataset.normKey;
    const szenario = el.dataset.szenario;

    const c = ResultsVM.getCounts(normKey, szenario); // nur diese Alternative
    // hübsches Node mit 4 Zeilen zurückgeben
    const wrap = document.createElement("div");
    const header = document.createElement("div");
    header.style.fontWeight = "600";
    header.textContent = displayAltName ? `Alternative: ${displayAltName(szenario)}` : `Alternative: ${szenario}`;
    wrap.appendChild(header);

    const mk = (cls, label, n) => {
      const div = document.createElement("div");
      div.className = `tt-line ${cls}`;
      div.textContent = `${n} ${label}`;
      return div;
    };
    wrap.appendChild(mk("error", "Fehler",    c.error));
    wrap.appendChild(mk("warn",  "Warnungen", c.warn));
    wrap.appendChild(mk("hint",  "Hinweise",  c.hint));
    wrap.appendChild(mk("info",  "Infos",     c.info));
    return wrap;
  },
  // Rahmenfarbe = gravierendste vorhandene Meldung
  className: (el) => {
    if (!ResultsVM) return "tt-info";
    const normKey = el?.dataset?.normKey;
    const szenario = el?.dataset?.szenario;
    if (!normKey || !szenario) return "tt-info";
    const c = ResultsVM.getCounts(normKey, szenario);
    if (c.error > 0) return "tt-error";
    if (c.warn  > 0) return "tt-warn";
    if (c.hint  > 0) return "tt-hint";
    return "tt-info";
  },
  priority: 50,
  delay: 120
});

function sortMessagesBySeverity(msgs) {
  return [...msgs].sort((a, b) => {
    const sa = (a.severity || "").toLowerCase();
    const sb = (b.severity || "").toLowerCase();
    const ia = SEVERITY_ORDER.indexOf(sa);
    const ib = SEVERITY_ORDER.indexOf(sb);
    // unbekannte Severities hängen wir ans Ende
    const ra = ia >= 0 ? ia : SEVERITY_ORDER.length;
    const rb = ib >= 0 ? ib : SEVERITY_ORDER.length;
    return ra - rb;
  });
}

// ---- Messages im Modal rendern (Texte; Kontext wird als Tooltip gezeigt) ----
function openMessagesModalFor(normKey, szenario = null) {
  if (!ResultsVM) return;

  // Meldungen holen (Objekte; s.o.)
  const msgs = szenario
    ? (ResultsVM.listMessages ? ResultsVM.listMessages(normKey, szenario) : [])
    : (ResultsVM.listMessagesMainOnly ? ResultsVM.listMessagesMainOnly(normKey) : []);
  const sortedMsgs = sortMessagesBySeverity(msgs);

  // Normname hübsch machen
  const normName = getNormDisplayName(normKey);
  const niceScenario = szenario ? (displayAltName ? displayAltName(szenario) : szenario) : null;

  const title = szenario
    ? `Meldungen – ${normName} (${niceScenario})`
    : `Meldungen – ${normName} (Hauptberechnung)`;

  // DOM für Modal
  const wrap = document.createElement("div");
  const h = document.createElement("h3");
  h.textContent = title;
  h.className = "modal-title";
  wrap.appendChild(h);

  if (!msgs || msgs.length === 0) {
    const p = document.createElement("p");
    p.textContent = "Keine Meldungen vorhanden.";
    wrap.appendChild(p);
  } else {
    const ul = document.createElement("ul");
    ul.className = "messages-list";
    for (const m of sortedMsgs) {
      const li = document.createElement("li");

      const line = document.createElement("div");
      const sev = (m.severity || "").toLowerCase();
      const sevClass = (sev === "error" || sev === "warn" || sev === "hint" || sev === "info")
        ? sev
        : "info"; // Fallback
      line.className = `tt-line ${sevClass}`;
      line.textContent = m.text || "";
      li.appendChild(line);

      // Kontext generisch sammeln -> Tooltip-Attribut
      // Kontext generisch, nach CONTEXT_ORDER, Rest in Quell-Reihenfolge
      let ctxText = "";
      try {
        const ctx = m?.context || {};
        const ordered = orderContextEntries(ctx);
        const parts = ordered.map(([k, v]) => {
          const label = prettyKey(k);
          const val   = prettyVal(k, v);
          return `${label}: ${val}`;
        });

        // "code" anhängen, wenn noch nicht enthalten
        if (m.code && !parts.some(line => /^\s*code\s*:/.test(line))) {
          parts.push(`code: ${m.code}`);
        }

        if (parts.length) ctxText = parts.join("\n");
      } catch {
        ctxText = JSON.stringify(m?.context || {});
      }

      if (ctxText) {
        li.setAttribute("data-ctx", ctxText);
      }

      ul.appendChild(li);
    }
    wrap.appendChild(ul);
  }

  Modal.open(wrap);
}

// ---- Modal-Trigger: beim Klick auf die Tooltip-Zellen ein Modal öffnen ----
(function setupMessageModalOnce(){
  if (window.__messageModalSetup) return;
  window.__messageModalSetup = true;

  document.addEventListener("click", (ev) => {
    const target = ev.target;

    // 1) Kopfzellen je Norm
    const thHead = target.closest(".results-table thead th");
    if (thHead && thHead.dataset && thHead.dataset.normKey) {
      const normKey = thHead.dataset.normKey;
      openMessagesModalFor(normKey, null); // Hauptberechnung
      return;
    }

    // 2) Alternativ-Titelzellen
    const thAlt = target.closest(".results-table .alt-title th[data-szenario]");
    if (thAlt) {
      const normKey  = thAlt.dataset.normKey;
      const szenario = thAlt.dataset.szenario;
      openMessagesModalFor(normKey, szenario); // spezifische Variante
      return;
    }
  }, { passive: true });
})();

// Tooltip für Meldungseinträge im Modal: zeigt den Kontext
Tooltip.register('#modal-root .messages-list li[data-ctx]', {
  // wichtig: auch Treffer auf Kindelementen zulassen
  predicate: (el) => !!el.closest('li[data-ctx]'),
  content: (_ev, el) => {
    const li = el.closest('li[data-ctx]');
    return li ? (li.getAttribute('data-ctx') || "") : "";
  },
  delay: 80
});
