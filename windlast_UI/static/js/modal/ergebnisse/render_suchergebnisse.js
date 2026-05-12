import { escapeHtml, formatNumberDE, formatVectorDE, formatMathWithSubSup } from "../../utils/formatierung.js";

function formatValue(value) {
  if (Array.isArray(value)) return formatVectorDE(value, 4);
  if (value && typeof value === "object" && ["x", "y", "z"].every(k => k in value)) {
    return formatVectorDE([value.x, value.y, value.z], 4);
  }
  return formatNumberDE(value, 4);
}

export function renderSearchResultsPanel({
  query = "",
  hits = [],
  onSelectHit = null,
  onClose = null,
} = {}) {
  const root = document.createElement("div");
  root.className = "erg-search-results-panel";

  root.innerHTML = `
    <div class="erg-search-results-head">
      <div>
        <div class="erg-search-results-title">Suchtreffer</div>
        <div class="erg-search-results-sub">${escapeHtml(query)} · ${hits.length} Treffer</div>
      </div>
      <button class="erg-search-results-close" type="button">×</button>
    </div>

    <div class="erg-search-results-list">
      ${hits.length
        ? hits.map(renderHit).join("")
        : `<p class="erg-empty">Keine Treffer im aktuellen Ast.</p>`
      }
    </div>
  `;

  root.querySelector(".erg-search-results-close")?.addEventListener("click", () => {
    onClose?.();
  });

  root.querySelectorAll("[data-hit-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const hit = hits[Number(btn.dataset.hitIndex)];
      if (hit) onSelectHit?.(hit);
    });
  });

  return root;
}

function renderHit(hit, index) {
  if (hit.kind === "message") {
    return renderMessageHit(hit, index);
  }

  return renderErgebnisHit(hit, index);
}

function renderErgebnisHit(hit, index) {
  const ergebnis = hit.item;
  const label = ergebnis.label || ergebnis.name || "—";
  const unit = ergebnis.einheit ? ` ${escapeHtml(ergebnis.einheit)}` : "";
  const symbol = ergebnis.formelzeichen
    ? `<span class="erg-result-symbol">${formatMathWithSubSup(ergebnis.formelzeichen)}</span>`
    : "";

  return `
    <button class="erg-search-hit" type="button" data-hit-index="${index}">
      <div class="erg-search-hit-breadcrumb">${escapeHtml(hit.breadcrumb)}</div>
      <div class="erg-result-main">
        <span class="erg-result-label">${escapeHtml(label)}</span>
        ${symbol}
        <span class="erg-result-value">${formatValue(ergebnis.wert)}${unit}</span>
      </div>
    </button>
  `;
}

function renderMessageHit(hit, index) {
  const message = hit.item;
  const severity = String(message.severity || "").toLowerCase();

  return `
    <button class="erg-search-hit" type="button" data-hit-index="${index}">
      <div class="erg-search-hit-breadcrumb">${escapeHtml(hit.breadcrumb)}</div>
      <div class="erg-message-item erg-message-${escapeHtml(severity)}">
        <span class="erg-message-text">${escapeHtml(message.text || "")}</span>
      </div>
    </button>
  `;
}