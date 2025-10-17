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
  "szenario", "scenario", "szenario_anzeigename",
  "windzone",
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
  szenario_anzeigename: "Szenario",
  einwirkungsart: "Einwirkungsart",
  stelle: "Stelle",
  id: "ID",
  gesamt_hoehe: "Gesamthöhe",
  gesamthoehe: "Gesamthöhe",
  h_bau: "Gesamthöhe",
  h_max: "Max. gültige Höhe",
  z_max: "Max. erlaubte Höhe",
  windzone: "Windzone",
  winkel_deg: "Windrichtung (°)",
  paarung: "Materialpaarung",
  norm_used: "Verwendete Norm",
};

// Kontext-Blacklist: diese Keys werden im Tooltip NICHT angezeigt
const CONTEXT_BLACKLIST = new Set([
  "szenario",
  "element_index",
  "element_id_intern",
]);

// Optional: per Präfix ausblenden (z.B. alles was mit "debug_" beginnt)
const CONTEXT_BLACKLIST_PREFIXES = [
  /^debug_/,
  /^internal_/,
];

const RESULTS_SELECTOR = "#results"; // ggf. anpassen an euren Container
const CELL_SELECTOR = 'td[data-norm-key][data-nachweis], td.res-kipp, td.res-gleit, td.res-abhebe';

function wireZwischenergebnisseUI() {
  const root = document.querySelector(".results-table"); // <— statt #results
  if (!root) { console.warn("[ZwRes] .results-table nicht gefunden"); return; }

  root.addEventListener("click", (e) => {
    const td = e.target.closest('td[data-norm-key][data-nachweis], td[data-alt][data-nachweis][data-norm-key]');
    if (!td) return;
    // Debug:
    console.log("[ZwRes] Klick auf Ergebniszelle", td.dataset);
    const ctx = resolveCellContext(td);
    if (!ctx) { console.warn("[ZwRes] Kein Kontext ermittelbar"); return; }
    const docs = getDocsForModal(ctx);
    openZwischenergebnisseModal(ctx, docs);
  }, true);
}

function wireZwischenergebnisseUIOnce() {
  if (window.__zwresSetup) return;
  window.__zwresSetup = true;
  wireZwischenergebnisseUI(); // deine Funktion mit addEventListener auf #results
}

function onResultCellClick(e) {
  const td = e.target.closest(CELL_SELECTOR);
  if (!td) return;
  const ctx = resolveCellContext(td);
  if (!ctx) return;

  const docs = getDocsForModal(ctx);
  openZwischenergebnisseModal(ctx, docs);
}

function resolveCellContext(td) {
  const normKey = td.dataset.normKey || td.closest('[data-norm-key]')?.dataset.normKey;
  let nachweis = td.dataset.nachweis;
  let altName  = td.dataset.alt ?? null;

  if (!nachweis) {
    if (td.classList.contains('res-kipp'))  nachweis = "KIPP";
    if (td.classList.contains('res-gleit')) nachweis = "GLEIT";
    if (td.classList.contains('res-abhebe')) nachweis = "ABHEB";
  }
  if (!altName) {
    altName = td.closest('tr[data-alt]')?.dataset.alt ?? null;
  }
  if (!normKey || !nachweis) return null;
  return { normKey, nachweis, altName };
}

function getDocsForModal({ normKey, nachweis, altName=null }) {
  const norm = ResultsVM?.payload?.normen?.[normKey] || {};
  const src = altName ? (norm.alternativen?.[altName]?.docs || []) : (norm.docs || []);
  // Filter NUR auf diesen Nachweis, Reihenfolge egal
  return src.filter(d => (d?.context?.nachweis ?? null) === nachweis);
}

