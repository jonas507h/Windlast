import { escapeHtml, formatNumberDE, formatVectorDE, formatMathWithSubSup, renderLatex } from "../../utils/formatierung.js";
import { listEbenen, listGruppen, listErgebnisse, listMessages, makePathLabel } from "../../utils/tree.js";
import { renderTree } from "./render_tree.js";
import { renderBreadcrumb } from "./render_breadcrumb.js";
import { renderNavigation } from "./render_navigation.js";
import { renderFilterBar, makeFilterId } from "./render_filter.js";
import { applyErgebnisFilters } from "./filter_ergebnisse.js";
import { searchInBranch } from "./suche_ergebnisse.js";
import { renderSearchResultsPanel } from "./render_suchergebnisse.js";
import { resolveResource } from "../../resources/resources.js";

function formatValue(value) {
  if (Array.isArray(value)) return formatVectorDE(value, 4);
  if (value && typeof value === "object" && ["x", "y", "z"].every(k => k in value)) {
    return formatVectorDE([value.x, value.y, value.z], 4);
  }
  return formatNumberDE(value, 4);
}

function resultTooltipMeta(ergebnis) {
  return JSON.stringify(ergebnis?.meta || {});
}

function renderResultItem(ergebnis) {
  const labelCode = ergebnis.label || ergebnis.name || "—";
  const label = resolveResource(labelCode, labelCode);
  const unit = ergebnis.einheit ? ` ${escapeHtml(ergebnis.einheit)}` : "";
  // const formula = ergebnis.formel ? `<div class="erg-result-formula">${formatMathWithSubSup(ergebnis.formel)}</div>` : "";
  // const symbol = ergebnis.formelzeichen ? `<span class="erg-result-symbol">${formatMathWithSubSup(ergebnis.formelzeichen)}</span>` : "";
  const symbolCode = ergebnis.formelzeichen;
  const symbolLatex = symbolCode
    ? resolveResource(symbolCode, symbolCode)
    : "";
  const formulaLatex = ergebnis.formel
    ? resolveResource(ergebnis.formel, ergebnis.formel)
    : "";

  return `
    <li class="erg-result-item" data-meta-json="${escapeHtml(resultTooltipMeta(ergebnis))}">
      <div class="erg-result-main">
        <span class="erg-result-label">${escapeHtml(label)}</span>
        ${symbolLatex
          ? `<span class="erg-result-symbol">${renderLatex(symbolLatex)}</span>`
          : ""
        }
        <span class="erg-result-value">${formatValue(ergebnis.wert)}${unit}</span>
      </div>
      ${formulaLatex
        ? `<div class="erg-result-formula">${renderLatex(formulaLatex, { block: true })}</div>`
        : ""
      }
    </li>
  `;
}

function renderMessageItem(message) {
  const severity = String(message.severity || "").toLowerCase();

  return `
    <li
      class="erg-message-item erg-message-${escapeHtml(severity)}"
      data-message-code="${escapeHtml(message.code || "")}"
      data-message-severity="${escapeHtml(severity)}"
      data-message-meta="${escapeHtml(JSON.stringify(message.meta || {}))}"
    >
      <span class="erg-message-text">${escapeHtml(message.text || "")}</span>
    </li>
  `;
}

