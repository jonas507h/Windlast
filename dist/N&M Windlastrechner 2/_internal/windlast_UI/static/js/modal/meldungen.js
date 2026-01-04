// modal/meldungen.js (ES module)
import {
  getNormDisplayName,
  displayAltName,
  orderContextEntries,
  prettyKey,
  prettyValHTML,
  sortMessagesBySeverity,
} from "../utils/formatierung.js";

let DEPS = {
  // Pflicht
  getVM: null, // () => ResultsVM-Objekt

  // Optional (mit Fallbacks)
  getNormDisplayName,
  displayAltName,
  orderContextEntries,
  prettyKey,
  prettyValHTML,
  buildModal: null,
  Modal: null,
  Tooltip: null,
};

// Aufrufer konfiguriert Dependencies einmalig
export function configureMeldungen({
  vm,
  getVM,
  buildModal,
  Modal,
  Tooltip,
  getNormDisplayName: getNormDisplayNameOverride,
  displayAltName: displayAltNameOverride,
  orderContextEntries: orderContextEntriesOverride,
  prettyKey: prettyKeyOverride,
  prettyValHTML: prettyValHTMLOverride,
} = {}) {
  DEPS.getVM = getVM || (vm ? () => vm : null);
  if (!DEPS.getVM) {
    console.warn("[meldungen] configureMeldungen: getVM/vm fehlt");
  }
  if (getNormDisplayNameOverride) DEPS.getNormDisplayName = getNormDisplayNameOverride;
  if (displayAltNameOverride) DEPS.displayAltName = displayAltNameOverride;
  if (orderContextEntriesOverride) DEPS.orderContextEntries = orderContextEntriesOverride;
  if (prettyKeyOverride) DEPS.prettyKey = prettyKeyOverride;
  if (prettyValHTMLOverride) DEPS.prettyValHTML = prettyValHTMLOverride;
  if (buildModal) DEPS.buildModal = buildModal;
  if (Modal) DEPS.Modal = Modal;
  if (Tooltip) DEPS.Tooltip = Tooltip;
}

function _fallbackBuildModal(titleText, bodyNodeOrHtml) {
  const wrap = document.createElement("div");
  const h = document.createElement("h3");
  h.textContent = titleText;
  h.className = "modal-title";
  wrap.appendChild(h);
  const cont = document.createElement("div");
  if (typeof bodyNodeOrHtml === "string") cont.innerHTML = bodyNodeOrHtml;
  else if (bodyNodeOrHtml instanceof Node) cont.appendChild(bodyNodeOrHtml);
  wrap.appendChild(cont);
  return wrap;
}

// Hilfsfunktion: nur erstes Vorkommen je Anzeige-Text behalten
function dedupeMessagesByText(list) {
  const seen = new Set();
  const out = [];
  for (const m of (list || [])) {
    const key = String(m?.text ?? "")
      .replace(/\s+/g, " ")  // Whitespace normalisieren (wie Anzeige)
      .trim();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(m);
  }
  return out;
}

