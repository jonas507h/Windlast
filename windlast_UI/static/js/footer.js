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
  const num = typeof val === "string" ? Number(val) : val;
  if (num === null || num === undefined || Number.isNaN(num)) return false;
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
      el.textContent = (Math.round(num * 100) / 100).toFixed(2);
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
    td.textContent = (Math.round(num * 100) / 100).toFixed(2);
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