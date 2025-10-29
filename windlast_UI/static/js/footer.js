// footer.js  (als ES Module laden)
import { configureMeldungen, setupMeldungenUI } from "./modal/meldungen.js";
import {
  ALT_LABELS,
  SEVERITY_ORDER,
  NORM_DISPLAY_NAMES,
  CONTEXT_ORDER,
  CONTEXT_ALIASES,
  CONTEXT_BLACKLIST,
  CONTEXT_BLACKLIST_PREFIXES,

  displayAltName,
  getNormDisplayName,
  escapeHtml,
  formatNumberDE,
  formatVectorDE,
  formatMathWithSubSup,
  formatVal,
  prettyVal,
  prettyValHTML,
  isBlacklistedKey,
  orderContextEntries,
  sortMessagesBySeverity,
} from "./utils/formatierung.js";


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

const CELL_SELECTOR = 'td[data-norm-key][data-nachweis], td.res-kipp, td.res-gleit, td.res-abhebe';

// === Zwischenergebnisse UI Handler ===

function wireZwischenergebnisseUI() {
  const root = document.querySelector(".results-table");
  if (!root) { console.warn("[ZwRes] .results-table nicht gefunden"); return; }
  // Delegation an den gemeinsamen Handler (öffnet ALLE Docs + UI-Filter)
  root.addEventListener("click", onResultCellClick, true);
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

  const docsAll = getAllDocsForModal(ctx);
  openZwischenergebnisseModal(ctx, docsAll, { initialNachweis: ctx.nachweis });
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

// === Modal ===
const NACHWEIS_CHOICES = ["ALLE", "KIPP", "GLEIT", "ABHEB", "BALLAST", "LOADS"];

function filterDocsByNachweis(docs, sel) {
  if (!sel || sel === "ALLE") return docs;
  return (docs || []).filter(d => {
    const n = d?.context?.nachweis ?? null;
    // LOADS zählen immer dazu, ebenso Docs ohne Nachweis (Meta/Allgemein)
    return n === sel || n === "LOADS" || n === null;
  });
}

// Rollen-Filterzustand als Set der aktivierten Rollen
const ROLE_FILTER_CHOICES = ["entscheidungsrelevant", "irrelevant"];

function filterDocsByRole(docs, activeRoles /* Set<string> */) {
  const getRole = d => (d?.context?.rolle ?? d?.context?.role ?? "")
    .toString().toLowerCase();

  // KEIN Chip aktiv → NUR "relevant" zeigen
  if (!activeRoles || activeRoles.size === 0) {
    return (docs || []).filter(d => getRole(d) === "relevant");
  }

  // Mind. ein Chip aktiv:
  // - "relevant" immer zeigen
  // - zusätzlich: alle ausgewählten Rollen
  // - Items ohne Rolle NICHT zeigen
  return (docs || []).filter(d => {
    const role = getRole(d);
    if (role === "relevant") return true;
    if (!role) return false;
    return activeRoles.has(role);
  });
}

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

function openZwischenergebnisseModal({ normKey, nachweis, altName }, docsAll, { initialNachweis=null } = {}) {
  // Titel exakt wie bei Meldungen bauen
  const normName = getNormDisplayName(normKey);
  const niceScenario = altName ? (displayAltName ? displayAltName(altName) : altName) : null;

  const title = altName
    ? `Zwischenergebnisse – ${normName} (${niceScenario})`
    : `Zwischenergebnisse – ${normName} (Hauptberechnung)`;

  // Gleiches Markup: <h3 class="modal-title">…</h3>
  const wrap = buildModal(title, document.createElement("div"));
  const contentRoot = wrap.lastElementChild; // unser body-Container

  // --- Nachweis-Filterleiste ---
  const bar = document.createElement("div");
  bar.className = "nachweis-filter";
  const start = (initialNachweis && NACHWEIS_CHOICES.includes(initialNachweis)) ? initialNachweis : "ALLE";
  bar.innerHTML = NACHWEIS_CHOICES.map(c =>
    `<button class="nf-chip${c===start?" active":""}" data-nachweis="${c}" aria-pressed="${c===start}">${c==="ALLE"?"Alle":c}</button>`
  ).join("");
  contentRoot.appendChild(bar);

  // --- Rollen-Filterleiste (Mehrfachauswahl) ---
  const roleBar = document.createElement("div");
  roleBar.className = "nachweis-filter";
  // beide Chips sind initial AUS (keine .active) → d.h. kein Filter aktiv
  roleBar.innerHTML = `
    <button type="button" class="nf-chip" data-role="entscheidungsrelevant" aria-pressed="false">Entscheidungsrelevant</button>
    <button type="button" class="nf-chip" data-role="irrelevant" aria-pressed="false">Irrelevant</button>
  `;
  contentRoot.appendChild(roleBar);

  // --- Ergebnisbereich ---
  const list = document.createElement("div");

  // aktueller Zustand
  let activeNachweis = (initialNachweis && ["ALLE","KIPP","GLEIT","ABHEB","BALLAST","LOADS"].includes(initialNachweis))
    ? initialNachweis : "ALLE";
  const activeRoles = new Set(); // leer = kein Rollenfilter

  const apply = () => {
    // 1) Nachweis-Filter
    const docsByNachweis = (activeNachweis && activeNachweis !== "ALLE")
      ? (docsAll || []).filter(d => {
          const n = d?.context?.nachweis ?? null;
          return n === activeNachweis || n === "LOADS" || n === null;
        })
      : docsAll;

    // 2) Rollen-Filter (Mehrfachauswahl; Relevant immer sichtbar)
    const docsFinal = filterDocsByRole(docsByNachweis, activeRoles);

    // rendern
    list.innerHTML = renderDocsByWindrichtung(docsFinal);
  };

  // initial render
  apply();
  contentRoot.appendChild(list);

  // --- Events: Nachweis Single-Select (wie gehabt) ---
  bar.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".nf-chip");
    if (!btn) return;
    bar.querySelectorAll(".nf-chip.active").forEach(b => { b.classList.remove("active"); b.setAttribute("aria-pressed","false"); });
    btn.classList.add("active");
    btn.setAttribute("aria-pressed","true");
    activeNachweis = btn.dataset.nachweis;
    apply();
  });

  // --- Events: Rolle Multi-Select (Toggle) ---
  roleBar.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".nf-chip");
    if (!btn) return;
    const role = btn.dataset.role;
    const isActive = btn.classList.toggle("active");
    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    if (isActive) activeRoles.add(role);
    else activeRoles.delete(role);
    apply();
  });

  Modal.open(wrap);
}