function openZwischenergebnisseModal({ normKey, nachweis, altName }, docs) {
  // Titel exakt wie bei Meldungen bauen
  const normName = getNormDisplayName(normKey);
  const niceScenario = altName ? (displayAltName ? displayAltName(altName) : altName) : null;

  const title = altName
    ? `Zwischenergebnisse – ${normName} (${niceScenario})`
    : `Zwischenergebnisse – ${normName} (Hauptberechnung)`;

  // Gleiches Markup: <h3 class="modal-title">…</h3>
  const wrap = document.createElement("div");
  const h = document.createElement("h3");
  h.textContent = title;
  h.className = "modal-title";
  wrap.appendChild(h);

  // Gruppierte Ansicht: je Windrichtung ein auf-/zuklappbarer Block
  const list = document.createElement("div");
  list.innerHTML = renderDocsByWindrichtung(docs);
  wrap.appendChild(list);

  Modal.open(wrap);
}

function renderDocsSimpleList(docs) {
  if (!docs || !docs.length) {
    return `<div class="muted" style="padding:0.75rem 0;">Keine Zwischenergebnisse vorhanden.</div>`;
  }
  const lis = docs.map(d => {
    const titleHtml = escapeHtml(d?.title ?? "—");
    const val   = formatNumberDE(d?.value);
    const unitHtml  = d?.unit ? ` ${escapeHtml(String(d.unit))}` : "";

    // Für den Tooltip nur Rohdaten speichern: Formel + Kontext (JSON)
    const formula = d?.formula ? String(d.formula) : "";
    const formulaSource = d?.formula_source ? String(d?.formula_source) : "";
    const ctxJson = escapeHtml(JSON.stringify(d?.context || {}));
    const dataAttr =
      `data-formula="${escapeHtml(formula)}" ` +
      `data-formula_source="${escapeHtml(String(formulaSource))}" ` +
      `data-ctx-json="${ctxJson}"`

    return `
      <li class="doc-li" ${dataAttr}>
        <span class="doc-title">${titleHtml}</span>
        <span class="doc-eq"> = </span>
        <span class="doc-val">${val}${unitHtml}</span>
      </li>
    `;
  }).join("");

  return `<ul class="doc-list">${lis}</ul>`;
}

function formatNumber(v) {
  if (v === "INF" || v === "-INF" || v == null) return String(v);
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  return n.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function formatNumberDE(value, sig = 4) {
  if (value == null || value === "INF" || value === "-INF" || Number.isNaN(value)) return String(value);

  const num = Number(value);
  if (!Number.isFinite(num)) return String(value);

  // ➜ Ganzzahlen direkt ohne Nachkommastellen
  if (Number.isInteger(num)) {
    return num.toString(); // keine Kommata oder Nachkommastellen
  }

  // wissenschaftliche Notation auseinandernehmen
  let [mantissa, exp] = num.toExponential(sig - 1).split("e");
  exp = Number(exp);

  // Standardfall: keine Exponentialdarstellung, normale Zahl
  if (exp > -3 && exp < 4) {
    const rounded = num.toPrecision(sig);
    // Punkt durch Komma ersetzen
    return rounded.replace(".", ",");
  }

  // wissenschaftliche Darstellung →  mantissa ×10^exp
  const mant = parseFloat(mantissa).toString().replace(".", ",");
  return `${mant}×10<sup>${exp}</sup>`;
}

function formatVectorDE(vec, sig = 4) {
  if (!Array.isArray(vec)) return formatNumberDE(vec, sig);
  const parts = vec.map(v => formatNumberDE(v, sig));
  return `(${parts.join("; ")})`;
}

// Einheit hübsch anhängen (schmales Leerzeichen)
function withUnit(valStr, unit) {
  return unit ? `${valStr}\u2009${String(unit)}` : valStr;
}

function formatLabelWithSubscripts(input) {
  if (input == null) return "";
  const raw = String(input);

  // Ersetze Muster:  X_y  oder  X_{y,z}  →  X<sub>y[,z]</sub>
  // - X = einzelner Buchstabe (auch griechisch), bleibt wie ist
  // - y[,z] werden kleingeschrieben (F_W → F<sub>w</sub>)
  // - alles sauber geescaped
  return raw.replace(
    /([A-Za-z\u0370-\u03FF])_(\{[^}]+\}|[A-Za-z0-9,]+)(?![^<]*>)/g,
    (_, base, sub) => {
      const inner = sub.startsWith("{") ? sub.slice(1, -1) : sub;
      const lowered = inner.toLowerCase();
      return `${escapeHtml(base)}<sub>${escapeHtml(lowered)}</sub>`;
    }
  ).replace(/(^|[^>])_([^>]|$)/g, (m) => {
    // übrige Unterstriche (keine Subscript-Pattern) entschärfen
    return m.replace("_", "&#95;");
  });
}

