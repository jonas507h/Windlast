// static/js/modal/suchergebnisse.js
import { runHelpSearch } from "../utils/help_suche.js";

// Help-Content, um Breadcrumb & Body-Text zu kennen
import { NORM_HELP_PAGES } from "../help_content/norminfo.js";
import { GENERAL_HELP_PAGES } from "../help_content/allgemein.js";
import { MELDUNGEN_HELP_PAGES } from "../help_content/meldungen.js";
import { HEADER_HELP_PAGES } from "../help_content/header.js";
import { TOR_HELP_PAGES } from "../help_content/tor.js";
import { STEHER_HELP_PAGES } from "../help_content/steher.js";
import { TISCH_HELP_PAGES } from "../help_content/tisch.js";
import { ERGEBNISSE_HELP_PAGES } from "../help_content/ergebnisse.js";
import { ZWISCHENERGEBNISSE_HELP_PAGES } from "../help_content/zwischenergebnisse.js";

// interne Registry, analog zu help.js
const PAGES_BY_ID = Object.create(null);

function registerPages(list) {
  for (const p of list || []) {
    if (!p || !p.id) continue;
    PAGES_BY_ID[p.id] = p;
  }
}

registerPages(NORM_HELP_PAGES);
registerPages(GENERAL_HELP_PAGES);
registerPages(MELDUNGEN_HELP_PAGES);
registerPages(HEADER_HELP_PAGES);
registerPages(TOR_HELP_PAGES);
registerPages(STEHER_HELP_PAGES);
registerPages(TISCH_HELP_PAGES);
registerPages(ERGEBNISSE_HELP_PAGES);
registerPages(ZWISCHENERGEBNISSE_HELP_PAGES);

/**
 * Kleiner interner State
 */
let panelRoot = null;
let panelEl   = null;
let currentAnchor = null;

/**
 * Panel-Root einmalig anlegen
 */
function ensurePanel() {
  if (panelEl) return;

  panelRoot = document.createElement("div");
  panelRoot.id = "help-search-results-root";

  panelRoot.innerHTML = `
    <div class="help-search-results-panel" hidden>
      <div class="help-search-results-header">
        <div class="help-search-results-title">Suche in der Hilfe</div>
        <div class="help-search-results-meta">
          <span class="help-search-results-pill" data-role="meta-pill"></span>
        </div>
      </div>
      <div class="help-search-empty" data-role="empty">Gib einen Suchbegriff ein …</div>
      <ul class="help-search-results-list" data-role="list"></ul>
    </div>
  `;

  document.body.appendChild(panelRoot);
  panelEl = panelRoot.querySelector(".help-search-results-panel");

  // Schließen bei Klick außerhalb
  document.addEventListener("mousedown", (ev) => {
    if (!panelEl || panelEl.hidden) return;
    if (panelEl.contains(ev.target)) return;
    if (currentAnchor && currentAnchor.contains && currentAnchor.contains(ev.target)) return;
    closeHelpSearchResults();
  });

  // Debug-Tooltip für Suchergebnisse registrieren (nur einmal)
  registerHelpSearchDebugTooltip();
}

/**
 * Panel an ein Anker-Element (z.B. Input) positionieren
 */
function positionPanel(anchor) {
  if (!panelEl || !anchor) return;
  const rect = anchor.getBoundingClientRect();

  const marginTop = 4;
  const top  = rect.bottom + marginTop + window.scrollY;
  const left = rect.left + window.scrollX;

  panelEl.style.top  = `${top}px`;
  panelEl.style.left = `${left}px`;
  panelEl.style.right = "auto";

  // Breite: mindestens Breite des Inputs
  const minWidth = rect.width;
  panelEl.style.minWidth = `${minWidth}px`;
}

/**
 * Hilfsfunktion: Query in einzelne Wörter zerlegen
 */
function splitQueryTerms(query) {
  if (!query) return [];
  return String(query)
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
}

/**
 * Snippet bauen und Treffer hervorheben
 */
function buildHighlightedSnippet(text, query) {
  if (!text) return "";

  const lower = text.toLowerCase();
  const terms = splitQueryTerms(query);
  if (!terms.length) return escapeHtml(text);

  // Beste Fundstelle suchen
  let bestIdx = -1;
  for (const t of terms) {
    const idx = lower.indexOf(t);
    if (idx !== -1 && (bestIdx === -1 || idx < bestIdx)) {
      bestIdx = idx;
    }
  }

  let start = 0;
  let end = text.length;

  const desiredLen = 180;
  if (bestIdx !== -1 && text.length > desiredLen) {
    start = Math.max(0, bestIdx - 60);
    end   = Math.min(text.length, start + desiredLen);
  }

  let snippet = text.slice(start, end);
  let prefix = start > 0 ? "…" : "";
  let suffix = end < text.length ? "…" : "";

  // Highlight via Regex
  const escapedTerms = terms.map(escapeRegex);
  const re = new RegExp("(" + escapedTerms.join("|") + ")", "gi");

  const html = escapeHtml(snippet).replace(re, (m) => {
    return `<mark class="help-search-hit">${m}</mark>`;
  });

  return prefix + html + suffix;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Vereinfachtes Text-Extract aus HTML, wie in help_suche.js
function extractSearchableText(rawHtml) {
  if (!rawHtml) return "";

  let text = String(rawHtml);

  // FAQ-Fragen in sichtbaren Text umwandeln
  text = text.replace(/<faq[^>]*question="([^"]+)"[^>]*>/gi, " $1 ");
  text = text.replace(/<\/faq>/gi, " ");

  // Wiki-Links [[id|Label]] → Label; [[id]] → id
  text = text.replace(/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g, (_m, id, _rest, label) => {
    return " " + (label || id) + " ";
  });

  // HTML-Tags entfernen
  text = text.replace(/<[^>]+>/g, " ");

  // Whitespace normalisieren
  text = text.replace(/\s+/g, " ").trim();

  return text;
}