function formatLabelWithSubscripts(input) {
  if (input == null) return "";
  const raw = String(input);

  // Ersetze Muster:  X_y  oder  X_{y,z}  →  X<sub>y[,z]</sub>
  // - X = einzelner Buchstabe (auch griechisch), bleibt wie ist
  // - y[,z] werden kleingeschrieben (F_W → F<sub>w</sub>)
  // - alles sauber geescaped
  return raw.replace(
    /([A-Za-z\u0370-\u03FF])_(\{[^}]+\}|[^\s^_<>()]+)(?![^<]*>)/g,
    (_, base, sub) => {
      const inner = sub.startsWith("{") ? sub.slice(1, -1) : sub;
      return `${escapeHtml(base)}<sub>${escapeHtml(inner)}</sub>`;
    }
  ).replace(/(^|[^>])_([^>]|$)/g, (m) => {
    // übrige Unterstriche (keine Subscript-Pattern) entschärfen
    return m.replace("_", "&#95;");
  });
}

// === Gruppierungen ===
function groupBy(docs, { keyFn, emptyKey="__none__", sort="numeric", emptyLast=true }) {
  const groups = new Map();
  for (const d of (docs || [])) {
    const raw = keyFn(d);
    const k = (raw === undefined || raw === null || raw === "") ? emptyKey : raw;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(d);
  }

  const keys = [...groups.keys()].sort((a, b) => {
    // leeren Marker (z.B. "__none__", "__allgemein__", "__ohne_achse__") ans Ende
    if (emptyLast) {
      if (a === emptyKey && b === emptyKey) return 0;
      if (a === emptyKey) return 1;
      if (b === emptyKey) return -1;
    }

    if (sort === "alnum") {
      // numerisch, sonst localeCompare (für Element-IDs)
      const na = Number(a), nb = Number(b);
      const an = Number.isFinite(na), bn = Number.isFinite(nb);
      if (an && bn) return na - nb;
      return String(a).localeCompare(String(b), undefined, { numeric:true, sensitivity:"base" });
    }

    // default: numeric
    return Number(a) - Number(b);
  });

  return { groups, keys };
}