function formatMathWithSubSup(input) {
  const s = String(input ?? "");
  // Wir bauen output sicher auf: zwischen Matches wird ge-escaped,
  // in den Matches escapen wir Base und Innenleben separat.
  const pattern = /([A-Za-z\u0370-\u03FF0-9])_(\{[^}]+\}|[A-Za-z0-9]+)|([A-Za-z\u0370-\u03FF0-9])\^(\{[^}]+\}|[A-Za-z0-9]+)/g;
  let out = "";
  let last = 0;

  const esc = (t) => t.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

  for (let m; (m = pattern.exec(s)); ) {
    // Text vor dem Match escapen
    out += esc(s.slice(last, m.index));
    last = pattern.lastIndex;

    if (m[1] != null) {
      // Subscript: base _ sub
      const base = m[1];
      const rawSub = m[2];
      const inner = rawSub.startsWith("{") ? rawSub.slice(1, -1) : rawSub;
      out += esc(base) + "<sub>" + esc(inner) + "</sub>";
    } else {
      // Superscript: base ^ sup
      const base = m[3];
      const rawSup = m[4];
      const inner = rawSup.startsWith("{") ? rawSup.slice(1, -1) : rawSup;
      out += esc(base) + "<sup>" + esc(inner) + "</sup>";
    }
  }
  // Rest anhängen
  out += esc(s.slice(last));
  return out;
}

