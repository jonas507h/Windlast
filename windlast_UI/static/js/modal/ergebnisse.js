// modal/ergebnisse.js  (ES module)

import {
    escapeHtml,
    formatNumberDE,
    formatVectorDE,
    getNormDisplayName,
    displayAltName,
    orderContextEntries,
    prettyKey,
    prettyValHTML,
    formatMathWithSubSup,
} from "../utils/formatierung.js";

// === Konfiguration der Gruppierung der Zwischenergebnisse ===
// Format: [merkmalKeyAusContext, labelFürFehlendeWerte]
const DOC_GROUP_CONFIG = [
  ["windrichtung_deg", "ohne Richtung"],
  ["element_id",       "allgemein"],
  ["achse_index",      "ohne Achse"],
  ["zone",             "ohne Zone"],
  ["segment_index",    "kein Segment"],
];

// === Filter: Nachweis & Rollen ===
const NACHWEIS_CHOICES = ["ALLE", "KIPP", "GLEIT", "ABHEBE", "BALLAST", "LOADS", "BASIS"];
const NACHWEIS_LABELS = {
  "ALLE":   "Alle",
  "KIPP":   "Kippen",
  "GLEIT":  "Gleiten",
  "ABHEBE":  "Abheben",
  "BALLAST":"Ballast",
  "LOADS":  "Kräfte",
  "BASIS":  "Basis",
};
const ROLE_ORDER = { relevant: 3, entscheidungsrelevant: 2, irrelevant: 1 };

function isDocVisibleInNachweisView(ctx, sel) {
  const n = ctx?.nachweis ?? null;

  // "ALLE" sieht alles
  if (!sel || sel === "ALLE") return true;

  // Spezialsicht: BASIS – nur BASIS selbst
  if (sel === "BASIS") {
    return n === "BASIS";
  }

  // Spezialsicht: LOADS – nur LOADS + BASIS (wie bisher)
  if (sel === "LOADS") {
    return n === "LOADS" || n === "BASIS";
  }

  // Normale Nachweise: KIPP, GLEIT, ABHEBE, BALLAST
  // → eigene Docs + globale BASIS/LOADS + nachweislose Meta-Docs
  if (n === sel) return true;
  if (n === "BASIS") return true;
  if (n === "LOADS") return true;
  if (n === null) return true; // Meta-Daten ohne eigenen Nachweis

  // Alles andere (z.B. GLEIT-Docs in KIPP-Sicht) raus
  return false;
}

function filterDocsByNachweis(docs, sel) {
  if (!sel || sel === "ALLE") return docs || [];

  // LOADS-Sicht: nur LOADS + BASIS
  if (sel === "LOADS") {
    return (docs || []).filter(d => {
      const n = d?.context?.nachweis ?? null;
      return (n === "LOADS") || (n === "BASIS");
    });
  }

  // Spezialsicht: BASIS
  if (sel === "BASIS") {
    return (docs || []).filter(d => {
      const n = d?.context?.nachweis ?? null;
      return n === "BASIS";
    });
  }

  // Spezialsicht: BALLAST
  if (sel === "BALLAST") {
    return (docs || []).filter(d => {
      const ctx    = d?.context || {};
      const relMap = ctx.rolle_pro_nachweis || ctx.relevanz_pro_nachweis || null;

      // „alles zulassen im Rahmen der Relevanz für den Ballast“
      // ⇒ Doc gehört in die BALLAST-Sicht, wenn es dort überhaupt eine Rolle hat.
      if (relMap && typeof relMap === "object") {
        return Object.prototype.hasOwnProperty.call(relMap, "BALLAST");
      }

      // Fallback für ganz alte Daten ohne Map:
      const n = ctx.nachweis ?? null;
      if (n === "BALLAST") return true;
      if (n === "BASIS" || n === "LOADS" || n === null) return true;
      return false;
    });
  }

  // Normale Nachweise: KIPP, GLEIT, ABHEBE
  return (docs || []).filter(d => {
    const ctx    = d?.context || {};
    const relMap = ctx.rolle_pro_nachweis || ctx.relevanz_pro_nachweis || null;
    const n      = ctx.nachweis ?? null;

    // Nur Docs aus dem „passenden“ Nachweis-Kontext zulassen,
    // plus globale Dinge (BASIS/LOADS/Meta)
    if (!(n === sel || n === "BASIS" || n === "LOADS" || n === null)) {
      return false;
    }

    // Wenn es eine explizite Rollen-Angabe pro Nachweis gibt,
    // gehört das Doc nur dann in die Sicht, wenn der Nachweis im Map auftaucht.
    if (relMap && typeof relMap === "object") {
      return Object.prototype.hasOwnProperty.call(relMap, sel);
    }

    // Fallback für alte / meta-Daten (ohne rollen_map):
    if (n === sel) return true;
    if (n === "LOADS" || n === "BASIS" || n === null) return true;

    return false;
  });
}