// Windrichtung (deg)
function _pickDir(d){
  return d?.context?.windrichtung_deg ?? null;
}  // :contentReference[oaicite:8]{index=8}

// Element-ID bevorzugt; sonst sinnvolle Fallbacks
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

// Achsindex (nur numerisch zulassen)
function _pickAxisIndex(ctx) {
  if (!ctx) return null;
  const v =
    ctx.achse_index ??    // bevorzugt (kommt in euren Kontexten vor)
    null;
  
  if (v === null || v === undefined || v === "") return null;
  if (typeof v === "boolean") return null; // Safety, falls mal true/false reinkommt

  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function renderAccordionGroup({ cardClass, detailsClass, summaryClass, title, count, bodyHtml, open=false }) {
  return `
    <div class="group-card ${cardClass}">
      <details class="${detailsClass}"${open ? " open" : ""}>
        <summary class="${summaryClass}" aria-label="${escapeHtml(title)}">${escapeHtml(title)} ${count}</summary>
        ${bodyHtml}
      </details>
    </div>
  `;
}

function renderDocsByWindrichtung(docs){
  const { groups, keys } = groupBy(docs, { keyFn: _pickDir, emptyKey:"__none__", sort:"numeric", emptyLast:true });
  if (!keys.length) {
    return `<div class="muted" style="padding:0.75rem 0;">Keine Zwischenergebnisse vorhanden.</div>`;
  }
  const blocks = keys.map((k, idx) => {
    const list = groups.get(k) || [];
    const title = (k === "__none__") ? "ohne Richtung" : `Windrichtung ${k}`;
    const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    // innerhalb jeder Richtung weiter nach Element gruppieren
    const elemGroupsHtml = renderDocsByElement(list);
    return renderAccordionGroup({
      cardClass:"dir-card", detailsClass:"dir-group", summaryClass:"dir-summary",
      title, count, bodyHtml:`<div class="elem-groups">${elemGroupsHtml}</div>`, open: idx===0
    });
  }).join("");
  return `<div class="doc-groups">${blocks}</div>`;
}

function renderDocsByElement(docsInDir){
  const { groups, keys } = groupBy(docsInDir, {
    keyFn: d => _pickElementKey(d?.context),
    emptyKey: "__allgemein__",
    sort: "alnum",
    emptyLast: true
  });

  // NEU: Wenn es ausschließlich "allgemein"-Ergebnisse gibt,
  // dann KEINE "allgemein"-Gruppe anzeigen, sondern direkt
  // die Achs-Gruppierung unter der Windrichtung rendern.
  const hasSpecificElements = keys.some(k => k !== "__allgemein__");
  if (!hasSpecificElements) {
    const onlyGeneral = groups.get("__allgemein__") || [];
    // direkt unter der Windrichtung anzeigen (mit Achs-Gruppierung)
    return `<div class="axis-groups">${renderDocsByAxis(onlyGeneral)}</div>`;
  }

  // Es gibt mind. ein spezifisches Element → normale Element-Gruppierung
  return keys.map((k, idx) => {
    const list = groups.get(k) || [];
    const title = (k === "__allgemein__") ? "allgemein" : `Element ${k}`;
    const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    const axisHtml = renderDocsByAxis(list);
    return renderAccordionGroup({
      cardClass:"elem-card", detailsClass:"elem-group", summaryClass:"elem-summary",
      title, count, bodyHtml:`<div class="elem-body"><div class="axis-groups">${axisHtml}</div></div>`, open: idx===0
    });
  }).join("");
}

function renderDocsByAxis(docs){
  const { groups, keys } = groupBy(docs, {
    keyFn: d => _pickAxisIndex(d?.context),
    emptyKey: "__ohne_achse__",
    sort: "numeric",
    emptyLast: true
  });

  const hasAxes = keys.some(k => k !== "__ohne_achse__");
  if (!hasAxes) {
    const only = groups.get("__ohne_achse__") || [];
    return `<ul class="doc-list">${renderDocsListItems(only)}</ul>`;
  }

  return keys.map((k, idx) => {
    const list = groups.get(k) || [];
    const title = (k === "__ohne_achse__") ? "ohne Achse" : `Achse ${k}`;
    const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    const body = `<ul class="doc-list">${renderDocsListItems(list)}</ul>`;
    return renderAccordionGroup({
      cardClass:"axis-card", detailsClass:"axis-group", summaryClass:"axis-summary",
      title, count, bodyHtml: body, open: idx===0
    });
  }).join("");
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

    // Rolle (relevant | entscheidungsrelevant | irrelevant) als Klasse
    const roleRaw = (d?.context?.rolle ?? d?.context?.role ?? "").toString().toLowerCase();
    const roleClass =
      roleRaw === "entscheidungsrelevant" ? "role-key" :
      roleRaw === "relevant"              ? "role-rel" :
      roleRaw === "irrelevant"            ? "role-irr" : "";
    const roleAttr = roleRaw ? ` data-rolle="${escapeHtml(roleRaw)}"` : "";

    return `
      <li class="doc-li ${roleClass}" ${dataAttr}${roleAttr}>
        <span class="doc-title">${titleHtml}</span>
        <span class="doc-eq"> = </span>
        <span class="doc-val">${val}${unitHtml}</span>
      </li>
    `;
  }).join("");
}

