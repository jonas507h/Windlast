// modal/ergebnisse/render_navigation.js

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function listEbenen(node) {
  return Array.isArray(node?.ebenen) ? node.ebenen : [];
}

function listGruppen(ebene) {
  return Array.isArray(ebene?.gruppen) ? ebene.gruppen : [];
}

export function renderNavigation({ nodeInfo, onUp, onChild } = {}) {
  const root = document.createElement("div");
  root.className = "erg-nav-box";

  const children = [];

  for (const ebene of listEbenen(nodeInfo?.node)) {
    for (const gruppe of listGruppen(ebene)) {
      children.push({
        ebene: ebene.name,
        ebeneLabel: ebene.label || ebene.name,
        gruppe: gruppe.name,
        gruppeLabel: gruppe.label || gruppe.name,
        winner: gruppe.winner === true,
      });
    }
  }

  root.innerHTML = `
    <button
      type="button"
      class="erg-nav-up"
      ${nodeInfo?.path?.length ? "" : "disabled"}
      title="Eine Ebene nach oben"
    >
      ↑
    </button>

    <div class="erg-nav-children">
      ${
        children.length
          ? children.map((child, i) => `
              <button
                type="button"
                class="erg-nav-child"
                data-child-index="${i}"
                title="${esc(child.ebeneLabel)}"
              >
                <span class="erg-nav-child-key">${esc(child.ebeneLabel)}</span>
                <span class="erg-nav-child-label">${esc(child.gruppeLabel)}</span>
                ${child.winner ? `<span class="erg-nav-winner">✓</span>` : ""}
              </button>
            `).join("")
          : `<span class="erg-nav-empty">Keine Unterebenen</span>`
      }
    </div>
  `;

  root.querySelector(".erg-nav-up")?.addEventListener("click", () => {
    onUp?.();
  });

  root.querySelectorAll("[data-child-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const child = children[Number(btn.dataset.childIndex)];
      if (child) onChild?.(child);
    });
  });

  return root;
}