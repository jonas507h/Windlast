// static/js/modal/suchergebnisse.js
import { runHelpSearch } from "../utils/help_suche.js";

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

    // Titel
    const titleEl = document.createElement("div");
    titleEl.className = "help-search-result-title";
    titleEl.textContent = r.title || r.id || "Ohne Titel";

    // Snippet
    const snippetEl = document.createElement("div");
    snippetEl.className = "help-search-result-snippet";
    snippetEl.innerHTML = buildHighlightedSnippet(r.text || "", query);

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
