// modal/meldungen.js
import { buildMeldungTooltipContent } from "../tooltip/meldungen.js";

let DEPS = {
  getVM: null,
  getMessages: null,
  Modal: null,
  Tooltip: null,
  buildModal: null,
};

export function configureMeldungen({
  vm,
  getVM,
  getMessages,
  Modal,
  Tooltip,
  buildModal,
} = {}) {
  DEPS.getVM = getVM || (vm ? () => vm : DEPS.getVM);
  if (getMessages) DEPS.getMessages = getMessages;
  if (Modal) DEPS.Modal = Modal;
  if (Tooltip) DEPS.Tooltip = Tooltip;
  if (buildModal) DEPS.buildModal = buildModal;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeSeverity(severity) {
  return String(severity || "").toLowerCase();
}

function fallbackBuildModal(titleText, bodyNode) {
  const wrap = document.createElement("div");

  const h = document.createElement("h3");
  h.textContent = titleText;
  h.className = "modal-title";
  wrap.appendChild(h);

  if (bodyNode instanceof Node) {
    wrap.appendChild(bodyNode);
  }

  return wrap;
}

function renderMessageItem(message) {
  const severity = normalizeSeverity(message?.severity);
  const meta = message?.meta || {};

  return `
    <li
      class="msg-modal-item msg-modal-${escapeHtml(severity)}"
      data-message-code="${escapeHtml(message?.code || "")}"
      data-message-severity="${escapeHtml(severity)}"
      data-message-meta="${escapeHtml(JSON.stringify(meta))}"
    >
      <span class="msg-modal-severity">${escapeHtml(severity || "info")}</span>
      <span class="msg-modal-text">${escapeHtml(message?.text || "")}</span>
    </li>
  `;
}

function renderMessages(messages = []) {
  const root = document.createElement("div");
  root.className = "msg-modal";

  if (!messages.length) {
    root.innerHTML = `<p class="msg-modal-empty">Keine Meldungen vorhanden.</p>`;
    return root;
  }

  root.innerHTML = `
    <ul class="msg-modal-list">
      ${messages.map(renderMessageItem).join("")}
    </ul>
  `;

  return root;
}

export function openMeldungenModal(normKeyOrMessages = null, scenario = null) {
  let messages = [];

  if (Array.isArray(normKeyOrMessages)) {
    messages = normKeyOrMessages;
  } else {
    const normKey = normKeyOrMessages;

    if (DEPS.getMessages) {
      messages = DEPS.getMessages(normKey, scenario) || [];
    } else {
      const VM = DEPS.getVM?.();
      messages = VM?.listMessages?.(normKey, scenario) || [];
    }
  }

  const body = renderMessages(messages);
  const buildModal = DEPS.buildModal || fallbackBuildModal;
  const wrap = buildModal("Meldungen", body);

  (DEPS.Modal || window.Modal)?.open(wrap);
  registerMeldungenTooltip();
}

export function setupMeldungenTriggers() {
  if (setupMeldungenTriggers.__done) return;
  setupMeldungenTriggers.__done = true;

  document.addEventListener("click", (ev) => {
    const badge = ev.target.closest(".results-table .count-badge");
    if (!badge) return;

    const th = badge.closest("th[data-norm-key]");
    if (!th) return;

    const normKey = th.dataset.normKey || null;
    const szenario = th.dataset.szenario || null;

    if (!normKey) return;

    ev.preventDefault();
    ev.stopPropagation();

    openMeldungenModal(normKey, szenario);
  });
}

export function registerMeldungenTooltip() {
  if (registerMeldungenTooltip.__done) return;

  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip) {
    if (!registerMeldungenTooltip.__retries) {
      registerMeldungenTooltip.__retries = 0;
    }

    if (registerMeldungenTooltip.__retries < 50) {
      registerMeldungenTooltip.__retries++;
      setTimeout(registerMeldungenTooltip, 100);
    }

    return;
  }

  Tooltip.register(".msg-modal-item, .msg-modal-item *", {
    predicate: (el) => !!el.closest(".msg-modal-item"),

    content: (_ev, el) => {
      const li = el.closest(".msg-modal-item");
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

  registerMeldungenTooltip.__done = true;
}

export function setupMeldungenUI() {
  registerMeldungenTooltip();
  setupMeldungenTriggers();
}