// NEU: holt alle Docs für Norm × (optional) Alternative – ohne Nachweis-Filter
function getAllDocsForModal({ normKey, altName=null }) {
  const norm = ResultsVM?.payload?.normen?.[normKey] || {};
  return altName ? (norm.alternativen?.[altName]?.docs || []) : (norm.docs || []);
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
    const c = ResultsVM?.getCountsMainOnly(th.dataset.normKey);
    updateHeaderBadge(th, c);
  });

  // Alternativen-Zeilen (pro Norm + Szenario)
  document.querySelectorAll(".results-table .alt-title th[data-norm-key][data-szenario]").forEach(th => {
    const c = ResultsVM?.getCounts(th.dataset.normKey, th.dataset.szenario);
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
    key === "abhebe"  ? "ABHEB"   : "";
  if (el.dataset.alt) delete el.dataset.alt;
}

function setBallastCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  // Norm/Nachweis in die Datenattribute schreiben (falls noch nicht passiert)
  try { setDatasetFromId(el, id); } catch {}

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
  refreshHeaderBadges();

  const VM = ResultsVM; // oder wie dein ViewModel bei dir heißt

  configureMeldungen({
    vm: VM,
    buildModal,
    Modal,   // falls bei dir als Objekt vorhanden
    Tooltip, // falls bei dir als Objekt vorhanden
  });

  setupMeldungenUI();
}

window.addEventListener("message", (ev) => {
  const msg = ev.data;
  if (msg?.type === "results/update" || msg?.type === "results") {
    updateFooter(msg.payload);
  }
});

// ---- Meldungs-Tooltip ----
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
  return wrap;
}

function registerCountsTooltip(selector, { getCounts, getHeaderText, predicate, priority=50, delay=120 } = {}) {
  Tooltip.register(selector, {
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
registerCountsTooltip('.results-table thead th', {
  predicate: el => !!el.dataset.normKey,
  getCounts: (el) => ResultsVM?.getCountsMainOnly(el.dataset.normKey)
});

// Register Alternativen-Berechnung
registerCountsTooltip('.results-table .alt-title th[data-szenario]', {
  predicate: el => !!el.dataset.normKey && !!el.dataset.szenario,
  getCounts: (el) => ResultsVM?.getCounts(el.dataset.normKey, el.dataset.szenario),
  getHeaderText: (el) => {
    const raw = el.dataset.szenario;
    const nice = displayAltName ? displayAltName(raw) : raw;
    return `Alternative: ${nice}`;
  }
});


// Tooltip für Zwischenergebnis-Einträge im Modal (Node-basiert => HTML möglich)
Tooltip.register('#modal-root .doc-list li', {
  predicate: (el) => {
    return !!(APP_STATE?.flags?.show_zwischenergebnisse_tooltip) && !!el.closest('li.doc-li');
  },
  content: (_ev, el) => {
    if (!APP_STATE?.flags?.show_zwischenergebnisse_tooltip) return "";
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
        vEl.innerHTML = prettyValHTML(k, v);
        row.appendChild(kEl);
        row.appendChild(vEl);
        root.appendChild(row);
      }
    }
    return root; // <- Node, Tooltip kann HTML rendern
  },
  delay: 80
});
