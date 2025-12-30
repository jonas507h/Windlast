// modal/einstellungen.js

function labelFromKey(key) {
  // simple: show_nullpunkt -> "Show Nullpunkt"
  // du kannst das später durch eine Mapping-Tabelle ersetzen
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function buildFlagsPanel() {
  const panel = document.createElement("section");
  panel.dataset.panel = "flags";
  panel.hidden = true;

  const header = document.createElement("div");
  header.className = "settings-section-head";

  const h = document.createElement("h4");
  h.className = "settings-section-title";
  h.textContent = "Editierbare Flags";

  const sub = document.createElement("div");
  sub.className = "settings-section-hint";
  sub.textContent = "Diese Flags können in dieser Rolle angepasst und gespeichert werden.";

  header.appendChild(h);
  header.appendChild(sub);

  const list = document.createElement("div");
  list.className = "settings-flag-list";

  panel.appendChild(header);
  panel.appendChild(list);

  function render() {
    list.innerHTML = "";

    const meta = (window.APP_STATE && window.APP_STATE.flagsMeta) ? window.APP_STATE.flagsMeta : {};
    const entries = Object.entries(meta)
      .filter(([, v]) => v && v.lock === false);

    if (entries.length === 0) {
      const empty = document.createElement("div");
      empty.className = "settings-placeholder";
      empty.textContent = "In dieser Rolle sind keine Flags editierbar.";
      list.appendChild(empty);
      return;
    }

    // Stabil sortieren
    entries.sort(([a], [b]) => a.localeCompare(b, "de"));

    for (const [key, v] of entries) {
      const row = document.createElement("label");
      row.className = "settings-flag-row";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !!v.value;
      cb.dataset.flag = key;

      const text = document.createElement("span");
      text.className = "settings-flag-label";
      text.textContent = labelFromKey(key);

      const code = document.createElement("code");
      code.className = "settings-flag-key";
      code.textContent = key;

      const left = document.createElement("div");
      left.className = "settings-flag-left";
      left.appendChild(text);
      left.appendChild(code);

      row.appendChild(cb);
      row.appendChild(left);

      cb.addEventListener("change", () => {
        try {
          window.APP_STATE.setFlag(key, cb.checked);
        } catch (e) {
          console.warn(e?.message || e);
          // rollback auf echten Zustand
          try { cb.checked = !!window.APP_STATE.getFlag(key); } catch {}
        }
      });

      list.appendChild(row);
    }
  }

  // re-render bei Role/Flag Änderungen
  if (window.APP_STATE?.onRoleChanged) window.APP_STATE.onRoleChanged(render);
  document.addEventListener("ui:flags-changed", render);

  // erstes Render
  render();

  return panel;
}

export function openEinstellungenModal({ initialTab = "berechnung" } = {}) {
  const wrap = document.createElement("div");
  wrap.className = "settings-modal";

  /* ---------- Title ---------- */
  const title = document.createElement("h3");
  title.id = "modal-title";
  title.textContent = "Einstellungen";

  /* ---------- Tabs (IDENTISCH zu index.html) ---------- */
  const tabs = document.createElement("nav");
  tabs.className = "tabs";

  const tabDefs = [
    { id: "berechnung", label: "Berechnung" },
    { id: "flags", label: "Flags" },
  ];

  tabDefs.forEach(({ id, label }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tab";
    btn.dataset.view = id;
    btn.textContent = label;
    tabs.appendChild(btn);
  });

  /* ---------- Panels ---------- */
  const panels = document.createElement("div");
  panels.className = "settings-panels";

  const panelMap = new Map();

  tabDefs.forEach(({ id }) => {
    let panel;

    if (id === "flags") {
        panel = buildFlagsPanel();
    } else {
        panel = document.createElement("section");
        panel.dataset.panel = id;
        panel.hidden = true;
        panel.textContent = "Inhalt folgt…";
    }

    panelMap.set(id, panel);
    panels.appendChild(panel);
    });

  /* ---------- Actions ---------- */
  const actions = document.createElement("div");
  actions.className = "settings-actions";

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "btn";
  closeBtn.textContent = "Schließen";
  closeBtn.onclick = () => Modal.close();

  actions.appendChild(closeBtn);

  /* ---------- Compose ---------- */
  wrap.appendChild(title);
  wrap.appendChild(tabs);
  wrap.appendChild(panels);
  wrap.appendChild(actions);

  /* ---------- Tab logic (identisch zu switch_konstruktion) ---------- */
  function switchTab(view) {
    // Tabs
    tabs.querySelectorAll(".tab").forEach(btn => {
      btn.setAttribute(
        "aria-current",
        btn.dataset.view === view ? "page" : ""
      );
    });

    // Panels
    panelMap.forEach((panel, key) => {
      panel.hidden = key !== view;
    });
  }

  tabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (!btn) return;
    switchTab(btn.dataset.view);
  });

  Modal.open(wrap, {
    onOpen: () => switchTab(initialTab),
  });
}

// global (wie bei dir üblich)
window.openEinstellungenModal = openEinstellungenModal;
