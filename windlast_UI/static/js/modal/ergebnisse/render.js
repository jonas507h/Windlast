import { escapeHtml, formatNumberDE, formatVectorDE, formatMathWithSubSup } from "../../utils/formatierung.js";
import { listEbenen, listGruppen, listErgebnisse, listMessages, makePathLabel } from "./tree.js";
import { renderTree } from "./render_tree.js";

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

export function renderErgebnisModalContent(rootNode) {
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
        <h4 class="erg-detail-title">Root</h4>
      </div>

      <div class="erg-detail-content"></div>
    </section>
  `;

  const treePane = shell.querySelector(".erg-tree-pane");
  const titleEl = shell.querySelector(".erg-detail-title");
  const contentEl = shell.querySelector(".erg-detail-content");

  function renderDetails(nodeInfo) {
    const node = nodeInfo.node;
    const ergebnisse = listErgebnisse(node);
    const messages = listMessages(node);

    titleEl.textContent = makePathLabel(nodeInfo.path);

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

  tree.select("root");

  return shell;
}