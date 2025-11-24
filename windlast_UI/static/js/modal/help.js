// static/js/modal/help.js

import { NORM_HELP_PAGES } from "../help_content/norminfo.js";
import { GENERAL_HELP_PAGES } from "../help_content/allgemein.js";
import { MELDUNGEN_HELP_PAGES } from "../help_content/meldungen.js";
import { HEADER_HELP_PAGES } from "../help_content/header.js";
import { TOR_HELP_PAGES } from "../help_content/tor.js";
import { STEHER_HELP_PAGES } from "../help_content/steher.js";
import { TISCH_HELP_PAGES } from "../help_content/tisch.js";
import { ERGEBNISSE_HELP_PAGES } from "../help_content/ergebnisse.js";
import { ZWISCHENERGEBNISSE_HELP_PAGES } from "../help_content/zwischenergebnisse.js";

// Welche Seite soll der globale "Hilfe"-Startpunkt sein?
export const HELP_ROOT_ID = "app:start"; 

// Später: weitere Content-Module hier zusammenführen:
// import { GENERAL_HELP_PAGES } from "../help_content/allgemein.js";

import { initHelpSearch } from "../utils/help_suche.js";
import {
  openHelpSearchResults,
  closeHelpSearchResults
} from "./suchergebnisse.js";

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
registerPages(MELDUNGEN_HELP_PAGES);
registerPages(HEADER_HELP_PAGES);
registerPages(TOR_HELP_PAGES);
registerPages(STEHER_HELP_PAGES);
registerPages(TISCH_HELP_PAGES);
registerPages(ERGEBNISSE_HELP_PAGES);
registerPages(ZWISCHENERGEBNISSE_HELP_PAGES);

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

function ensureHelpSearchInput() {
  // Root des Wiki-Modals, wie in wiki_modal.js angelegt
  const root = document.getElementById("wiki-modal-root");
  if (!root) return;

  const headerCenter = root.querySelector(".wiki-modal-header-center");
  if (!headerCenter) return;

  // Schon vorhanden? → nur zurückgeben
  let input = headerCenter.querySelector("input.help-search-input");
  if (input) {
    return input;
  }

  // Bisherigen Titeltext entfernen ("Windlastrechner – Hilfe")
  headerCenter.textContent = "";

  // Neues Suchfeld anlegen
  input = document.createElement("input");
  input.type = "search";
  input.className = "help-search-input";
  input.placeholder = "Hilfe durchsuchen …";
  input.autocomplete = "off";
  input.spellcheck = false;

  // Baseline-Styles (kannst du später komplett per CSS überschreiben)
  input.style.width = "100%";
  input.style.maxWidth = "360px";
  input.style.padding = "4px 8px";
  input.style.borderRadius = "4px";
  input.style.border = "1px solid rgba(0,0,0,0.2)";
  input.style.fontSize = "0.9rem";

  headerCenter.appendChild(input);

  // Hook für spätere Suchlogik
  initHelpSearch(input);

  // Input-Event: Platzhalter-Ergebnis-Modal öffnen/schließen
  input.addEventListener("input", () => {
    const value = input.value.trim();
    if (!value) {
      closeHelpSearchResults();
      return;
    }
    openHelpSearchResults(input, value);
  });

  input.addEventListener("mousedown", (ev) => {
    ev.stopPropagation();
  });

  // Optional: ESC schließt nur das Ergebnis-Modal
  input.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      if (input.value) {
        input.value = "";
        closeHelpSearchResults();
        ev.stopPropagation();
        ev.preventDefault();
      }
    }
  });

  return input;
}

