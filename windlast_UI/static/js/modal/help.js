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

import { HELP_CONTACTS } from "../help_content/help_contacts.js";

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
// externe Links:
// [[ext:https://example.com]]         → <a href="https://example.com" class="external">https://example.com</a>
// [[ext:https://example.com|Label]]   → <a href="https://example.com" class="external">Label</a>
// Kontakt-Popover:
// [[contact:key]]             → <button data-contact-id="key">key</button>
// [[contact:key|Label]]      → <button data-contact-id="key">Label</button>
function resolveHelpLinks(html) {
  if (!html || typeof html !== "string") return html || "";

  return html.replace(/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g, (_m, rawId, _rest, label) => {
    const id = String(rawId).trim();

    // --- 1a) EXTERNER LINK --- 
    // Syntax: [[ext:https://example.com | Label]]
    if (id.startsWith("ext:")) {
      const url = id.slice(4).trim();
      const text = label || url;
      const escapedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

      return `<a href="${url}" class="help-link external" target="_blank" rel="noopener noreferrer">${escapedText}</a>`;
    }
    // --- 1b) KONTAKT-POPOVER LINK ---
    // Syntax: [[contact:key]] oder [[contact:key|Label]]
    if (id.startsWith("contact:")) {
      const key = id.slice("contact:".length).trim();
      const text = label || key;
      const escapedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

      // button statt <a>, damit es kein "Navigation" ist
      return `
        <button
          type="button"
          class="help-contact-link"
          data-contact-id="${key}"
          aria-haspopup="dialog"
          aria-expanded="false"
        >${escapedText}</button>
      `;
    }

    // --- 2) INTERNE HÄLFTE (bestehender Code) ---
    const page = PAGES_BY_ID[id];
    const text = label || page?.shortTitle || page?.title || id;
    const escapedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

    return `<a href="#help:${id}" data-help-id="${id}" class="help-link">${escapedText}</a>`;
  });
}

async function loadChangelogIntoHelp() {
  const container = document.getElementById("help-changelog-content");
  if (!container) return;

  try {
    const res = await fetch("/api/v1/meta/changelog", {
      headers: { "Accept": "text/html" }
    });
    if (!res.ok) throw new Error(res.statusText);

    const html = await res.text();
    container.innerHTML = html;
    transformChangelogForHelp(container);
  } catch (e) {
    container.innerHTML =
      "<p><em>Changelog konnte nicht geladen werden.</em></p>";
    console.error("Changelog load failed:", e);
  }
}

function transformChangelogForHelp(container) {
  // Wir erwarten HTML aus Markdown: h1, p, hr, h2 (Version), h3 (Added/Changed...), ul, etc.

  // 0) Erste H1-Überschrift entfernen (z.B. "# Changelog")
  const firstH1 = container.querySelector("h1");
  if (firstH1) {
    firstH1.remove();
  }

  // 1) h3 -> h4 (Added/Changed/Fixed/Known Issues etc.)
  container.querySelectorAll("h3").forEach(h3 => {
    const h4 = document.createElement("h4");
    h4.innerHTML = h3.innerHTML;
    h3.replaceWith(h4);
  });

  // 2) h2-Blöcke in <details> gruppieren
  const children = Array.from(container.childNodes);
  const frag = document.createDocumentFragment();

  let i = 0;
  let versionCount = 0;

  while (i < children.length) {
    const node = children[i];

    // Nur Elemente mit tagName H2 als Version betrachten
    if (node.nodeType === 1 && node.tagName === "H2") {
      versionCount++;

      const details = document.createElement("details");
      details.className = "help-changelog-version";
      if (versionCount === 1) details.open = true; // neueste oben offen

      const summary = document.createElement("summary");
      summary.className = "help-changelog-summary";
      summary.textContent = formatChangelogVersionTitle(node.textContent || "");
      details.appendChild(summary);

      // Content bis zum nächsten H2 einsammeln
      const contentWrap = document.createElement("div");
      contentWrap.className = "help-changelog-body";

      i++; // weiter nach dem H2
      while (i < children.length) {
        const n = children[i];
        if (n.nodeType === 1 && n.tagName === "H2") break;
        contentWrap.appendChild(n);
        i++;
      }

      details.appendChild(contentWrap);
      frag.appendChild(details);
      continue;
    }

    // Alles vor dem ersten H2 (Titel, Intro) 그대로 lassen
    frag.appendChild(node);
    i++;
  }

  container.textContent = "";
  container.appendChild(frag);

  // Wrapper-Klasse für CSS (falls noch nicht vorhanden)
  container.classList.add("help-changelog");
}