export function openMeldungenModal(normKey, szenario = null) {
  const VM = DEPS.getVM?.();
  if (!VM) return;

  const msgsRaw = szenario
    ? (VM.listMessages ? VM.listMessages(normKey, szenario) : [])
    : (VM.listMessagesMainOnly ? VM.listMessagesMainOnly(normKey) : []);

  // Flag: doppelte Meldungen anzeigen?
  const showDup = !!(window.APP_STATE?.flags?.show_doppelte_meldungen);
  const msgs = showDup ? msgsRaw : dedupeMessagesByText(msgsRaw);

  const normName = DEPS.getNormDisplayName(normKey);
  const niceScenario = szenario ? DEPS.displayAltName(szenario) : null;
  const title = szenario
    ? `Meldungen – ${normName} (${niceScenario})`
    : `Meldungen – ${normName} (Hauptberechnung)`;

  const buildModal = DEPS.buildModal || _fallbackBuildModal;
  const wrap = buildModal(title, document.createElement("div"));
  const contentRoot = wrap.lastElementChild;

  // --- Fragezeichen-Button ---
  const titleEl = wrap.querySelector(".modal-title");
  if (titleEl) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "help-icon-btn";
    btn.style.marginLeft = "8px";
    btn.textContent = "?";

    const helpId = `meldungen:allgemein`;

    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      ev.preventDefault();
      if (window.HELP?.open) {
        window.HELP.open(helpId);
      }
    });

    // Button in den Titel hängen
    titleEl.appendChild(btn);
  }

  if (!msgs || msgs.length === 0) {
    const p = document.createElement("p");
    p.textContent = "Keine Meldungen vorhanden.";
    contentRoot.appendChild(p);
  } else {
    const ul = document.createElement("ul");
    ul.className = "messages-list";
    for (const m of sortMessagesBySeverity(msgs)) {
      const li = document.createElement("li");
      const line = document.createElement("div");
      const sev = (m.severity || "").toLowerCase();
      line.className = `tt-line ${["error","warn","hint","info"].includes(sev) ? sev : "info"}`;
      line.textContent = m.text || "";
      li.appendChild(line);

      // Tooltip-Daten
      let ctx = {};
      try { ctx = m?.context || {}; } catch {}
      try { li.setAttribute("data-ctx-json", JSON.stringify(ctx)); } catch {}
      ul.appendChild(li);
    }
    contentRoot.appendChild(ul);
  }

  (DEPS.Modal || window.Modal)?.open(wrap);
}

export function registerMeldungenContextTooltip() {
  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip || registerMeldungenContextTooltip.__done) return;
  registerMeldungenContextTooltip.__done = true;

  Tooltip.register('#modal-root .messages-list li', {
    predicate: (el) => {
      const showFlag = !!(window.APP_STATE?.flags?.show_meldungen_tooltip);
      if (!showFlag) return false;
      return !!el.closest('li');
    },
    content: (_ev, el) => {
      const li = el.closest('li');
      if (!li) return "";
      let ctx = {};
      try { ctx = JSON.parse(li.getAttribute('data-ctx-json') || "{}"); } catch {}
      const ordered = DEPS.orderContextEntries(ctx);
      if (!ordered.length) return "";

      const root = document.createElement("div");
      root.className = "ctx-tooltip";
      for (const [k, v] of ordered) {
        const row = document.createElement('div');
        row.className = 'ctx-row';
        const kEl = document.createElement('span');
        kEl.className = 'ctx-k';
        kEl.textContent = DEPS.prettyKey(k) + ": ";
        const vEl = document.createElement('span');
        vEl.className = 'ctx-v';
        vEl.innerHTML = DEPS.prettyValHTML(k, v);
        row.appendChild(kEl);
        row.appendChild(vEl);
        root.appendChild(row);
      }
      return root;
    },
    delay: 80
  });
}

export function setupMeldungenTriggers() {
  if (setupMeldungenTriggers.__done) return;
  setupMeldungenTriggers.__done = true;

  document.addEventListener("click", (ev) => {
    const t = ev.target;

    // ✅ Nur Klicks auf Count-Badges (oder deren Kinder)
    const badge = t.closest(".results-table .count-badge");
    if (!badge) return;

    // ✅ Hauptberechnung: Badge im thead-th
    const thHead = badge.closest(".results-table thead th[data-norm-key]");
    if (thHead) {
      const normKey = thHead.dataset.normKey;
      if (normKey) openMeldungenModal(normKey, null);
      return;
    }

    // ✅ Alternativen: Badge im alt-title-th mit szenario
    const thAlt = badge.closest(".results-table .alt-title th[data-norm-key][data-szenario]");
    if (thAlt) {
      const { normKey, szenario } = thAlt.dataset;
      if (normKey && szenario) openMeldungenModal(normKey, szenario);
      return;
    }

    // optional: generischer Trigger bleibt, aber nur wenn du ihn wirklich noch brauchst:
    // const generic = t.closest('[data-open="meldungen"]');
    // ...
  }, { passive: true });
}

export function setupMeldungenUI() {
  registerMeldungenContextTooltip();
  setupMeldungenTriggers();
}
