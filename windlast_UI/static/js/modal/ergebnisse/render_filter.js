export function renderFilterBar({
  query = "",
  activeFilters = [],
  onSearchInput = null,
  onSearchSubmit = null,
  onRemoveFilter = null,
  onClearFilters = null,
} = {}) {
  const root = document.createElement("div");
  root.className = "erg-filter";

  root.innerHTML = `
    <form class="erg-filter-search" autocomplete="off">
      <input
        class="erg-filter-input"
        type="search"
        placeholder="Ergebnisse durchsuchen oder Filter eingeben…"
        value="${escapeAttr(query)}"
      />
    </form>

    <div class="erg-filter-chips">
      ${activeFilters.length
        ? activeFilters.map(renderFilterChip).join("")
        : `<span class="erg-filter-empty">Keine Filter aktiv</span>`
      }

      ${activeFilters.length
        ? `<button class="erg-filter-clear" type="button">Alle entfernen</button>`
        : ""
      }
    </div>
  `;

  const form = root.querySelector(".erg-filter-search");
  const input = root.querySelector(".erg-filter-input");

  input?.addEventListener("input", () => {
    onSearchInput?.(input.value);
  });

  form?.addEventListener("submit", (ev) => {
    ev.preventDefault();
    onSearchSubmit?.(input?.value || "");
  });

  root.querySelectorAll("[data-remove-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      onRemoveFilter?.(btn.dataset.removeFilter);
    });
  });

  root.querySelector(".erg-filter-clear")?.addEventListener("click", () => {
    onClearFilters?.();
  });

  return root;
}

function renderFilterChip(filter) {
  const id = String(filter.id ?? filter.key ?? filter.name ?? "");
  const label = filter.label ?? filter.name ?? id;

  return `
    <button
      class="erg-filter-chip"
      type="button"
      data-remove-filter="${escapeAttr(id)}"
      title="Filter entfernen"
    >
      <span class="erg-filter-chip-label">${escapeHtml(label)}</span>
      <span class="erg-filter-chip-remove" aria-hidden="true">×</span>
    </button>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}