// Für Titel: komplett, ohne Abschneiden, nur highlighten
function buildHighlightedInline(text, query) {
  if (!text) return "";
  const terms = splitQueryTerms(query);
  if (!terms.length) return escapeHtml(text);

  const escapedTerms = terms.map(escapeRegex);
  const re = new RegExp("(" + escapedTerms.join("|") + ")", "gi");

  return escapeHtml(text).replace(re, (m) => {
    return `<mark class="help-search-hit">${m}</mark>`;
  });
}

// Für den Fall "Treffer im Titel": Anfang des Inhalts zeigen
function buildHighlightedSnippetFromStart(text, query) {
  if (!text) return "";
  const maxLen = 180;
  const slice = text.slice(0, maxLen);
  const terms = splitQueryTerms(query);
  if (!terms.length) {
    return escapeHtml(slice) + (text.length > maxLen ? "…" : "");
  }

  const escapedTerms = terms.map(escapeRegex);
  const re = new RegExp("(" + escapedTerms.join("|") + ")", "gi");

  const html = escapeHtml(slice).replace(re, (m) => {
    return `<mark class="help-search-hit">${m}</mark>`;
  });

  return html + (text.length > maxLen ? "…" : "");
}

// Breadcrumb für eine Seite als Array von Labels
function getBreadcrumbLabels(pageId) {
  const page = PAGES_BY_ID[pageId];
  const labels = ["Hilfe"];

  const pathIds = Array.isArray(page?.pfad) ? page.pfad : [];
  for (const pid of pathIds) {
    const pPage = PAGES_BY_ID[pid];
    labels.push(pPage?.shortTitle || pPage?.title || pid);
  }

  const currentLabel = page?.shortTitle || page?.title || pageId;
  labels.push(currentLabel);

  return labels;
}

/**
 * Ergebnisse im Panel rendern
 */
function renderResults(query, searchResult) {
  if (!panelEl) return;
  const listEl  = panelEl.querySelector('[data-role="list"]');
  const emptyEl = panelEl.querySelector('[data-role="empty"]');
  const pill    = panelEl.querySelector('[data-role="meta-pill"]');

  listEl.textContent = "";
  const results = searchResult?.results || [];

  if (!query || !query.trim()) {
    emptyEl.textContent = "Gib einen Suchbegriff ein …";
    emptyEl.style.display = "block";
    pill.textContent = "0 Treffer";
    return;
  }

  if (!results.length) {
    emptyEl.textContent = "Keine Treffer in der Hilfe gefunden.";
    emptyEl.style.display = "block";
    pill.textContent = "0 Treffer";
    return;
  }

  emptyEl.style.display = "none";
  pill.textContent = `${results.length} Treffer`;

  for (const r of results) {
    const li = document.createElement("li");
    li.className = "help-search-result-item";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "help-search-result-button";
    btn.setAttribute("data-help-id", r.id);

    // Debug-Daten für Tooltip anheften
    try {
      if (r.debug) {
        btn.setAttribute("data-search-debug", JSON.stringify(r.debug));
      }
    } catch {}
    btn.setAttribute("data-search-score", String(r.score ?? ""));
    btn.setAttribute("data-search-field", r.field || "");

    const page = PAGES_BY_ID[r.id] || null;
    const titleText = (page && page.title) || r.title || r.id || "Ohne Titel";
    const bodyTextRaw = page ? extractSearchableText(page.body || "") : "";
    const breadcrumbLabels = getBreadcrumbLabels(r.id);

    // --- Breadcrumb-Zeile (ohne Links) ---
    const breadcrumbEl = document.createElement("div");
    breadcrumbEl.className = "help-search-result-breadcrumb";
    breadcrumbEl.textContent = breadcrumbLabels.join(" / ");

    // --- Titel-Zeile ---
    const titleEl = document.createElement("div");
    titleEl.className = "help-search-result-title";

    // --- Snippet-Zeile ---
    const snippetEl = document.createElement("div");
    snippetEl.className = "help-search-result-snippet";

    if (r.field === "title") {
      // Treffer im Titel:
      //  - Titel selbst markieren
      //  - Anfang vom Inhalt zeigen
      titleEl.innerHTML = buildHighlightedInline(titleText, query);
      snippetEl.innerHTML = buildHighlightedSnippetFromStart(bodyTextRaw, query);
    } else {
      // Treffer im Inhalt:
      //  - Titel normal anzeigen
      //  - Stelle im Inhalt mit Treffer zeigen
      titleEl.textContent = titleText;
      const snippetSource = bodyTextRaw || r.text || "";
      snippetEl.innerHTML = buildHighlightedSnippet(snippetSource, query);
    }

    // Beim Klick Panel schließen (Navigation macht help.js über document-click)
    btn.addEventListener("click", () => {
      closeHelpSearchResults();
    });

    btn.appendChild(breadcrumbEl);
    btn.appendChild(titleEl);
    btn.appendChild(snippetEl);

    li.appendChild(btn);
    listEl.appendChild(li);
  }
}

