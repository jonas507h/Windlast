// modal/ergebnisse/render_breadcrumb.js

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function renderBreadcrumb({ path = [], onSelectPath } = {}) {
  const root = document.createElement("nav");
  root.className = "erg-breadcrumb-box";
  root.setAttribute("aria-label", "Ergebnis-Pfad");

  const items = [
    {
      label: "Root",
      pathIndex: -1,
    },
    ...path.map((step, i) => ({
      label: step.gruppeLabel || step.gruppe || step.ebene || `Ebene ${i + 1}`,
      subLabel: step.ebeneLabel || step.ebene,
      pathIndex: i,
    })),
  ];

  root.innerHTML = `
    <ol class="erg-breadcrumb">
      ${items.map((item, i) => `
        <li class="erg-breadcrumb-item">
          ${i > 0 ? `<span class="erg-breadcrumb-sep">/</span>` : ""}
          <button
            type="button"
            class="erg-breadcrumb-btn"
            data-path-index="${item.pathIndex}"
            title="${esc(item.subLabel || item.label)}"
          >
            ${item.subLabel ? `<span class="erg-breadcrumb-key">${esc(item.subLabel)}</span>` : ""}
            <span class="erg-breadcrumb-label">${esc(item.label)}</span>
          </button>
        </li>
      `).join("")}
    </ol>
  `;

  root.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-path-index]");
    if (!btn || !root.contains(btn)) return;

    const index = Number(btn.dataset.pathIndex);
    onSelectPath?.(index);
  });

  return root;
}