function formatChangelogVersionTitle(raw) {
  // Erwartet z.B. "[2.0.0-alpha.1] – 2025-12-18" oder "2.0.0-alpha.1 – 2025-12-18"
  const text = String(raw || "").trim();

  // Version extrahieren (optional in [])
  // Datum extrahieren (YYYY-MM-DD)
  const m = text.match(/\[?([0-9]+\.[0-9]+\.[0-9A-Za-z.-]+)\]?\s*[–-]\s*([0-9]{4})-([0-9]{2})-([0-9]{2})/);
  if (!m) return text;

  const ver = m[1];
  const yyyy = m[2], mm = m[3], dd = m[4];
  return `${ver} – ${dd}.${mm}.${yyyy}`;
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

  // Hook für Suchlogik
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

  // Wenn bereits Text im Feld steht und es fokussiert wird → Panel anzeigen
  input.addEventListener("focus", () => {
    const value = input.value.trim();
    if (value) {
      openHelpSearchResults(input, value);
    }
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
  ensureHelpSearchInput();
  initContactPopoverOnce();

  if (push) {
    // Forward-History abschneiden, falls wir mitten in der History sind
    if (historyIndex < history.length - 1) {
      history.splice(historyIndex + 1);
    }
    history.push(id);
    historyIndex = history.length - 1;
  }

  updateWikiNavState();

  if (id === "app:changelog") {
    loadChangelogIntoHelp();
  }
}

// --- Kontakt-Popover Logik ---
let _contactPopoverInited = false;

function initContactPopoverOnce() {
  if (_contactPopoverInited) return;
  _contactPopoverInited = true;

  const root = document.getElementById("wiki-modal-root");
  if (!root) return;

  const modal = root.querySelector(".wiki-modal");
  const body = root.querySelector(".wiki-modal-body");
  if (!modal || !body) return;

  // Singleton Popover
  const pop = document.createElement("div");
  pop.className = "help-contact-popover";
  pop.hidden = true;
  pop.setAttribute("role", "dialog");
  pop.setAttribute("aria-label", "Kontakt");
  modal.appendChild(pop);

  let currentKey = null;
  let currentAnchor = null;

  function closePopover() {
    if (currentAnchor) currentAnchor.setAttribute("aria-expanded", "false");
    pop.hidden = true;
    pop.innerHTML = "";
    currentKey = null;
    currentAnchor = null;
  }

  function teamsChatUrlFromEmail(email) {
    // gängiger Deep-Link; funktioniert in vielen M365-Tenants
    // (wenn ihr etwas anderes nutzt, hier anpassen)
    return `https://teams.microsoft.com/l/chat/0/0?users=${encodeURIComponent(email)}`;
  }

  async function copyToClipboard(text) {
    // Modern (funktioniert in https / secure contexts)
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_) {}

    // Fallback (auch ohne secure context)
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      ta.style.top = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch (_) {
      return false;
    }
  }

  function flashCopyState(btn, ok) {
    const original = btn.textContent;
    btn.textContent = ok ? "Kopiert" : "Fehler";
    btn.dataset.state = ok ? "ok" : "err";
    window.setTimeout(() => {
      btn.textContent = original;
      delete btn.dataset.state;
    }, 900);
  }

  function renderContact(key) {
    const c = HELP_CONTACTS[key];
    if (!c) {
      pop.innerHTML = `<div class="help-contact-popover-body">
        <div class="help-contact-title">${key}</div>
        <div class="help-contact-row help-contact-empty">Keine Kontaktdaten hinterlegt.</div>
      </div>`;
      return;
    }

    const rows = [];

    if (c.email) {
      const safe = c.email;
      rows.push(`
        <div class="help-contact-row">
          <span class="help-contact-label">E-Mail</span>
          <span class="help-contact-valuewrap">
            <a class="help-contact-value" href="mailto:${safe}">${safe}</a>
            <button type="button" class="help-contact-copy" data-copy="${safe}" aria-label="E-Mail kopieren">Kopieren</button>
          </span>
        </div>
      `);
    }
    if (c.teamsEmail) {
      const url = teamsChatUrlFromEmail(c.teamsEmail);
      rows.push(`
        <div class="help-contact-row">
          <span class="help-contact-label">Teams</span>
          <a class="help-contact-value" href="${url}" target="_blank" rel="noopener noreferrer">
            Chat öffnen
          </a>
        </div>
      `);
    }
    if (c.teams) {
      const url = c.teams;
      rows.push(`
        <div class="help-contact-row">
          <span class="help-contact-label">Teams</span>
          <a class="help-contact-value" href="${url}" target="_blank" rel="noopener noreferrer">
            Chat öffnen
          </a>
        </div>
      `);  
    }
    if (c.mobile) {
      const safe = c.mobile;
      rows.push(`
        <div class="help-contact-row">
          <span class="help-contact-label">Mobil</span>
          <span class="help-contact-valuewrap">
            <a class="help-contact-value" href="tel:${safe}">${safe}</a>
            <button type="button" class="help-contact-copy" data-copy="${safe}" aria-label="Mobilnummer kopieren">Kopieren</button>
          </span>
        </div>
      `);
    }
    if (c.phone) {
      const safe = c.phone;
      rows.push(`
        <div class="help-contact-row">
          <span class="help-contact-label">Festnetz</span>
            <span class="help-contact-valuewrap">
              <a class="help-contact-value" href="tel:${safe}">${safe}</a>
              <button type="button" class="help-contact-copy" data-copy="${safe}" aria-label="Festnetznummer kopieren">Kopieren</button>
            </span>
        </div>
      `);
    }

    pop.innerHTML = `
      <div class="help-contact-popover-head">
        <div class="help-contact-title">${(c.name || key).replace(/</g,"&lt;").replace(/>/g,"&gt;")}</div>
        <button type="button" class="help-contact-close" aria-label="Schließen">×</button>
      </div>
      <div class="help-contact-popover-body">
        ${rows.join("") || `<div class="help-contact-row help-contact-empty">Keine Kontaktdaten vorhanden.</div>`}
      </div>
    `;

    pop.querySelectorAll(".help-contact-copy").forEach((btn) => {
      btn.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();

        const text = btn.getAttribute("data-copy") || "";
        if (!text) return;

        const ok = await copyToClipboard(text);
        flashCopyState(btn, ok);
      });
    });

    pop.querySelector(".help-contact-close")?.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      closePopover();
    });
  }

  function positionPopover(anchorEl) {
    const a = anchorEl.getBoundingClientRect();
    const margin = 8;

    // Popover erst sichtbar machen, damit Maße stimmen
    pop.hidden = false;
    pop.style.left = "0px";
    pop.style.top = "0px";

    const p = pop.getBoundingClientRect();
    const vw = window.innerWidth || document.documentElement.clientWidth;
    const vh = window.innerHeight || document.documentElement.clientHeight;

    // Default: rechts unterhalb
    let left = a.right + margin;
    let top  = a.top;

    // Wenn rechts kein Platz, links daneben
    if (left + p.width > vw - margin) {
      left = a.left - margin - p.width;
    }
    // Wenn immer noch kein Platz: clamp
    left = Math.max(margin, Math.min(left, vw - margin - p.width));

    // Vertikal clamp
    if (top + p.height > vh - margin) {
      top = vh - margin - p.height;
    }
    top = Math.max(margin, top);

    pop.style.left = `${left}px`;
    pop.style.top  = `${top}px`;
  }

  body.addEventListener("click", (ev) => {
    const btn = ev.target.closest?.("[data-contact-id]");
    if (!btn) return;

    ev.preventDefault();
    ev.stopPropagation();

    const key = btn.getAttribute("data-contact-id");
    if (!key) return;

    // Toggle
    if (!pop.hidden && currentKey === key) {
      closePopover();
      return;
    }

    if (currentAnchor) currentAnchor.setAttribute("aria-expanded", "false");
    currentKey = key;
    currentAnchor = btn;
    currentAnchor.setAttribute("aria-expanded", "true");

    renderContact(key);
    positionPopover(btn);
  });

  // Click außerhalb schließt
  document.addEventListener("mousedown", (ev) => {
    if (pop.hidden) return;
    const t = ev.target;
    if (t === pop || pop.contains(t)) return;
    if (currentAnchor && (t === currentAnchor || currentAnchor.contains(t))) return;
    closePopover();
  });

  // ESC schließt
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !pop.hidden) closePopover();
  });

  // Reposition bei Scroll/Resize (Modal-Body scrollt)
  body.addEventListener("scroll", () => {
    if (!pop.hidden && currentAnchor) positionPopover(currentAnchor);
  });
  window.addEventListener("resize", () => {
    if (!pop.hidden && currentAnchor) positionPopover(currentAnchor);
  });
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
  // 3. Hilfe-Bilder umwandeln
  transformHelpImages(body);

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

