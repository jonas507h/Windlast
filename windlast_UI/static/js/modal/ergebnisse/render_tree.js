// modal/ergebnisse/render_tree.js

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

function hasChildren(gruppe) {
  return listEbenen(gruppe).some((ebene) => listGruppen(ebene).length > 0);
}

function makeNodeId() {
  return `erg-tree-${Math.random().toString(36).slice(2)}`;
}

function renderGroup({ ebene, gruppe, state, path }) {
  const id = makeNodeId();

  const nextPath = [
    ...path,
    {
      ebene: ebene.name,
      ebeneLabel: ebene.label || ebene.name,
      gruppe: gruppe.name,
      gruppeLabel: gruppe.label || gruppe.name,
    },
  ];

  state.nodes.set(id, {
    id,
    node: gruppe,
    path: nextPath,
  });

  const expandable = hasChildren(gruppe);
  const winner = gruppe.winner === true;

  return `
    <li class="erg-tree-node" data-tree-node="${id}">
      <div class="erg-tree-row">
        <button
          type="button"
          class="erg-tree-toggle"
          data-tree-toggle="${id}"
          ${expandable ? "" : "disabled"}
          aria-label="Aufklappen"
          aria-expanded="false"
        >
          ${expandable ? "▸" : ""}
        </button>

        <button
          type="button"
          class="erg-tree-select"
          data-tree-select="${id}"
        >
          <span class="erg-tree-key">${esc(ebene.label || ebene.name)}</span>
          <span class="erg-tree-eq">=</span>
          <span class="erg-tree-label">${esc(gruppe.label || gruppe.name)}</span>
          ${winner ? `<span class="erg-tree-winner">✓</span>` : ""}
        </button>
      </div>

      ${
        expandable
          ? `<ul class="erg-tree-children" hidden>
              ${renderTreeLevels({
                container: gruppe,
                state,
                path: nextPath,
              })}
            </ul>`
          : ""
      }
    </li>
  `;
}

function renderTreeLevels({ container, state, path }) {
  return listEbenen(container)
    .map((ebene) => {
      return listGruppen(ebene)
        .map((gruppe) => renderGroup({ ebene, gruppe, state, path }))
        .join("");
    })
    .join("");
}

export function renderTree({ rootNode, onSelect }) {
  const state = {
    nodes: new Map(),
    selectedId: "root",
  };

  state.nodes.set("root", {
    id: "root",
    node: rootNode,
    path: [],
  });

  const root = document.createElement("div");
  root.className = "erg-tree-view";

  root.innerHTML = `
    <ul class="erg-tree-list">
      <li class="erg-tree-node" data-tree-node="root">
        <div class="erg-tree-row">
          <button
            type="button"
            class="erg-tree-toggle"
            data-tree-toggle="root"
            aria-label="Aufklappen"
            aria-expanded="true"
          >
            ▾
          </button>

          <button
            type="button"
            class="erg-tree-select active"
            data-tree-select="root"
          >
            <span class="erg-tree-label">Root</span>
          </button>
        </div>

        <ul class="erg-tree-children">
          ${renderTreeLevels({ container: rootNode, state, path: [] })}
        </ul>
      </li>
    </ul>
  `;

  function setSelected(id) {
    const info = state.nodes.get(id);
    if (!info) return;

    root.querySelectorAll(".erg-tree-select.active")
      .forEach((el) => el.classList.remove("active"));

    const btn = root.querySelector(`[data-tree-select="${CSS.escape(id)}"]`);
    btn?.classList.add("active");

    state.selectedId = id;
    onSelect?.(info);
  }

  function toggleNode(id) {
    const li = root.querySelector(`[data-tree-node="${CSS.escape(id)}"]`);
    if (!li) return;

    const children = li.querySelector(":scope > .erg-tree-children");
    const toggle = li.querySelector(":scope > .erg-tree-row > .erg-tree-toggle");

    if (!children || !toggle || toggle.disabled) return;

    const isHidden = children.hasAttribute("hidden");

    if (isHidden) {
      children.removeAttribute("hidden");
      toggle.textContent = "▾";
      toggle.setAttribute("aria-expanded", "true");
    } else {
      children.setAttribute("hidden", "");
      toggle.textContent = "▸";
      toggle.setAttribute("aria-expanded", "false");
    }
  }

  root.addEventListener("click", (ev) => {
    const toggle = ev.target.closest("[data-tree-toggle]");
    if (toggle && root.contains(toggle)) {
      toggleNode(toggle.dataset.treeToggle);
      return;
    }

    const select = ev.target.closest("[data-tree-select]");
    if (select && root.contains(select)) {
      setSelected(select.dataset.treeSelect);
      return;
    }
  });

  function pathsEqual(a = [], b = []) {
    if (a.length !== b.length) return false;
    return a.every((step, i) =>
      String(step.ebene) === String(b[i].ebene) &&
      String(step.gruppe) === String(b[i].gruppe)
    );
  }

  function selectPath(path) {
    const target = [...state.nodes.values()].find((entry) => pathsEqual(entry.path, path));
    if (!target) return false;

    // Eltern aufklappen
    for (let i = 0; i <= target.path.length; i++) {
      const partial = target.path.slice(0, i);
      const entry = [...state.nodes.values()].find((e) => pathsEqual(e.path, partial));
      if (!entry) continue;

      const li = root.querySelector(`[data-tree-node="${CSS.escape(entry.id)}"]`);
      const children = li?.querySelector(":scope > .erg-tree-children");
      const toggle = li?.querySelector(":scope > .erg-tree-row > .erg-tree-toggle");

      if (children && toggle && children.hasAttribute("hidden")) {
        children.removeAttribute("hidden");
        toggle.textContent = "▾";
        toggle.setAttribute("aria-expanded", "true");
      }
    }

    setSelected(target.id);
    return true;
  }

  return {
    element: root,
    state,
    select: setSelected,
    selectPath,
  };
}