// Liefert die Rolle eines Docs für einen gewählten Nachweis.
// Für "ALLE" oder fehlende rolle_pro_nachweis wird ein sinnvoller Fallback gewählt.
function getRoleForNachweis(d, nachweisSel) {
  const ctx = d?.context || {};
  const relMap = ctx.rolle_pro_nachweis || ctx.relevanz_pro_nachweis || null;

  // Konkrete Nachweis-Sicht
  if (nachweisSel && nachweisSel !== "ALLE" && relMap && relMap[nachweisSel] != null) {
    return String(relMap[nachweisSel]).toLowerCase();
  }

  // "ALLE"-Sicht oder keine explizite Zuordnung zu nachweisSel:
  // Wenn mehrere Rollen existieren, nimm die "stärkste".
  if (relMap && typeof relMap === "object") {
    let best = "";
    let bestScore = 0;
    for (const val of Object.values(relMap)) {
      const role = String(val || "").toLowerCase();
      const score = ROLE_ORDER[role] || 0;
      if (score > bestScore) {
        bestScore = score;
        best = role;
      }
    }
    if (best) return best;
  }

  // Fallback: alte Felder rolle / role (für Übergangsphase)
  const legacy = (ctx.rolle ?? ctx.role ?? "").toString().toLowerCase();
  return legacy;
}

function filterDocsByRole(docs, nachweisSel, activeRoles /* Set<string> */) {
  // KEIN Chip aktiv → NUR "relevant" zeigen
  if (!activeRoles || activeRoles.size === 0) {
    return (docs || []).filter(d => getRoleForNachweis(d, nachweisSel) === "relevant");
  }

  // Mind. ein Chip aktiv:
  // - "relevant" immer zeigen
  // - zusätzlich: alle ausgewählten Rollen
  // - Items ohne Rolle NICHT zeigen
  return (docs || []).filter(d => {
    const role = getRoleForNachweis(d, nachweisSel);
    if (role === "relevant") return true;
    if (!role) return false;
    return activeRoles.has(role);
  });
}

// ── Dependencies (per DI setzen, weil ResultsVM nicht global ist)
let DEPS = {
  getVM: null,     // () => ResultsVM-Objekt
  Modal: null,     // optional, sonst window.Modal
  Tooltip: null,   // optional, sonst window.Tooltip
  buildModal: null // optional Fallback
};

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
}

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

function getGroupValueFromContext(doc, key) {
  const ctx = doc?.context || {};

  switch (key) {
    case "windrichtung_deg":
      return _pickDir(doc);              // wie bisher
    case "element_id":
      return _pickElementKey(ctx);       // nutzt alle Fallbacks
    case "achse_index":
      return _pickAxisIndex(ctx);        // numeric only
    default:
      // generischer Fallback: direkt aus dem Kontext lesen
      return (ctx[key] !== undefined) ? ctx[key] : null;
  }
}

// Sortierstrategie je Merkmal
function inferSortForGroupKey(key) {
  if (key === "element_id") return "alnum";
  // Default: numerisch (wie Windrichtung/Achse)
  return "numeric";
}

