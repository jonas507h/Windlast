// static/js/modal/help.js

import { NORM_HELP_PAGES } from "../help_content/norminfo.js";
import { GENERAL_HELP_PAGES } from "../help_content/allgemein.js";

// Später: weitere Content-Module hier zusammenführen:
// import { GENERAL_HELP_PAGES } from "../help_content/allgemein.js";

const PAGES_BY_ID = Object.create(null);

// --- Content registrieren ---
function registerPages(list) {
  for (const p of list || []) {
    if (!p.id) continue;
    PAGES_BY_ID[p.id] = p;
  }
}

registerPages(NORM_HELP_PAGES);
registerPages(GENERAL_HELP_PAGES);

// --- History-Stack für Vor / Zurück ---------------------------------------
const history = [];
let historyIndex = -1;

function updateWikiNavState() {
  if (!window.WikiModal || typeof window.WikiModal.setNavState !== "function") return;
  const canBack    = historyIndex > 0;
  const canForward = historyIndex >= 0 && historyIndex < history.length - 1;
  window.WikiModal.setNavState({ canBack, canForward });
}

// --- Utility: ID-Mapping für Normen ---
// Konvention:
//   Hauptseite:     "norm:" + normKey
//   Alternative:    "norm:" + normKey + ":" + szenario
function normId(normKey, szenario = null) {
  return szenario ? `norm:DIN_${normKey}:${szenario}` : `norm:DIN_${normKey}`;
}

// --- Link-Syntax auflösen ---
// [[page-id]]                → <a data-help-id="page-id">Titel der Seite</a>
// [[page-id|Linktext]]       → <a data-help-id="page-id">Linktext</a>
function resolveHelpLinks(html) {
  if (!html || typeof html !== "string") return html || "";

  return html.replace(/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g, (_m, rawId, _rest, label) => {
    const id = String(rawId).trim();
    const page = PAGES_BY_ID[id];
    const text = label || page?.shortTitle || page?.title || id;
    const escapedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

    return `<a href="#help:${id}" data-help-id="${id}" class="help-link">${escapedText}</a>`;
  });
}

// --- Seitenzugriff ---
function getPage(id) {
  return PAGES_BY_ID[id] || null;
}

function getRenderedPage(id) {
  const page = getPage(id);
  if (!page) {
    return {
      title: "Hilfe",
      body: `
        <p>Für diese Hilfe-ID <code>${id}</code> ist noch kein Inhalt hinterlegt.</p>
      `
    };
  }
  return {
    title: page.title || "Hilfe",
    body: resolveHelpLinks(page.body || "")
  };
}

function navigateTo(id, { push = true } = {}) {
  const page = getPage(id);
  const { title, body } = getRenderedPage(id);
  const contentNode = buildHelpContent(
    title,
    body,
    page?.stand || null
  );

  // ins Wiki-Modal rendern
  window.WikiModal?.open({
    title,
    contentNode
  });

  if (push) {
    // Forward-History abschneiden, falls wir mitten in der History sind
    if (historyIndex < history.length - 1) {
      history.splice(historyIndex + 1);
    }
    history.push(id);
    historyIndex = history.length - 1;
  }

  updateWikiNavState();
}

// --- Modal-Rendering ---
function buildHelpContent(title, bodyHtml, stand) {
  const wrap = document.createElement("div");

  const body = document.createElement("div");
  body.innerHTML = bodyHtml || "<p>Kein Inhalt.</p>";
  transformFAQ(body);
  wrap.appendChild(body);

  if (stand) {
    const meta = document.createElement("div");
    meta.textContent = "Stand: " + stand;
    meta.style.marginTop = "12px";
    meta.style.textAlign = "right";
    meta.style.fontSize = "0.75rem";
    meta.style.opacity = "0.65";
    meta.style.borderTop = "1px solid rgba(0,0,0,0.08)";
    meta.style.paddingTop = "4px";
    wrap.appendChild(meta);
  }

  return wrap;
}

export function openHelp(id) {
  navigateTo(id, { push: true });
}

// Norm-spezifische Convenience
export function openNormHelp(normKey, szenario = null) {
  const id = normId(normKey, szenario);
  openHelp(id);
}

export function getNorminfo(normKey, szenario = null) {
  const id = normId(normKey, szenario);
  const page = getRenderedPage(id);

  // Beibehaltung des alten API-Contracts: { title, body }
  return {
    title: page.title,
    body: page.body
  };
}

function transformFAQ(root) {
  const faqNodes = root.querySelectorAll("faq[question]");

  faqNodes.forEach(faq => {
    const question = faq.getAttribute("question") || "Frage";
    const answerHTML = faq.innerHTML;

    const wrapper = document.createElement("div");
    wrapper.className = "wiki-faq-item";

    const q = document.createElement("div");
    q.className = "wiki-faq-question";

    const arrow = document.createElement("span");
    arrow.className = "wiki-faq-arrow";
    arrow.textContent = "▶";

    const text = document.createElement("span");
    text.textContent = question;

    q.appendChild(arrow);
    q.appendChild(text);

    const ans = document.createElement("div");
    ans.className = "wiki-faq-answer";
    ans.innerHTML = answerHTML;

    wrapper.appendChild(q);
    wrapper.appendChild(ans);

    // Ersetzt das <faq> Element durch das neue FAQ-Widget
    faq.replaceWith(wrapper);

    // Toggle-Logik
    q.addEventListener("click", () => {
      wrapper.classList.toggle("open");
    });
  });
}

// --- Klick-Handling für Links aus Content und anderen Stellen ---

function handleDocumentClick(ev) {
  const a = ev.target.closest('a[data-help-id], a[href^="#help:"]');
  const btn = ev.target.closest('button[data-help-id]');
  if (!a && !btn) return;

  ev.preventDefault();

  const el = a || btn;
  const idFromData = el.getAttribute("data-help-id");
  const href = el.getAttribute("href") || "";
  const idFromHref = href.startsWith("#help:") ? href.slice("#help:".length) : null;
  const id = idFromData || idFromHref;
  if (!id) return;

  openHelp(id);
}

document.addEventListener("click", handleDocumentClick);

// --- Globales API für z.B. den Hilfe-Button ---
window.HELP = {
  open: openHelp,
  openNorm: openNormHelp,
  getNorminfo,
};

if (window.WikiModal) {
  // Zurück-Button
  window.WikiModal.back = function () {
    if (historyIndex > 0) {
      historyIndex--;
      const id = history[historyIndex];
      navigateTo(id, { push: false });
    }
  };

  // Vorwärts-Button
  window.WikiModal.forward = function () {
    if (historyIndex >= 0 && historyIndex < history.length - 1) {
      historyIndex++;
      const id = history[historyIndex];
      navigateTo(id, { push: false });
    }
  };
}
