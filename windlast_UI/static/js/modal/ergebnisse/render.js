import { escapeHtml, formatNumberDE, formatVectorDE, formatMathWithSubSup } from "../../utils/formatierung.js";
import { listEbenen, listGruppen, listErgebnisse, listMessages, makePathLabel } from "./tree.js";

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

function makeNodeId() {
  return `erg-node-${Math.random().toString(36).slice(2)}`;
}

function renderTreeLevel(container, state, path = []) {
  const ebenen = listEbenen(container);
  if (!ebenen.length) return "";

  return ebenen.map(ebene => {
    const gruppen = listGruppen(ebene);
    if (!gruppen.length) return "";

    const groupsHtml = gruppen.map(gruppe => {
      const id = makeNodeId();
      state.nodes.set(id, { node: gruppe, path: [...path, {
        ebene: ebene.name,
        ebeneLabel: ebene.label,
        gruppe: gruppe.name,
        gruppeLabel: gruppe.label,
      }] });

      const winnerMark = gruppe.winner === true ? `<span class="erg-tree-winner">✓</span>` : "";
      const label = gruppe.label || gruppe.name;

      return `
        <li class="erg-tree-group">
          <button type="button" class="erg-tree-btn" data-node-id="${id}">
            <span class="erg-tree-name">${escapeHtml(label)}</span>
            ${winnerMark}
          </button>
          <div class="erg-tree-children">
            ${renderTreeLevel(gruppe, state, state.nodes.get(id).path)}
          </div>
        </li>
      `;
    }).join("");

    return `
      <li class="erg-tree-level">
        <div class="erg-tree-level-label">${escapeHtml(ebene.label || ebene.name)}</div>
        <ul class="erg-tree-groups">${groupsHtml}</ul>
      </li>
    `;
  }).join("");
}

export function renderErgebnisModalContent(rootNode) {
  const state = { nodes: new Map(), selectedId: null };

  const rootId = "root";
  state.nodes.set(rootId, { node: rootNode, path: [] });
  state.selectedId = rootId;

  const shell = document.createElement("div");
  shell.className = "ergebnisse-modal";

  shell.innerHTML = `
    <aside class="erg-tree-pane">
      <button type="button" class="erg-tree-root active" data-node-id="${rootId}">Root</button>
      <ul class="erg-tree">
        ${renderTreeLevel(rootNode, state)}
      </ul>
    </aside>

    <section class="erg-detail-pane">
      <div class="erg-detail-header">
        <h4 class="erg-detail-title">Root</h4>
      </div>
      <div class="erg-detail-content"></div>
    </section>
  `;

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

  shell.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-node-id]");
    if (!btn) return;

    const id = btn.dataset.nodeId;
    const nodeInfo = state.nodes.get(id);
    if (!nodeInfo) return;

    shell.querySelectorAll(".erg-tree-btn.active, .erg-tree-root.active")
      .forEach(el => el.classList.remove("active"));

    btn.classList.add("active");
    state.selectedId = id;
    renderDetails(nodeInfo);
  });

  renderDetails(state.nodes.get(rootId));

  return shell;
}