// Titeltext je Gruppenschlüssel
function buildGroupTitle(key, value) {
  if (value === null || value === undefined || value === "") return "";

  if (key === "windrichtung_deg") {
    return `Windrichtung ${value}`;
  }
  if (key === "element_id") {
    return `Element ${value}`;
  }
  if (key === "achse_index") {
    return `Achse ${value}`;
  }

  // generischer Fallback
  const niceKey = prettyKey(key); // z.B. "windrichtung_deg" → "Windrichtung deg"
  return `${niceKey} ${value}`;
}

// CSS-Klassen pro Ebene (für existierende Styles)
const GROUP_LEVEL_CLASSES = [
  { card: "dir-card",  details: "dir-group",  summary: "dir-summary"  }, // Ebene 0
  { card: "elem-card", details: "elem-group", summary: "elem-summary" }, // Ebene 1
  { card: "axis-card", details: "axis-group", summary: "axis-summary" }, // Ebene 2
];

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

function renderDocsGrouped(docs, nachweisSel, groupConfig = DOC_GROUP_CONFIG, level = 0) {
  // Keine Gruppierung konfiguriert → einfach Liste ausgeben
  if (!groupConfig || groupConfig.length === 0 || level >= groupConfig.length) {
    return `<ul class="doc-list">${renderDocsListItems(docs, nachweisSel)}</ul>`;
  }

  const [key, emptyLabel] = groupConfig[level];
  const emptyKey = `__empty_${key}__`;
  const sort = inferSortForGroupKey(key);

  const { groups, keys } = groupBy(docs, {
    keyFn: d => getGroupValueFromContext(d, key),
    emptyKey,
    sort,
    emptyLast: true
  });

  if (!keys.length) {
    // gar nichts da
    if (level === 0) {
      return `<div class="muted" style="padding:0.75rem 0;">Keine Zwischenergebnisse vorhanden.</div>`;
    }
    return "";
  }

  // Wenn es nur die "leere" Gruppe gibt → Ebene überspringen, tiefer gehen
  const hasNonEmpty = keys.some(k => k !== emptyKey);
  if (!hasNonEmpty) {
    const only = groups.get(emptyKey) || [];
    return renderDocsGrouped(only, nachweisSel, groupConfig, level + 1);
  }

  const blocks = keys.map((k, idx) => {
    const list = groups.get(k) || [];
    const title = (k === emptyKey) ? emptyLabel : buildGroupTitle(key, k);
    const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
    const bodyHtml = renderDocsGrouped(list, nachweisSel, groupConfig, level + 1);

    const cls = GROUP_LEVEL_CLASSES[level] || {};
    const cardClass    = cls.card    || `lvl-${level}-card`;
    const detailsClass = cls.details || `lvl-${level}-group`;
    const summaryClass = cls.summary || `lvl-${level}-summary`;

    return renderAccordionGroup({
      cardClass,
      detailsClass,
      summaryClass,
      title,
      count,
      bodyHtml,
      open: idx === 0
    });
  }).join("");

  // Oberste Ebene bekommt wie bisher einen Wrapper
  if (level === 0) {
    return `<div class="doc-groups">${blocks}</div>`;
  }

  return blocks;
}

// function renderDocsByWindrichtung(docs, nachweisSel){
//   const { groups, keys } = groupBy(docs, { keyFn: _pickDir, emptyKey:"__none__", sort:"numeric", emptyLast:true });
//   if (!keys.length) {
//     return `<div class="muted" style="padding:0.75rem 0;">Keine Zwischenergebnisse vorhanden.</div>`;
//   }
//   const blocks = keys.map((k, idx) => {
//     const list = groups.get(k) || [];
//     const title = (k === "__none__") ? "ohne Richtung" : `Windrichtung ${k}`;
//     const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
//     // innerhalb jeder Richtung weiter nach Element gruppieren
//     const elemGroupsHtml = renderDocsByElement(list, nachweisSel); // ← nachweisSel durchreichen
//     return renderAccordionGroup({
//       cardClass:"dir-card", detailsClass:"dir-group", summaryClass:"dir-summary",
//       title, count, bodyHtml:`<div class="elem-groups">${elemGroupsHtml}</div>`, open: idx===0
//     });
//   }).join("");
//   return `<div class="doc-groups">${blocks}</div>`;
// }

