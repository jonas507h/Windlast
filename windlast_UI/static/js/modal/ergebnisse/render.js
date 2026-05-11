import { escapeHtml, formatNumberDE, formatVectorDE, formatMathWithSubSup } from "../../utils/formatierung.js";
import { listEbenen, listGruppen, listErgebnisse, listMessages, makePathLabel } from "./tree.js";
import { renderTree } from "./render_tree.js";
import { renderBreadcrumb } from "./render_breadcrumb.js";
import { renderNavigation } from "./render_navigation.js";

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
  const label = ergebnis.label || ergebnis.name || "—";
  const unit = ergebnis.einheit ? ` ${escapeHtml(ergebnis.einheit)}` : "";
  const formula = ergebnis.formel ? `<div class="erg-result-formula">${formatMathWithSubSup(ergebnis.formel)}</div>` : "";
  const symbol = ergebnis.formelzeichen ? `<span class="erg-result-symbol">${escapeHtml(String(ergebnis.formelzeichen))}</span>` : "";

  return `
    <li class="erg-result-item" data-meta-json="${escapeHtml(resultTooltipMeta(ergebnis))}">
      <div class="erg-result-main">
        <span class="erg-result-label">${escapeHtml(label)}</span>
        ${symbol}
        <span class="erg-result-value">${formatValue(ergebnis.wert)}${unit}</span>
      </div>
      ${formula}
    </li>
  `;
}

function renderMessageItem(message) {
  return `
    <li class="erg-message-item erg-message-${escapeHtml(String(message.severity || "").toLowerCase())}">
      <strong>${escapeHtml(message.code || "")}</strong>
      <span>${escapeHtml(message.text || "")}</span>
    </li>
  `;
}

export function renderErgebnisModalContent(rootNode, { startPath = null } = {}) {
  const state = { nodes: new Map(), selectedId: null };

  const rootId = "root";
  state.nodes.set(rootId, { node: rootNode, path: [] });
  state.selectedId = rootId;

  const shell = document.createElement("div");
  shell.className = "ergebnisse-modal";

  shell.innerHTML = `
    <aside class="erg-tree-pane"></aside>

    <section class="erg-detail-pane">
      <div class="erg-detail-header">
        <div class="erg-breadcrumb-slot"></div>
        <div class="erg-navigation-slot"></div>
      </div>
      <div class="erg-detail-content"></div>
    </section>
  `;

  const treePane = shell.querySelector(".erg-tree-pane");
  const breadcrumbSlot = shell.querySelector(".erg-breadcrumb-slot");
  const navigationSlot = shell.querySelector(".erg-navigation-slot");
  const contentEl = shell.querySelector(".erg-detail-content");

  function renderDetails(nodeInfo) {
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

  const tree = renderTree({
    rootNode,
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

  return shell;
}