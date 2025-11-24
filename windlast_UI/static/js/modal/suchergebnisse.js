// static/js/modal/suchergebnisse.js

/**
 * Kleines "Dropdown-Modal" für die Hilfe-Suche.
 * Wird relativ zu einem Anker-Element (dem Suchfeld) positioniert.
 */

class HelpSearchResults {
  constructor() {
    this.container = null;
    this.anchorEl = null;
  }

  _ensureContainer() {
    if (this.container) return;

    const div = document.createElement("div");
    div.className = "help-search-results-modal";
    div.style.position = "absolute";
    div.style.zIndex = "9999";
    div.style.minWidth = "260px";
    div.style.maxWidth = "520px";
    div.style.maxHeight = "320px";
    div.style.overflowY = "auto";
    div.style.borderRadius = "6px";
    div.style.boxShadow = "0 8px 20px rgba(0,0,0,0.2)";
    div.style.fontSize = "0.9rem";

    // Theme-Freundlich: Hintergrund über CSS überschreibbar lassen,
    // aber Fallback hier definieren
    div.style.background = "var(--color-surface-elevated, #ffffff)";
    div.style.color = "inherit";

    // Initialer Inhalt – Placeholder
    const inner = document.createElement("div");
    inner.className = "help-search-results-content";
    inner.style.padding = "8px 10px";
    inner.textContent = "Platzhalter für Suchergebnisse";
    div.appendChild(inner);

    document.body.appendChild(div);
    this.container = div;

    // Klick außerhalb schließt das Modal
    document.addEventListener("click", (ev) => {
      if (!this.container) return;
      if (this.anchorEl && this.anchorEl.contains(ev.target)) return;
      if (this.container.contains(ev.target)) return;
      this.hide();
    });
  }

  /**
   * Öffnet das Ergebnis-Modal unterhalb des anchorEl.
   * query wird aktuell ignoriert (placeholder).
   */
  openBelow(anchorEl, query) {
    this._ensureContainer();
    this.anchorEl = anchorEl;

    // Inhalt: erstmal statischer Placeholder
    const content = this.container.querySelector(".help-search-results-content");
    if (content) {
      content.textContent = "Platzhalter für Suchergebnisse";
    }

    // Positionieren
    const rect = anchorEl.getBoundingClientRect();
    const scrollX = window.scrollX || window.pageXOffset;
    const scrollY = window.scrollY || window.pageYOffset;

    this.container.style.left = (rect.left + scrollX) + "px";
    this.container.style.top = (rect.bottom + scrollY + 4) + "px"; // 4px Abstand

    this.container.style.display = "block";
  }

  hide() {
    if (!this.container) return;
    this.container.style.display = "none";
    this.anchorEl = null;
  }
}

const INSTANCE = new HelpSearchResults();

/**
 * Convenience-API von außen nutzbar:
 * openHelpSearchResults(inputEl, query)
 * closeHelpSearchResults()
 */
export function openHelpSearchResults(anchorEl, query) {
  INSTANCE.openBelow(anchorEl, query);
}

export function closeHelpSearchResults() {
  INSTANCE.hide();
}
