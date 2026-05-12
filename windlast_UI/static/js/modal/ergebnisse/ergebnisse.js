import { getScenarioPath, findGruppe } from "./tree.js";
import { renderErgebnisModalContent } from "./render.js";
import { buildMeldungTooltipContent } from "../../tooltip/meldungen.js";

let DEPS = {
  getVM: null,
  Modal: null,
  Tooltip: null,
  buildModal: null,
};

export function configureErgebnisse({ vm, getVM, Modal, Tooltip, buildModal } = {}) {
  DEPS.getVM = getVM || (vm ? () => vm : DEPS.getVM);
  if (Modal) DEPS.Modal = Modal;
  if (Tooltip) DEPS.Tooltip = Tooltip;
  if (buildModal) DEPS.buildModal = buildModal;
}

function fallbackBuildModal(titleText, bodyNode) {
  const wrap = document.createElement("div");

  const h = document.createElement("h3");
  h.textContent = titleText;
  h.className = "modal-title";
  wrap.appendChild(h);

  if (bodyNode instanceof Node) wrap.appendChild(bodyNode);

  return wrap;
}

export function openErgebnisseModal(normKey, szenario = null) {
  const VM = DEPS.getVM?.();
  if (!VM) return;

  const tree = VM?.payload?.ergebnis || VM?.tree || null;
  if (!tree) return;

  const startPath = getScenarioPath(normKey, szenario);
  if (!startPath.length) return;

  const normStep = startPath[0];
  const scenarioStep = startPath[1];

  const normGroup = normStep
    ? findGruppe(tree, normStep.ebene, normStep.gruppe)
    : null;

  const scenarioGroup = (
    normGroup &&
    scenarioStep
  )
    ? findGruppe(normGroup, scenarioStep.ebene, scenarioStep.gruppe)
    : null;

  const normName =
    normGroup?.label ||
    normGroup?.name ||
    normKey;

  const scenarioName =
    scenarioGroup?.label ||
    scenarioGroup?.name ||
    szenario ||
    "Hauptberechnung";

  const title = `Ergebnisse – ${normName} (${scenarioName})`;

  const body = renderErgebnisModalContent(tree, { startPath });
  const buildModal = DEPS.buildModal || fallbackBuildModal;
  const wrap = buildModal(title, body);

  (DEPS.Modal || window.Modal)?.open(wrap, {
    dialogClass: "modal-dialog-wide",
  });

  registerErgebnisseMetaTooltip();
  registerErgebnisseMessageTooltip();
}

export function registerErgebnisseMetaTooltip() {
  if (registerErgebnisseMetaTooltip.__done) return;

  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip) {
    if (!registerErgebnisseMetaTooltip.__retries) registerErgebnisseMetaTooltip.__retries = 0;
    if (registerErgebnisseMetaTooltip.__retries < 50) {
      registerErgebnisseMetaTooltip.__retries++;
      setTimeout(registerErgebnisseMetaTooltip, 100);
    }
    return;
  }

  Tooltip.register("#modal-root .erg-result-item, #modal-root .erg-result-item *", {
    predicate: (el) => {
      const showFlag = !!(window.APP_STATE?.flags?.show_zwischenergebnisse_tooltip);
      if (!showFlag) return false;
      return !!el.closest(".erg-result-item");
    },
    content: (_ev, el) => {
      const li = el.closest(".erg-result-item");
      if (!li) return "";

      let meta = {};
      try {
        meta = JSON.parse(li.getAttribute("data-meta-json") || "{}");
      } catch {}

      const root = document.createElement("div");
      root.className = "ctx-tooltip";

      const entries = Object.entries(meta || {});
      if (!entries.length) {
        root.textContent = "Keine Meta-Daten.";
        return root;
      }

      for (const [k, v] of entries) {
        const row = document.createElement("div");
        row.className = "ctx-row";

        const key = document.createElement("span");
        key.className = "ctx-k";
        key.textContent = `${k}: `;

        const val = document.createElement("span");
        val.className = "ctx-v";
        val.textContent = typeof v === "string" ? v : JSON.stringify(v);

        row.appendChild(key);
        row.appendChild(val);
        root.appendChild(row);
      }

      return root;
    },
    delay: 80,
  });

  registerErgebnisseMetaTooltip.__done = true;
}

export function registerErgebnisseMessageTooltip() {
  if (registerErgebnisseMessageTooltip.__done) return;

  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip) {
    if (!registerErgebnisseMessageTooltip.__retries) registerErgebnisseMessageTooltip.__retries = 0;
    if (registerErgebnisseMessageTooltip.__retries < 50) {
      registerErgebnisseMessageTooltip.__retries++;
      setTimeout(registerErgebnisseMessageTooltip, 100);
    }
    return;
  }

  Tooltip.register("#modal-root .erg-message-item, #modal-root .erg-message-item *", {
    predicate: (el) => {
      return !!el.closest(".erg-message-item");
    },
    content: (_ev, el) => {
      const li = el.closest(".erg-message-item");
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

  registerErgebnisseMessageTooltip.__done = true;
}

export function setupErgebnisseTriggers() {
  const showFlag = !!(window.APP_STATE?.flags?.open_zwischenergebnis_modal);
  if (!showFlag) return;

  if (setupErgebnisseTriggers.__done) return;
  setupErgebnisseTriggers.__done = true;

  document.addEventListener("click", (ev) => {
    const t = ev.target;

    const generic = t.closest('[data-open="ergebnisse"]');
    if (generic) {
      const normKey = generic.dataset.normKey || generic.closest("[data-norm-key]")?.dataset.normKey;
      const szenario = generic.dataset.szenario || null;
      if (normKey) openErgebnisseModal(normKey, szenario);
      return;
    }

    const cell = t.closest('.results-table td[data-norm-key][data-openable="ergebnisse"]');
    if (cell) {
      const { normKey, szenario } = cell.dataset;
      if (normKey) openErgebnisseModal(normKey, szenario || null);
      return;
    }
  }, { passive: true });
}

export function setupErgebnisseUI() {
  registerErgebnisseMetaTooltip();
  registerErgebnisseMessageTooltip();
  setupErgebnisseTriggers();
}