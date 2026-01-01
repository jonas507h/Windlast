// modal/einstellungen.js

import { getFlagLabel } from "../utils/formatierung.js";

function renderFlags(container) {
  // Header
  const head = document.createElement("div");
  head.className = "settings-section-head";

  // const h = document.createElement("h4");
  // h.className = "settings-section-title";
  // h.textContent = "Editierbare Flags";

  // const sub = document.createElement("div");
  // sub.className = "settings-section-hint";
  // sub.textContent = "Diese Flags können in dieser Rolle angepasst und gespeichert werden.";

  // head.appendChild(h);
  // head.appendChild(sub);

  const list = document.createElement("div");
  list.className = "settings-flag-list";

  container.appendChild(head);
  container.appendChild(list);

  const renderList = () => {
    list.innerHTML = "";

    const meta = window.APP_STATE?.flagsMeta || {};
    const entries = Object.entries(meta).filter(([, v]) => v && v.lock === false);

    if (entries.length === 0) {
      const empty = document.createElement("div");
      empty.className = "settings-placeholder";
      empty.textContent = "In dieser Rolle sind keine Flags editierbar.";
      list.appendChild(empty);
      return;
    }

    entries.sort(([a], [b]) => a.localeCompare(b, "de"));

    for (const [key, v] of entries) {
      const row = document.createElement("label");
      row.className = "settings-flag-row";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.className = "checkbox";
      cb.checked = !!v.value;

      const left = document.createElement("div");
      left.className = "settings-flag-left";

      const text = document.createElement("span");
      text.className = "settings-flag-label";
      text.textContent = getFlagLabel(key);

      const code = document.createElement("code");
      code.className = "settings-flag-key";
      code.textContent = key;

      left.appendChild(text);
      left.appendChild(code);

      row.appendChild(cb);
      row.appendChild(left);

      cb.addEventListener("change", () => {
        try {
          window.APP_STATE.setFlag(key, cb.checked);
        } catch (e) {
          console.warn(e?.message || e);
          // rollback
          cb.checked = !!(window.APP_STATE?.getFlag ? window.APP_STATE.getFlag(key) : v.value);
        }
      });

      list.appendChild(row);
    }
  };

  // Listener merken, damit wir sie beim Tabwechsel entfernen können
  const onFlagsChanged = () => renderList();
  const onRoleChanged = () => renderList();

  document.addEventListener("ui:flags-changed", onFlagsChanged);
  window.APP_STATE?.onRoleChanged?.(onRoleChanged);

  renderList();

  // destroy() zurückgeben
  return () => {
    document.removeEventListener("ui:flags-changed", onFlagsChanged);
    // onRoleChanged ist bei dir vermutlich ein Event-Wrapper → wenn du keinen "unsubscribe" hast,
    // dann lassen wir den Listener weg und verlassen uns auf ui:role-changed:
  };
}

function renderBerechnung(container) {
  const ph = document.createElement("div");
  ph.className = "settings-placeholder";
  ph.textContent = "Inhalt folgt…";
  container.appendChild(ph);
  return () => {};
}

function renderAnzeige(container) {
  const head = document.createElement("div");
  head.className = "settings-section-head";

  const row = document.createElement("div");
  row.className = "settings-row";

  const label = document.createElement("label");
  label.className = "settings-label";
  label.textContent = "Theme";

  const select = document.createElement("select");
  select.className = "settings-select";
  select.innerHTML = `
    <option value="dark">Dark</option>
    <option value="light">Light</option>
  `;

  // initialer Wert: localStorage('theme') oder data-theme
  const stored = localStorage.getItem("theme");
  const currentAttr = document.documentElement.getAttribute("data-theme");
  const initial =
    (stored === "dark" || stored === "light") ? stored :
    (currentAttr === "dark" || currentAttr === "light") ? currentAttr :
    "light";

  select.value = initial;

  select.addEventListener("change", () => {
    const v = select.value;
    if (v === "dark" || v === "light") {
      window.__setTheme?.(v); // nutzt deinen bestehenden Setter :contentReference[oaicite:1]{index=1}
    }
  });

  row.appendChild(label);
  row.appendChild(select);

  container.appendChild(head);
  container.appendChild(row);

  // optional: wenn Theme von außen geändert wird (z.B. header toggle), Dropdown synchron halten
  const onMsg = (e) => {
    const d = e?.data;
    if (!d || d.type !== "theme") return;
    const v = d.value;
    if (v === "dark" || v === "light") select.value = v;
  };
  window.addEventListener("message", onMsg);

  return () => window.removeEventListener("message", onMsg);
}

export function openEinstellungenModal({ initialTab = "berechnung" } = {}) {
  const wrap = document.createElement("div");
  wrap.className = "settings-modal";

  const title = document.createElement("h3");
  title.id = "modal-title";
  title.textContent = "Einstellungen";

  // Tabs (wie index.html)
  const tabs = document.createElement("nav");
  tabs.className = "tabs";

  const tabDefs = [
    { id: "berechnung", label: "Berechnung" },
    { id: "flags", label: "Flags" },
    { id: "anzeige", label: "Anzeige" },
  ];

  tabDefs.forEach(({ id, label }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tab";
    btn.dataset.view = id;
    btn.textContent = label;
    tabs.appendChild(btn);
  });

  // EIN Container für den Inhalt
  const content = document.createElement("div");
  content.className = "settings-content";

  // Footer
  const actions = document.createElement("div");
  actions.className = "settings-actions";

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "btn";
  closeBtn.textContent = "Schließen";
  closeBtn.onclick = () => Modal.close();

  actions.appendChild(closeBtn);

  wrap.appendChild(title);
  wrap.appendChild(tabs);
  wrap.appendChild(content);
  wrap.appendChild(actions);

  // Render/Destroy registry
  const tabRenderers = {
    berechnung: renderBerechnung,
    flags: renderFlags,
    anzeige: renderAnzeige,
  };

  let activeTab = null;
  let destroyActive = null;

  function switchTab(view) {
    if (!tabRenderers[view]) view = "berechnung";
    if (view === activeTab) return;

    // Tabs markieren
    tabs.querySelectorAll(".tab").forEach(btn => {
      btn.setAttribute("aria-current", btn.dataset.view === view ? "page" : "");
    });

    // alten Inhalt entfernen + cleanup
    if (typeof destroyActive === "function") destroyActive();
    destroyActive = null;
    content.innerHTML = "";

    // neuen Inhalt rendern
    destroyActive = tabRenderers[view](content) || null;
    activeTab = view;
  }

  tabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (!btn) return;
    switchTab(btn.dataset.view);
  });

  Modal.open(wrap, {
    onOpen: () => switchTab(initialTab),
    onClose: () => {
      if (typeof destroyActive === "function") destroyActive();
    }
  });
}

window.openEinstellungenModal = openEinstellungenModal;