/**
 * Öffentliche API:
 *  - anchorEl: das Input-Element
 *  - query: String (optional; wenn nicht übergeben, wird anchorEl.value benutzt)
 */
export function openHelpSearchResults(anchorEl, query) {
  ensurePanel();
  currentAnchor = anchorEl || currentAnchor;

  const q = typeof query === "string"
    ? query
    : (anchorEl && "value" in anchorEl ? anchorEl.value : "");

  const searchResult = runHelpSearch(q || "");

  positionPanel(currentAnchor);
  renderResults(q, searchResult);

  panelEl.hidden = false;
}

/**
 * Panel schließen
 */
export function closeHelpSearchResults() {
  if (!panelEl) return;
  panelEl.hidden = true;
}

/**
 * Auch als globale Fallback-API bereitstellen,
 * falls du irgendwo schon window.openHelpSearchResults o.ä. benutzt.
 */
window.HelpSearchResults = {
  open: openHelpSearchResults,
  close: closeHelpSearchResults,
};
window.openHelpSearchResults = openHelpSearchResults;
window.closeHelpSearchResults = closeHelpSearchResults;

/**
 * Debug-Tooltip für Suchergebnisse registrieren.
 * Nutzt window.Tooltip und das Flag window.APP_STATE.flags.show_suche_tooltip.
 */
function registerHelpSearchDebugTooltip() {
  const Tooltip = window.Tooltip;
  if (!Tooltip || registerHelpSearchDebugTooltip.__done) return;
  registerHelpSearchDebugTooltip.__done = true;

  Tooltip.register(".help-search-results-list .help-search-result-button", {
    predicate: (el) => {
      const showFlag = !!(window.APP_STATE?.flags?.show_suche_tooltip);
      if (!showFlag) return false;
      return !!el.closest(".help-search-result-button");
    },
    content: (_ev, el) => {
      const btn = el.closest(".help-search-result-button");
      if (!btn) return "";

      // Flag erneut prüfen – wenn zur Laufzeit deaktiviert wird, kein Tooltip anzeigen
      const showFlag = !!(window.APP_STATE?.flags?.show_suche_tooltip);
      if (!showFlag) return "";

      let debug = {};
      try {
        debug = JSON.parse(btn.getAttribute("data-search-debug") || "{}");
      } catch {}

      const score = Number(btn.getAttribute("data-search-score") || "0");
      const field = debug.field || btn.getAttribute("data-search-field") || "body";
      const penalties = debug.penalties || {};
      const base = typeof debug.basePenalty === "number"
        ? debug.basePenalty
        : (field === "title" ? 0 : 2); // Fallback auf deine Defaults

      const matchType = debug.matchType || "decomposed";

      const labels = {
        decomposition: "Begriffszerlegung",
        gap: "Abstand zwischen Begriffsteilen",
        order: "Reihenfolgeabweichung",
        missingFullTerm: "Begriff nicht komplett gefunden",
        synonyms: "Synonyme verwendet",
        fuzzy: "Schreibfehler / Fuzzy-Match",
        notFound: "In diesem Feld nichts gefunden",
      };

      const root = document.createElement("div");
      root.className = "ctx-tooltip"; // nutzt bestehendes Tooltip-CSS

      function addRow(keyLabel, valueText) {
        const row = document.createElement("div");
        row.className = "ctx-row";
        const kEl = document.createElement("span");
        kEl.className = "ctx-k";
        kEl.textContent = keyLabel + ": ";
        const vEl = document.createElement("span");
        vEl.className = "ctx-v";
        vEl.textContent = valueText;
        row.appendChild(kEl);
        row.appendChild(vEl);
        root.appendChild(row);
      }

      // Kopf
      addRow("Gesamt-Score", String(score));
      addRow("Feld", field === "title" ? "Titel" : "Inhalt");
      addRow("Match-Typ", matchType === "full" ? "Volltreffer (Phrase)" : "Zerlegte Teile");

      // Basis-Strafe für das Feld
      addRow("Basis (Feld)", "+" + base);

      // Einzelne Mechanismen nur anzeigen, wenn sie > 0 sind
      for (const key of Object.keys(labels)) {
        const val = penalties[key] || 0;
        if (!val) continue;
        addRow(labels[key], "+" + val);
      }

      return root;
    },
    delay: 80,
  });
}