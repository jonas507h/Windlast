// modal/einstellungen.js

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
    const panel = document.createElement("section");
    panel.dataset.panel = id;
    panel.hidden = true;

    // Placeholder
    panel.textContent = "Inhalt folgt…";

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