function transformHelpImages(root) {
  const nodes = root.querySelectorAll("help-img[path], help-img[src]");
  nodes.forEach((node) => {
    const path = node.getAttribute("path") || node.getAttribute("src");
    if (!path) {
      node.remove();
      return;
    }

    const link = node.getAttribute("link") || "";
    const date = node.getAttribute("date") || "";
    const alt  = node.getAttribute("alt") || "";
    const sourceLabel = node.getAttribute("source-label") || link;

    const figure = document.createElement("figure");
    figure.className = "help-figure";

    const img = document.createElement("img");
    img.className = "help-figure-img";
    img.src = path;
    img.alt = alt;
    img.loading = "lazy";

    let imageNode = img;

    // Wenn Link vorhanden: Bild klickbar machen
    if (link) {
      const a = document.createElement("a");
      a.className = "help-figure-link";
      a.href = link;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.appendChild(img);
      imageNode = a;
    }

    figure.appendChild(imageNode);

    // Caption bauen (nur wenn link oder date da ist)
    if (link || date) {
      const caption = document.createElement("figcaption");
      caption.className = "help-figure-caption";

      if (link) {
        const span = document.createElement("span");
        span.className = "help-figure-meta";

        // “Quelle: <Linktext>”
        const a = document.createElement("a");
        a.href = link;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = sourceLabel || link;

        span.append("Quelle: ");
        span.appendChild(a);
        caption.appendChild(span);
      }

      if (date) {
        const span = document.createElement("span");
        span.className = "help-figure-meta";

        const time = document.createElement("time");
        time.setAttribute("datetime", date);
        time.textContent = formatHelpDate(date);

        span.append("Entnommen am: ");
        span.appendChild(time);
        caption.appendChild(span);
      }

      figure.appendChild(caption);
    }

    node.replaceWith(figure);
  });
}

function formatHelpDate(raw) {
  // Erwartet YYYY-MM-DD, gibt DD.MM.YYYY zurück; sonst raw unverändert
  const m = String(raw || "").trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return raw;
  const yyyy = m[1], mm = m[2], dd = m[3];
  return `${dd}.${mm}.${yyyy}`;
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