// function renderDocsByElement(docsInDir, nachweisSel){
//   const { groups, keys } = groupBy(docsInDir, {
//     keyFn: d => _pickElementKey(d?.context),
//     emptyKey: "__allgemein__",
//     sort: "alnum",
//     emptyLast: true
//   });

//   const hasSpecificElements = keys.some(k => k !== "__allgemein__");
//   if (!hasSpecificElements) {
//     const onlyGeneral = groups.get("__allgemein__") || [];
//     return `<div class="axis-groups">${renderDocsByAxis(onlyGeneral, nachweisSel)}</div>`; // ← weiterreichen
//   }

//   return keys.map((k, idx) => {
//     const list = groups.get(k) || [];
//     const title = (k === "__allgemein__") ? "allgemein" : `Element ${k}`;
//     const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
//     const axisHtml = renderDocsByAxis(list, nachweisSel); // ← weiterreichen
//     return renderAccordionGroup({
//       cardClass:"elem-card", detailsClass:"elem-group", summaryClass:"elem-summary",
//       title, count, bodyHtml:`<div class="elem-body"><div class="axis-groups">${axisHtml}</div></div>`, open: idx===0
//     });
//   }).join("");
// }

// function renderDocsByAxis(docs, nachweisSel){
//   const { groups, keys } = groupBy(docs, {
//     keyFn: d => _pickAxisIndex(d?.context),
//     emptyKey: "__ohne_achse__",
//     sort: "numeric",
//     emptyLast: true
//   });

//   const hasAxes = keys.some(k => k !== "__ohne_achse__");
//   if (!hasAxes) {
//     const only = groups.get("__ohne_achse__") || [];
//     return `<ul class="doc-list">${renderDocsListItems(only, nachweisSel)}</ul>`;
//   }

//   return keys.map((k, idx) => {
//     const list = groups.get(k) || [];
//     const title = (k === "__ohne_achse__") ? "ohne Achse" : `Achse ${k}`;
//     const count = `<span class="muted" style="font-weight:400; margin-left:.5rem;">(${list.length})</span>`;
//     const body = `<ul class="doc-list">${renderDocsListItems(list, nachweisSel)}</ul>`;
//     return renderAccordionGroup({
//       cardClass:"axis-card", detailsClass:"axis-group", summaryClass:"axis-summary",
//       title, count, bodyHtml: body, open: idx===0
//     });
//   }).join("");
// }

