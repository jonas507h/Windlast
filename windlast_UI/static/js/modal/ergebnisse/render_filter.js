import { searchFilterSuggestions } from "./suche_ergebnisse.js";

export function renderFilterBar({
  query = "",
  activeFilters = [],
  onSearchInput = null,
  onSearchSubmit = null,
  onSelectFilter = null,
  onBranchSearch = null,
  onRemoveFilter = null,
  onClearFilters = null,
} = {}) {
  let selectedIndex = 0;
  let matches = searchFilterSuggestions(query);

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

      <div class="erg-filter-suggestions" hidden></div>
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
  const suggestions = root.querySelector(".erg-filter-suggestions");

  function renderSuggestions() {
    matches = searchFilterSuggestions(input.value);
    selectedIndex = matches.length ? Math.min(selectedIndex, matches.length - 1) : 0;

    if (!input.value.trim() || !matches.length) {
      suggestions.hidden = true;
      suggestions.innerHTML = "";
      return;
    }

    suggestions.hidden = false;
    suggestions.innerHTML = matches.map((match, index) => `
      <button
        class="erg-filter-suggestion ${index === selectedIndex ? "active" : ""}"
        type="button"
        data-filter-index="${index}"
      >
        <span class="erg-filter-suggestion-group">${escapeHtml(match.groupLabel)}</span>
        <span class="erg-filter-suggestion-label">${escapeHtml(match.label)}</span>
      </button>
    `).join("");
  }

  function selectMatch(index) {
    const match = matches[index];
    if (!match) return;

    if (match.kind === "branch_search") {
      onBranchSearch?.(match.query);
    } else {
      onSelectFilter?.(match);
    }

    input.value = "";
    matches = [];
    selectedIndex = 0;
    suggestions.hidden = true;
    suggestions.innerHTML = "";
  }

  input?.addEventListener("input", () => {
    selectedIndex = 0;
    renderSuggestions();
    onSearchInput?.(input.value);
  });

  input?.addEventListener("keydown", (ev) => {
    if (!matches.length) return;

    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, matches.length - 1);
      renderSuggestions();
    }

    if (ev.key === "ArrowUp") {
      ev.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      renderSuggestions();
    }

    if (ev.key === "Enter") {
      ev.preventDefault();
      selectMatch(selectedIndex);
    }

    if (ev.key === "Escape") {
      suggestions.hidden = true;
    }
  });

  form?.addEventListener("submit", (ev) => {
    ev.preventDefault();
    if (matches.length) selectMatch(selectedIndex);
    else onSearchSubmit?.(input?.value || "");
  });

  suggestions?.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-filter-index]");
    if (!btn) return;
    selectMatch(Number(btn.dataset.filterIndex));
  });

  root.querySelectorAll("[data-remove-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      onRemoveFilter?.(btn.dataset.removeFilter);
    });
  });

  root.querySelector(".erg-filter-clear")?.addEventListener("click", () => {
    onClearFilters?.();
  });

  renderSuggestions();

  return root;
}

function renderFilterChip(filter) {
  const id = makeFilterId(filter);
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

export function makeFilterId(filter) {
  return `${filter.groupName}:${filter.name}`;
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