export function renderErgebnisModalContent(rootNode, { startPath = null } = {}) {
  const filterState = {
    query: "",
    activeFilters: [],
    filteredRoot: rootNode,
  };

  let currentNodeInfo = { node: rootNode, path: [] };

  const state = { nodes: new Map(), selectedId: null };

  const rootId = "root";
  state.nodes.set(rootId, { node: rootNode, path: [] });
  state.selectedId = rootId;

  const shell = document.createElement("div");
  shell.className = "ergebnisse-modal";

  shell.innerHTML = `
    <div class="erg-filter-slot"></div>

    <aside class="erg-tree-pane"></aside>

    <section class="erg-detail-pane">
      <div class="erg-detail-header">
        <div class="erg-breadcrumb-slot"></div>
        <div class="erg-navigation-slot"></div>
      </div>
      <div class="erg-detail-content"></div>
    </section>
  `;

  const filterSlot = shell.querySelector(".erg-filter-slot");
  const treePane = shell.querySelector(".erg-tree-pane");
  const breadcrumbSlot = shell.querySelector(".erg-breadcrumb-slot");
  const navigationSlot = shell.querySelector(".erg-navigation-slot");
  const contentEl = shell.querySelector(".erg-detail-content");

  let tree = null;

  function rerenderFilterBar() {
    filterSlot.replaceChildren(
      renderFilterBar({
        query: filterState.query,
        activeFilters: filterState.activeFilters,

        onBranchSearch: (query) => {
          filterSlot.querySelector(".erg-search-results-panel")?.remove();

          const hits = searchInBranch(
            filterState.filteredRoot,
            currentNodeInfo.path,
            query
          );

          filterSlot.appendChild(
            renderSearchResultsPanel({
              query,
              hits,
              onSelectHit: (hit) => {
                tree.selectPath(hit.path);
                filterSlot.querySelector(".erg-search-results-panel")?.remove();
              },
              onClose: () => {
                filterSlot.querySelector(".erg-search-results-panel")?.remove();
              },
            })
          );
        },

        onSearchInput: (value) => {
          filterState.query = value;
        },

        onSelectFilter: (filter) => {
          const id = makeFilterId(filter);
          const exists = filterState.activeFilters.some((f) => makeFilterId(f) === id);

          if (!exists) {
            filterState.activeFilters.push(filter);
          }

          filterState.query = "";
          rerenderAll();
        },

        onRemoveFilter: (id) => {
          filterState.activeFilters = filterState.activeFilters
            .filter((filter) => makeFilterId(filter) !== id);

          rerenderAll();
        },

        onClearFilters: () => {
          filterState.activeFilters = [];
          rerenderAll();
        },
      })
    );
  }

  function rerenderAll() {
    filterState.filteredRoot = applyErgebnisFilters(rootNode, filterState.activeFilters);

    treePane.replaceChildren();
    breadcrumbSlot.replaceChildren();
    navigationSlot.replaceChildren();
    contentEl.replaceChildren();

    tree = renderTree({
      rootNode: filterState.filteredRoot,
      onSelect: (nodeInfo) => {
        renderDetails(nodeInfo);
      },
    });

    treePane.appendChild(tree.element);

    if (startPath && !tree.selectPath(startPath)) {
      tree.select("root");
    } else if (!startPath) {
      tree.select("root");
    }

    rerenderFilterBar();
  }

  function renderDetails(nodeInfo) {
    currentNodeInfo = nodeInfo;
    const node = nodeInfo.node;
    const ergebnisse = listErgebnisse(node);
    const messages = listMessages(node);

    breadcrumbSlot.replaceChildren(
      renderBreadcrumb({
        path: nodeInfo.path,
        onSelectPath: (pathIndex) => {
          if (pathIndex < 0) {
            tree.select("root");
            return;
          }

          const targetPath = nodeInfo.path.slice(0, pathIndex + 1);
          const targetEntry = [...tree.state.nodes.values()].find((entry) => {
            return JSON.stringify(entry.path) === JSON.stringify(targetPath);
          });

          if (targetEntry) {
            tree.select(targetEntry.id);
          }
        },
      })
    );

    navigationSlot.replaceChildren(
      renderNavigation({
        nodeInfo,
        onUp: () => {
          if (!nodeInfo.path.length) {
            tree.select("root");
            return;
          }

          const parentPath = nodeInfo.path.slice(0, -1);
          if (!parentPath.length) {
            tree.select("root");
          } else {
            tree.selectPath(parentPath);
          }
        },
        onChild: (child) => {
          const childPath = [
            ...nodeInfo.path,
            {
              ebene: child.ebene,
              gruppe: child.gruppe,
            },
          ];

          tree.selectPath(childPath);
        },
      })
    );

    const resultsHtml = ergebnisse.length
      ? `<ul class="erg-result-list">${ergebnisse.map(renderResultItem).join("")}</ul>`
      : `<p class="erg-empty">Keine Ergebnisse auf dieser Ebene.</p>`;

    const messagesHtml = messages.length
      ? `
        <h5 class="erg-section-title">Meldungen</h5>
        <ul class="erg-message-list">${messages.map(renderMessageItem).join("")}</ul>
      `
      : "";

    contentEl.innerHTML = `
      <h5 class="erg-section-title">Ergebnisse</h5>
      ${resultsHtml}
      ${messagesHtml}
    `;
  }

  rerenderAll();

  return shell;
}