function escapeHtml(s){ return String(s).replace(/[&<>"']/g,m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));   }

function buildContextTitle(ctx) {
  // sortiere Kernfelder zuerst (Analog zu euren Message-Kontext-Regeln)
  const order = ["szenario","nachweis","doc_type","windrichtung_deg","element_id","segment_index","achse_index","rolle","ref_nachweis"];
  const keys = Object.keys(ctx || {});
  keys.sort((a,b) => {
    const ia = order.indexOf(a); const ib = order.indexOf(b);
    if (ia !== -1 || ib !== -1) return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
    return a.localeCompare(b);
  });
  const parts = keys.map(k => `${k}: ${String(ctx[k])}`);
  return parts.join(" · ");
}

// --- Gruppieren nach Windrichtung ---------------------------------

function groupDocsByWindrichtung(docs) {
  const groups = new Map(); // key -> array
  for (const d of (docs || [])) {
    const dir = d?.context?.windrichtung_deg;
    const key = (dir === undefined || dir === null || dir === "") ? "__none__" : Number(dir);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(d);
  }
  // sort keys: numeric ascending, "__none__" last
  const keys = [...groups.keys()].sort((a, b) => {
    if (a === "__none__" && b === "__none__") return 0;
    if (a === "__none__") return 1;
    if (b === "__none__") return -1;
    return Number(a) - Number(b);
  });
  return { groups, keys };
}

function renderDocsListItems(docs) {
  return (docs || []).map(d => {
    const titleHtml = formatLabelWithSubscripts(d?.title ?? "—");
    // Zahl ODER Vektor formatiert; Unit separat escapen
    const isVec = Array.isArray(d?.value) ||
                  (d?.value && typeof d.value === "object" &&
                   ["x","y","z"].every(k => k in d.value));
    const val   = isVec
      ? formatVectorDE(Array.isArray(d.value) ? d.value : [d.value.x, d.value.y, d.value.z], 4)
      : formatNumberDE(d?.value, 4);
    const unitHtml = d?.unit ? ` ${escapeHtml(String(d.unit))}` : "";

    // Für den Tooltip: Rohdaten speichern
    const formula = d?.formula ? String(d.formula) : "";
    const formulaSource = d?.formula_source ? String(d?.formula_source) : "";
    const ctxJson = escapeHtml(JSON.stringify(d?.context || {}));
    const dataAttr =
      `data-formula="${escapeHtml(formula)}" ` +
      `data-formula_source="${escapeHtml(String(formulaSource))}" ` +
      `data-ctx-json="${ctxJson}"`

    return `
      <li class="doc-li" ${dataAttr}>
        <span class="doc-title">${titleHtml}</span>
        <span class="doc-eq"> = </span>
        <span class="doc-val">${val}${unitHtml}</span>
      </li>
    `;
  }).join("");
}

// Akkordeon pro Windrichtung (Details/Summary ist simpel & barrierearm)
function renderDocsByWindrichtung(docs) {
  const { groups, keys } = groupDocsByWindrichtung(docs);
  if (!keys.length) {
    return `<div class="muted" style="padding:0.75rem 0;">Keine Zwischenergebnisse vorhanden.</div>`;
  }

  const blocks = keys.map((k, idx) => {
    const list = groups.get(k) || [];
    const title = (k === "__none__") ? "ohne Richtung" : `Windrichtung ${k}°`;
    const countBadge = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    // NEU: innerhalb jeder Windrichtung nach Element-ID gruppieren
    const elemGroupsHtml = renderDocsByElement(list);

    return `
      <div class="group-card dir-card">
        <details class="dir-group"${idx === 0 ? " open" : ""}>
          <summary class="dir-summary">${escapeHtml(title)} ${countBadge}</summary>
          <div class="elem-groups">
            ${elemGroupsHtml}
          </div>
        </details>
      </div>
    `;
  }).join("");

  return `<div class="doc-groups">${blocks}</div>`;
}

// --- Sub-Gruppierung nach Element-ID (oder ähnliche Felder) -----------------
// Bevorzugte Keys im Kontext: element_id > element > bauteil > komponente
function _pickElementKey(ctx) {
  if (!ctx) return null;
  return (
    ctx.element_id ??
    ctx.element ??
    ctx.bauteil ??
    ctx.komponente ??
    null
  );
}

function groupDocsByElement(docs) {
  const groups = new Map(); // key -> array
  for (const d of (docs || [])) {
    const k = _pickElementKey(d?.context);
    const key = (k === undefined || k === null || k === "") ? "__allgemein__" : String(k);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(d);
  }
  // Sortierung: alphanumerisch, "__allgemein__" am Ende
  const keys = [...groups.keys()].sort((a, b) => {
    if (a === "__allgemein__" && b === "__allgemein__") return 0;
    if (a === "__allgemein__") return 1;
    if (b === "__allgemein__") return -1;
    // try numeric if both look like numbers, else localeCompare
    const na = Number(a), nb = Number(b);
    const an = Number.isFinite(na), bn = Number.isFinite(nb);
    if (an && bn) return na - nb;
    return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" });
  });
  return { groups, keys };
}

function renderDocsByElement(docsInDir) {
  const { groups, keys } = groupDocsByElement(docsInDir);
  const blocks = keys.map((k, idx) => {
    let list = groups.get(k) || [];
    const title = (k === "__allgemein__") ? "allgemein" : `Element ${k}`;
    const countBadge = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    // NEU: innerhalb "allgemein" noch eine Ebene nach Achse
    const innerHtml = (k === "__allgemein__")
      ? renderDocsByAxis(list)
      : `<ul class="doc-list">${renderDocsListItems(list)}</ul>`;

    return `
      <div class="group-card elem-card">
        <details class="elem-group"${idx === 0 ? " open" : ""}>
          <summary class="elem-summary">${escapeHtml(title)} ${countBadge}</summary>
          <div class="elem-body">
            <div class="axis-groups">
              ${innerHtml}
            </div>
          </div>
        </details>
      </div>
    `;
  }).join("");
  return blocks || "";
}

// ---- Achs-Index aus dem Kontext lesen (mehrere mögliche Keys absichern) ---
function _pickAxisIndex(ctx) {
  if (!ctx) return null;
  const v =
    ctx.achse_index ??    // bevorzugt (kommt in euren Kontexten vor)
    null;

  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

// --- Gruppierung nach Achse (nur für "allgemein") ---------------------------
function groupDocsByAxis(docs) {
  const groups = new Map(); // key -> array
  for (const d of (docs || [])) {
    const ax = _pickAxisIndex(d?.context);
    const key = (ax == null) ? "__ohne_achse__" : Number(ax);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(d);
  }
  const keys = [...groups.keys()].sort((a, b) => {
    if (a === "__ohne_achse__" && b === "__ohne_achse__") return 0;
    if (a === "__ohne_achse__") return 1;
    if (b === "__ohne_achse__") return -1;
    return Number(a) - Number(b);
  });
  return { groups, keys };
}

function renderDocsByAxis(docs) {
  const { groups, keys } = groupDocsByAxis(docs);
  return keys.map((k, idx) => {
    const list = groups.get(k) || [];
    const title = (k === "__ohne_achse__") ? "ohne Achse" : `Achse ${k}`;
    const countBadge = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    const lis = renderDocsListItems(list); // nutzt dein bestehendes LI-Markup
    return `
      <div class="group-card axis-card">
        <details class="axis-group"${idx === 0 ? " open" : ""}>
          <summary class="axis-summary">${escapeHtml(title)} ${countBadge}</summary>
          <ul class="doc-list">${lis}</ul>
        </details>
      </div>
    `;
  }).join("");
}

// Helper
function isBlacklistedKey(k) {
  if (!k) return false;
  if (CONTEXT_BLACKLIST.has(k)) return true;
  return CONTEXT_BLACKLIST_PREFIXES.some(rx => rx.test(k));
}

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

  // Arrays: wenn rein numerisch (2/3/… Werte) -> als Vektor ausgeben
  if (Array.isArray(v)) {
    const numeric = v.every(x => x !== null && x !== undefined && isFinite(Number(x)));
    if (numeric) return formatVectorDE(v, 4);
    return v.map((x) => prettyVal(k, x)).join(", ");
  }

  // Objekte kompakt serialisieren
  if (v && typeof v === "object") {
    try { return JSON.stringify(v); } catch { return String(v); }
  }

  // Standard: Zahlen deutsch, Rest als String
  if (typeof v === "number" || (typeof v === "string" && isFinite(Number(v)))) {
    return formatNumberDE(v, 4);
  }
  return String(v);
}


// Sortiert Kontext-Einträge: erst laut CONTEXT_ORDER, dann Rest in Quell-Reihenfolge
function orderContextEntries(ctx, pref = CONTEXT_ORDER) {
  if (!ctx || typeof ctx !== "object") return [];

  const withIndex = [];
  let i = 0;
  for (const k in ctx) {
    if (!Object.hasOwn(ctx, k)) continue;
    if (isBlacklistedKey(k)) continue;                    
    const v = ctx[k];
    if (v === undefined || v === null || v === "") continue;
    withIndex.push([k, v, i++]); // [key, value, originalIndex]
  }

  const rank = new Map(pref.map((k, idx) => [k, idx]));
  withIndex.sort((a, b) => {
    const ra = rank.has(a[0]) ? rank.get(a[0]) : Infinity;
    const rb = rank.has(b[0]) ? rank.get(b[0]) : Infinity;
    if (ra !== rb) return ra - rb;
    return a[2] - b[2];
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
  try {
    const m = /^([a-z]+)_(.+)$/.exec(id);
    if (m) {
      const suf = m[2];
      const normKey = Object.entries(NORM_ID).find(([,v]) => v === suf)?.[0] || null;
      if (normKey) el.dataset.normKey = normKey;
      el.dataset.nachweis = "BALLAST";
      if (el.dataset.alt) delete el.dataset.alt;
    }
  } catch {}
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

  
  // Kontext für den Klick-Handler setzen (normKey + nachweis)
  try {
    const m = /^([a-z]+)_(.+)$/.exec(id); // z.B. "kipp_en13814_2005"
    if (m) {
      const key = m[1];               // kipp|gleit|abhebe|ballast
      const suf = m[2];               // en13814_2005 | en17879_2024 | en1991_2010
      const normKey = Object.entries(NORM_ID).find(([,v]) => v === suf)?.[0] || null;
      if (normKey) el.dataset.normKey = normKey;
      el.dataset.nachweis =
        key === "ballast" ? "BALLAST" :
        key === "kipp"    ? "KIPP"    :
        key === "gleit"   ? "GLEIT"   :
        key === "abhebe"  ? "ABHEB"   : "";
      // Hauptzellen haben kein alt:
      if (el.dataset.alt) delete el.dataset.alt;
    }
  } catch {}

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

        // data-* für Klick-Handler
        td.dataset.normKey  = normKey;
        td.dataset.nachweis =
          row.key === "ballast" ? "BALLAST" :
          row.key === "kipp"    ? "KIPP"    :
          row.key === "gleit"   ? "GLEIT"   :
          row.key === "abhebe"  ? "ABHEB"   : "";
        if (altName) td.dataset.alt = altName;
        else delete td.dataset.alt;

        if (row.isSafety) _setSafetyOnTdAlt(td, v);
        else _setBallastOnTdAlt(td, v);

        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
  }
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

  wireZwischenergebnisseUIOnce();
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

// Tooltip für Zwischenergebnis-Einträge im Modal (Node-basiert => HTML möglich)
Tooltip.register('#modal-root .doc-list li', {
  predicate: (el) => !!el.closest('li.doc-li'),
  content: (_ev, el) => {
    const li = el.closest('li.doc-li');
    if (!li) return "";
    const formula = li.getAttribute('data-formula') || "";
    const formulaSource = li.getAttribute('data-formula_source') || "";
    let ctx = {};
    try { ctx = JSON.parse(li.getAttribute('data-ctx-json') || "{}"); } catch {}

    // Node zusammenbauen
    const root = document.createElement('div');
    root.className = 'ctx-tooltip';

    // 1) Formel (falls vorhanden) – mit Tief-/Hochstellung
    if (formula) {
      const f = document.createElement('div');
      f.className = 'ctx-formula';
      f.innerHTML = formatMathWithSubSup(formula);
      root.appendChild(f);
    }

    // 2) Quellenangabe (falls vorhanden)
    if (formulaSource) {
      const fs = document.createElement('div');
      fs.className = 'ctx-formula-source';
      fs.textContent = `Quelle: ${escapeHtml(formulaSource)}`;
      root.appendChild(fs);
    }

    // Falls es Formel/Quelle gibt, Trennlinie einfügen
    if (formula || formulaSource) {
      const divider = document.createElement("div");
      divider.className = "tt-divider";
      root.appendChild(divider);
    }

    // 3) Kontext wie bei Fehlermeldungen
    const ordered = orderContextEntries(ctx);
    if (ordered.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ctx-empty muted';
      empty.textContent = 'Kein Kontext';
      root.appendChild(empty);
    } else {
      for (const [k, v] of ordered) {
        const row = document.createElement('div');
        row.className = 'ctx-row';
        const kEl = document.createElement('span');
        kEl.className = 'ctx-k';
        kEl.textContent = prettyKey(k) + ": ";
        const vEl = document.createElement('span');
        vEl.className = 'ctx-v';
        vEl.textContent = prettyVal(k, v);
        row.appendChild(kEl);
        row.appendChild(vEl);
        root.appendChild(row);
      }
    }
    return root; // <- Node, Tooltip kann HTML rendern
  },
  delay: 80
});
