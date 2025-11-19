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

// --- Modal-Rendering ---
function buildHelpModal(title, bodyHtml, stand) {
  const wrap = document.createElement("div");
  wrap.style.position = "relative";

  const h = document.createElement("h3");
  h.className = "modal-title";
  h.textContent = title || "Hilfe";
  wrap.appendChild(h);

  const body = document.createElement("div");
  body.innerHTML = bodyHtml || "<p>Kein Inhalt.</p>";
  wrap.appendChild(body);

  // --- Bearbeitungsstand-Footer unten rechts ---
  if (stand) {
    const meta = document.createElement("div");
    meta.textContent = `Stand: ${stand}`;
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
  const page = getPage(id);
  const { title, body } = getRenderedPage(id);

  const content = buildHelpModal(
    title,
    body,
    page?.stand || null
  );

  window.Modal?.open(content);
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

// --- Klick-Handling für Links aus Content und anderen Stellen ---

function handleDocumentClick(ev) {
  const a = ev.target.closest('a[data-help-id], a[href^="#help:"]');
  if (!a) return;

  ev.preventDefault();

  const idFromData = a.getAttribute("data-help-id");
  const href = a.getAttribute("href") || "";
  const idFromHref = href.startsWith("#help:") ? href.slice("#help:".length) : null;
  const id = idFromData || idFromHref;
  if (!id) return;

  openHelp(id);
}

// global einmal registrieren
document.addEventListener("click", handleDocumentClick);

// --- Globales API für z.B. den Hilfe-Button ---
window.HELP = {
  open: openHelp,
  openNorm: openNormHelp,
  getNorminfo,
};
