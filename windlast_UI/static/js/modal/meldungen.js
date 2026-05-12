// modal/meldungen.js (ES module)
import { sortMessagesBySeverity } from "../utils/formatierung.js";
import { buildMeldungTooltipContent } from "../tooltip/meldungen.js";
import { listEbenen, listGruppen, findEbene, findGruppe } from "../utils/tree.js";

let DEPS = {
  getVM: null,
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
} = {}) {
  DEPS.getVM = getVM || (vm ? () => vm : null);

  if (!DEPS.getVM) {
    console.warn("[meldungen] configureMeldungen: getVM/vm fehlt");
  }

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

  const tree = VM?.payload?.ergebnis || VM?.tree || null;

  const normGroup = tree
    ? findGruppe(tree, "norm", normKey)
    : null;

  const scenarioGroup = normGroup && szenario
    ? findGruppe(normGroup, "szenario", szenario)
    : null;

  const normName =
    normGroup?.label ||
    normGroup?.name ||
    normKey ||
    "Unbekannte Norm";

  const scenarioName =
    scenarioGroup?.label ||
    scenarioGroup?.name ||
    szenario ||
    "Hauptberechnung";

  const title = `Meldungen – ${normName} (${scenarioName})`;

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

      li.setAttribute("data-message-code", m.code || "");
      li.setAttribute("data-message-severity", sev || "");
      try {
        li.setAttribute("data-message-meta", JSON.stringify(m.meta || {}));
      } catch {
        li.setAttribute("data-message-meta", "{}");
      }

      ul.appendChild(li); // <- fehlt
    }
    contentRoot.appendChild(ul);
  }

  (DEPS.Modal || window.Modal)?.open(wrap);
}

export function registerMeldungenTooltip() {
  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip || registerMeldungenTooltip.__done) return;
  registerMeldungenTooltip.__done = true;

  Tooltip.register("#modal-root .messages-list li", {
    predicate: (el) => {
      const showFlag = !!(window.APP_STATE?.flags?.show_meldungen_tooltip);
      if (!showFlag) return false;
      return !!el.closest(".messages-list li");
    },

    content: (_ev, el) => {
      const li = el.closest(".messages-list li");
      if (!li) return "";

      let meta = {};
      try {
        meta = JSON.parse(li.getAttribute("data-message-meta") || "{}");
      } catch {}

      return buildMeldungTooltipContent({
        code: li.getAttribute("data-message-code") || "",
        severity: li.getAttribute("data-message-severity") || "",
        meta,
      });
    },

    delay: 80,
  });
}

export function setupMeldungenTriggers() {
  if (setupMeldungenTriggers.__done) return;
  setupMeldungenTriggers.__done = true;

  document.addEventListener("click", (ev) => {
    const badge = ev.target.closest(".results-table .count-badge");
    if (!badge) return;

    const altTh = badge.closest(".results-table .alt-title th[data-norm-key][data-szenario]");
    const mainTh = badge.closest(".results-table thead th[data-norm-key]");

    const th = altTh || mainTh;
    if (!th) return;

    const normKey = th.dataset.normKey;
    const szenario = altTh ? th.dataset.szenario : null;

    ev.preventDefault();
    ev.stopPropagation();

    openMeldungenModal(normKey, szenario);
  });
}

export function setupMeldungenUI() {
  registerMeldungenTooltip();
  setupMeldungenTriggers();
}