function navigateTo(id, { push = true } = {}) {
  const page = getPage(id);
  const { title, body } = getRenderedPage(id);
  const contentNode = buildHelpContent(
    id,
    title,
    body,
    page?.stand || null
  );

  // ins Wiki-Modal rendern
  window.WikiModal?.open({
    title,
    contentNode
  });

  ensureHelpSearchInput();

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
function buildHelpContent(id, title, bodyHtml, stand) {
  const wrap = document.createElement("div");

  // --- Breadcrumb oben ---
  const breadcrumb = buildBreadcrumb(id);
  wrap.appendChild(breadcrumb);

  // --- Seitentitel im Inhalt ---
  const pageTitleEl = document.createElement("h2");
  pageTitleEl.className = "wiki-page-title wiki-title-level-0";
  pageTitleEl.textContent = title || "Hilfe";
  wrap.appendChild(pageTitleEl);

  // --- Hauptinhalt ---
  const body = document.createElement("div");
  body.innerHTML = bodyHtml || "<p>Kein Inhalt.</p>";

  // 1. Includes auflösen (help-include)
  transformIncludes(body);
  // 2. FAQ-Elemente in klickbare Blöcke umwandeln
  transformFAQ(body);

  wrap.appendChild(body);

  // --- Stand unten rechts ---
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

function transformIncludes(root, visited = new Set(), depth = 0) {
  const nodes = root.querySelectorAll("help-include[page]");

  nodes.forEach(node => {
    const pageId = node.getAttribute("page");
    if (!pageId) {
      node.remove();
      return;
    }

    // optionale Attribute
    const showTitleAttr = node.getAttribute("show-title");
    const showTitle = showTitleAttr == null
      ? true
      : !/^(false|0)$/i.test(showTitleAttr.trim());

    const overrideTitle = node.getAttribute("title");
    const autoLevelAttr = node.getAttribute("auto-level");
    const autoLevel = autoLevelAttr != null
      ? !/^(false|0)$/i.test(autoLevelAttr.trim())
      : false;

    // Zyklen vermeiden
    if (visited.has(pageId)) {
      const warn = document.createElement("div");
      warn.textContent = `(Zirkuläre Hilfe-Einbindung: ${pageId})`;
      warn.style.fontStyle = "italic";
      warn.style.fontSize = "0.8rem";
      node.replaceWith(warn);
      return;
    }

    const page = getPage(pageId);
    if (!page) {
      const missing = document.createElement("div");
      missing.textContent = `Hinweis-Seite "${pageId}" nicht gefunden.`;
      missing.style.fontStyle = "italic";
      missing.style.fontSize = "0.8rem";
      node.replaceWith(missing);
      return;
    }

    visited.add(pageId);

    const { title, body } = getRenderedPage(pageId);
    const container = document.createElement("div");
    container.className = "wiki-include-block";

    // --- Überschrift im Include ---
    if (showTitle) {
      // Level bestimmen
      let level;
      if (autoLevel) {
        // Haupt h2 = Level 0 → Includes starten bei 1
        level = Math.min(depth + 1, 6);
      } else {
        // ohne auto-level: exakt wie Haupttitel
        level = 0;
      }

      // Tag wählen (für Semantik, Optik kommt über Level-Klassen)
      const tagName = level <= 0 ? "h2"
                     : level === 1 ? "h3"
                     : level === 2 ? "h4"
                     : "h5";

      const h = document.createElement(tagName);
      h.className = `wiki-page-title wiki-title-level-${level}`;
      h.textContent = overrideTitle || title || pageId;
      container.appendChild(h);
    }

    // Body der eingebetteten Seite
    const inner = document.createElement("div");
    inner.innerHTML = body || "";

    // rekursive Includes im Inneren (Tiefe +1)
    transformIncludes(inner, visited, depth + 1);

    // FAQ im Include transformieren
    transformFAQ(inner);

    container.appendChild(inner);

    node.replaceWith(container);
    visited.delete(pageId);
  });
}

function buildBreadcrumb(id) {
  const page = getPage(id);

  const nav = document.createElement("nav");
  nav.className = "wiki-breadcrumb";
  nav.setAttribute("aria-label", "Hilfe-Navigation");

  const ol = document.createElement("ol");
  nav.appendChild(ol);

  function addCrumb(label, targetId, isLast) {
    const li = document.createElement("li");

    if (targetId && !isLast) {
      const a = document.createElement("a");
      a.href = "#help:" + targetId;
      a.setAttribute("data-help-id", targetId);
      a.textContent = label;
      li.appendChild(a);
    } else {
      const span = document.createElement("span");
      span.textContent = label;
      li.appendChild(span);
    }

    ol.appendChild(li);
  }

  // Root: "Hilfe"
  addCrumb("Hilfe", HELP_ROOT_ID, false);

  const pathIds = Array.isArray(page?.pfad) ? page.pfad : [];

  // Zwischenstationen aus pfad[]
  for (const pid of pathIds) {
    const pPage  = getPage(pid);
    const label  = pPage?.shortTitle || pPage?.title || pid;
    addCrumb(label, pid, false);
  }

  // Aktuelle Seite als letzter Eintrag (kein Link)
  const currentLabel = page?.shortTitle || page?.title || id;
  addCrumb(currentLabel, null, true);

  return nav;
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