function renderDocsListItems(docs, nachweisSel) {
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
      `data-ctx-json="${ctxJson}"`;

    // Rolle (relevant | entscheidungsrelevant | irrelevant) als Klasse
    // → jetzt nach ausgewähltem Nachweis
    const roleRaw = getRoleForNachweis(d, nachweisSel);  // <— NEU
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

export function configureErgebnisse({ vm, getVM, Modal, Tooltip, buildModal } = {}) {
  DEPS.getVM = getVM || (vm ? () => vm : DEPS.getVM);
  if (Modal) DEPS.Modal = Modal;
  if (Tooltip) DEPS.Tooltip = Tooltip;
  if (buildModal) DEPS.buildModal = buildModal;
}

function _fallbackBuildModal(titleText, bodyNodeOrHtml) {
  const wrap = document.createElement("div");
  const h = document.createElement("h3");
  h.textContent = titleText;
  h.className = "modal-title";
  wrap.appendChild(h);

  const cont = document.createElement("div");
  if (typeof bodyNodeOrHtml === "string") cont.innerHTML = bodyNodeOrHtml;
  else if (bodyNodeOrHtml instanceof Node) cont.appendChild(bodyNodeOrHtml);
  wrap.appendChild(cont);
  return wrap;
}

// Öffnet das Ergebnis-Modal (Haupt- oder Szenario-Berechnung)
export function openErgebnisseModal(normKey, szenario = null, { initialNachweis = null } = {}) {
  const VM = DEPS.getVM?.();
  if (!VM) return;

  const normName = getNormDisplayName(normKey);
  const niceScenario = szenario ? displayAltName(szenario) : null;
  const title = szenario
    ? `Ergebnisse – ${normName} (${niceScenario})`
    : `Ergebnisse – ${normName} (Hauptberechnung)`;

  // Daten holen
  const norm = VM?.payload?.normen?.[normKey] || {};
  const items = szenario ? (norm.alternativen?.[szenario]?.docs || []) : (norm.docs || []);

  const buildModal = DEPS.buildModal || _fallbackBuildModal;
  const wrap = buildModal(title, document.createElement("div"));
  const root = wrap.lastElementChild;

  // --- Fragezeichen-Button ---
  const titleEl = wrap.querySelector(".modal-title");
  if (titleEl) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "help-icon-btn";
    btn.style.marginLeft = "8px";
    btn.textContent = "?";

    const helpId = `zwischenergebnis:allgemein`;

    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      ev.preventDefault();
      if (window.HELP?.open) {
        window.HELP.open(helpId);
      }
    });

    // Button in den Titel hängen
    titleEl.appendChild(btn);
  }

  if (!items.length) {
    const p = document.createElement("p");
    p.textContent = "Keine Ergebnisse vorhanden.";
    root.appendChild(p);
    (DEPS.Modal || window.Modal)?.open(wrap);
    return;
  }

  // --- Filterleiste (Nachweis) mit initialNachweis aus Klick ---
  const bar = document.createElement("div");
  bar.className = "nachweis-filter";
  const start = (initialNachweis && ["ALLE","KIPP","GLEIT","ABHEBE","BALLAST","BASIS","LOADS"].includes(initialNachweis))
    ? initialNachweis : "ALLE";
  bar.innerHTML = NACHWEIS_CHOICES.map(c => {
  const label = NACHWEIS_LABELS[c] ?? c;  // Fallback auf Key, falls mal was fehlt
  const isActive = c === start;
  return `<button class="nf-chip${isActive ? " active" : ""}"
                  data-nachweis="${c}"
                  aria-pressed="${isActive}">${label}</button>`;
}).join("");
  root.appendChild(bar);

  // --- Rollen-Filterleiste (Multi) ---
  const roleBar = document.createElement("div");
  roleBar.className = "nachweis-filter";
  roleBar.innerHTML = `
    <button type="button" class="nf-chip" data-role="entscheidungsrelevant" aria-pressed="false">Entscheidungsrelevant</button>
    <button type="button" class="nf-chip" data-role="irrelevant" aria-pressed="false">Irrelevant</button>
  `;
  root.appendChild(roleBar);

  // --- Ergebnis-Container ---
  const listWrap = document.createElement("div");
  root.appendChild(listWrap);

  // Zustand + Apply
  let activeNachweis = start;
  const activeRoles = new Set(); // leer ⇒ nur "relevant"
  const apply = () => {
    const byNachweis = filterDocsByNachweis(items, activeNachweis);
    const finalDocs  = filterDocsByRole(byNachweis, activeNachweis, activeRoles);
    listWrap.innerHTML = renderDocsGrouped(finalDocs, activeNachweis, DOC_GROUP_CONFIG);
  };

  apply();

  // Events
  bar.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".nf-chip");
    if (!btn) return;
    bar.querySelectorAll(".nf-chip.active").forEach(b => { b.classList.remove("active"); b.setAttribute("aria-pressed","false"); });
    btn.classList.add("active");
    btn.setAttribute("aria-pressed","true");
    activeNachweis = btn.dataset.nachweis;
    apply();
  });

  roleBar.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".nf-chip");
    if (!btn) return;
    const role = btn.dataset.role;
    const isActive = btn.classList.toggle("active");
    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    if (isActive) activeRoles.add(role); else activeRoles.delete(role);
    apply();
  });

  (DEPS.Modal || window.Modal)?.open(wrap);
registerErgebnisseContextTooltip();
}

// Tooltip nur innerhalb des Ergebnis-Modals
export function registerErgebnisseContextTooltip() {
  // mehrfach aufrufen erlaubt – wir registrieren nur genau einmal erfolgreich
  if (registerErgebnisseContextTooltip.__done) return;

  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip) {
    // Tooltip-Bibliothek noch nicht da → später nochmal probieren
    // (kurzer Retry – idempotent)
    if (!registerErgebnisseContextTooltip.__retries) registerErgebnisseContextTooltip.__retries = 0;
    if (registerErgebnisseContextTooltip.__retries < 50) {
      registerErgebnisseContextTooltip.__retries++;
      setTimeout(registerErgebnisseContextTooltip, 100);
    }
    return;
  }

  Tooltip.register('#modal-root .doc-list li, #modal-root .doc-list li *', {
    predicate: (el) => {
      const showFlag = !!(window.APP_STATE?.flags?.show_zwischenergebnisse_tooltip);
      if (!showFlag) return false;
      return !!el.closest('li.doc-li');
    },
    content: (_ev, el) => {
      try {
        const li = el.closest('li.doc-li');
        if (!li) return "";

        const formula = li.getAttribute('data-formula') || "";
        const formulaSource = li.getAttribute('data-formula_source') || "";

        let ctx = {};
        const raw = li.getAttribute('data-ctx-json');
        if (raw) { try { ctx = JSON.parse(raw); } catch {} }

        const root = document.createElement("div");
        root.className = "ctx-tooltip";

        if (formula) {
          const f = document.createElement('div');
          f.className = 'ctx-formula';
          f.innerHTML = formatMathWithSubSup(formula);
          root.appendChild(f);
        }

        if (formulaSource) {
          const fs = document.createElement('div');
          fs.className = 'ctx-formula-source';
          fs.textContent = `Quelle: ${formulaSource}`;
          root.appendChild(fs);
        }

        if (formula || formulaSource) {
          const divider = document.createElement("div");
          divider.className = "tt-divider";
          root.appendChild(divider);
        }

        const showRealKeys = !!(window.APP_STATE?.flags?.show_real_kontext_keys);
        if (showRealKeys) {
          // Debug-Modus: rohe Kontext-Keys/-Werte ohne Aliase, Sortierung oder weitere Formatierung
          const entries = ctx && typeof ctx === "object" ? Object.entries(ctx) : [];
          for (const [k, v] of entries) {
            const row = document.createElement('div');
            row.className = 'ctx-row';

            const kEl = document.createElement('span');
            kEl.className = 'ctx-k';
            kEl.textContent = `${k}: `;

            const vEl = document.createElement('span');
            vEl.className = 'ctx-v';

            let val;
            if (v === null || v === undefined) {
              val = "—";
            } else if (typeof v === "string") {
              val = v;
            } else {
              try {
                val = JSON.stringify(v);
              } catch {
                val = String(v);
              }
            }
            vEl.textContent = val;

            row.appendChild(kEl);
            row.appendChild(vEl);
            root.appendChild(row);
          }
        } else {
          // Standard-Modus: sortierte, "hübsche" Kontextanzeige mit Aliases und Zahlformatierung
          const ordered = orderContextEntries(ctx);
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
        return root;
      } catch {
        return "";
      }
    },
    delay: 80,
  });

  registerErgebnisseContextTooltip.__done = true;
}

// Event-Delegation: klickbare Trigger
export function setupErgebnisseTriggers() {
  if (setupErgebnisseTriggers.__done) return;
  setupErgebnisseTriggers.__done = true;

  document.addEventListener("click", (ev) => {
    const t = ev.target;

    // 1) Generischer Trigger irgendwo im UI
    const generic = t.closest('[data-open="ergebnisse"]');
    if (generic) {
      const normKey  = generic.dataset.normKey || generic.closest('[data-norm-key]')?.dataset.normKey;
      const szenario = generic.dataset.szenario || null;
      const nachweis = generic.dataset.nachweis || null; // ← NEU
      if (normKey) openErgebnisseModal(normKey, szenario, { initialNachweis: nachweis });
      return;
    }

    // 2) Tabellenzelle
    const cell = t.closest('.results-table td[data-norm-key][data-openable="ergebnisse"]');
    if (cell) {
      const { normKey, szenario, nachweis } = cell.dataset;
      if (normKey) openErgebnisseModal(normKey, szenario || null, { initialNachweis: nachweis || null });
      return;
    }
  }, { passive: true });
}

// Bequemer Sammelaufruf
export function setupErgebnisseUI() {
  registerErgebnisseContextTooltip();
  setupErgebnisseTriggers();
}
