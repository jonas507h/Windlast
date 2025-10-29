// modal/ergebnisse.js  (ES module)

import {
  getNormDisplayName,
  displayAltName,
  orderContextEntries,
  prettyKey,
  prettyValHTML,
  formatMathWithSubSup,
} from "../utils/formatierung.js";

// ── Dependencies (per DI setzen, weil ResultsVM nicht global ist)
let DEPS = {
  getVM: null,     // () => ResultsVM-Objekt
  Modal: null,     // optional, sonst window.Modal
  Tooltip: null,   // optional, sonst window.Tooltip
  buildModal: null // optional Fallback
};

export function configureErgebnisse({ vm, getVM, Modal, Tooltip, buildModal } = {}) {
  DEPS.getVM = getVM || (vm ? () => vm : DEPS.getVM);
  if (Modal) DEPS.Modal = Modal;
  if (Tooltip) DEPS.Tooltip = Tooltip;
  if (buildModal) DEPS.buildModal = buildModal;
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

// Öffnet das Ergebnis-Modal (Haupt- oder Szenario-Berechnung)
export function openErgebnisseModal(normKey, szenario = null) {
  const VM = DEPS.getVM?.();
  if (!VM) return;

  const normName = getNormDisplayName(normKey);
  const niceScenario = szenario ? displayAltName(szenario) : null;
  const title = szenario
    ? `Ergebnisse – ${normName} (${niceScenario})`
    : `Ergebnisse – ${normName} (Hauptberechnung)`;

  // Ergebnisse besorgen – gleiche VM-API wie bisher nutzen:
  // Erwartete Methoden: listDocs / listZwischenergebnisse o.ä.
  // Wir greifen defensiv zu: erst szenario-spezifisch, sonst main.
  let items = [];
  if (szenario && typeof VM.listZwischenergebnisse === "function") {
    items = VM.listZwischenergebnisse(normKey, szenario) || [];
  } else if (typeof VM.listZwischenergebnisseMainOnly === "function") {
    items = VM.listZwischenergebnisseMainOnly(normKey) || [];
  } else if (typeof VM.listDocs === "function") {
    // Fallback auf generischere Quelle, falls vorhanden
    items = szenario ? VM.listDocs(normKey, szenario) || [] : VM.listDocs(normKey) || [];
  }

  const buildModal = DEPS.buildModal || _fallbackBuildModal;
  const wrap = buildModal(title, document.createElement("div"));
  const root = wrap.lastElementChild;

  if (!items.length) {
    const p = document.createElement("p");
    p.textContent = "Keine Ergebnisse vorhanden.";
    root.appendChild(p);
  } else {
    // Liste
    const ul = document.createElement("ul");
    ul.className = "doc-list";
    for (const it of items) {
      // Erwartete Felder analog bisher: text / title, context usw.
      const li = document.createElement("li");
      li.className = "doc-li";

      // Hauptzeile
      const line = document.createElement("div");
      line.className = "tt-line";
      line.textContent = it?.title || it?.text || "";
      li.appendChild(line);

      // Tooltip-Kontext ablegen
      const ctx = it?.context || {};
      try { li.setAttribute("data-ctx-json", JSON.stringify(ctx)); } catch {}

      // Optional: zusätzliche Meta (Formel etc.) wie bisher genutzt
      if (it?.formula) {
        li.setAttribute("data-formula", String(it.formula));
      }
      if (it?.formula_source) {
        li.setAttribute("data-formula_source", String(it.formula_source));
      }

      ul.appendChild(li);
    }
    root.appendChild(ul);
  }

  (DEPS.Modal || window.Modal)?.open(wrap);
}

// Tooltip nur innerhalb des Ergebnis-Modals
export function registerErgebnisseContextTooltip() {
  const Tooltip = DEPS.Tooltip || window.Tooltip;
  if (!Tooltip || registerErgebnisseContextTooltip.__done) return;
  registerErgebnisseContextTooltip.__done = true;

  Tooltip.register('#modal-root .doc-list li, #modal-root .doc-list li *', {
    // wir akzeptieren jeden Nachfahren, peilen aber immer die li.doc-li an
    predicate: (el) => !!el.closest('li.doc-li'),
    content: (_ev, el) => {
        try {
            const li = el.closest('li.doc-li');
            if (!li) return "";

            // --- 0) Daten holen ---
            const formula = li.getAttribute('data-formula') || "";
            const formulaSource = li.getAttribute('data-formula_source') || "";

            let ctx = {};
            const raw = li.getAttribute('data-ctx-json');
            if (raw) { try { ctx = JSON.parse(raw); } catch {} }

            // --- 1) Root bauen ---
            const root = document.createElement("div");
            root.className = "ctx-tooltip";

            // --- 2) Formel (falls vorhanden) ---
            if (formula) {
                const f = document.createElement('div');
                f.className = 'ctx-formula';
                f.innerHTML = formatMathWithSubSup(formula);
                root.appendChild(f);
            }

            // --- 3) Quellenangabe (falls vorhanden) ---
            if (formulaSource) {
                const fs = document.createElement('div');
                fs.className = 'ctx-formula-source';
                fs.textContent = `Quelle: ${formulaSource}`;
                root.appendChild(fs);
            }

            // --- 4) Trennlinie, wenn Formel oder Quelle existiert ---
            if (formula || formulaSource) {
                const divider = document.createElement("div");
                divider.className = "tt-divider";
                root.appendChild(divider);
            }

            // --- 5) Kontext ---
            const ordered = orderContextEntries(ctx);
            if (!ordered.length) {
                // (optional leer lassen, wie beim Footer: "Kein Kontext")
                return root;
            }

            for (const [k, v] of ordered) {
                const row = document.createElement('div'); row.className = 'ctx-row';
                const kEl = document.createElement('span'); kEl.className = 'ctx-k'; kEl.textContent = prettyKey(k) + ": ";
                const vEl = document.createElement('span'); vEl.className = 'ctx-v'; vEl.innerHTML = prettyValHTML(k, v);
                row.appendChild(kEl); row.appendChild(vEl); root.appendChild(row);
            }
            return root;
        } catch (e) {
            console.debug("[ergebnisse-tooltip] content error:", e);
            return "";
        }
        },
    delay: 80,
  });
}

// Event-Delegation: klickbare Trigger
export function setupErgebnisseTriggers() {
  if (setupErgebnisseTriggers.__done) return;
  setupErgebnisseTriggers.__done = true;

  document.addEventListener("click", (ev) => {
    const t = ev.target;

    // 1) Generischer Trigger irgendwo im UI:
    //    <anything data-open="ergebnisse" data-norm-key="..." [data-szenario="..."]>
    const generic = t.closest('[data-open="ergebnisse"]');
    if (generic) {
      const normKey = generic.dataset.normKey || generic.closest('[data-norm-key]')?.dataset.normKey;
      const szenario = generic.dataset.szenario || null;
      if (normKey) openErgebnisseModal(normKey, szenario);
      return;
    }

    // 2) Tabellen-Zelle/Badge, die Ergebnisse symbolisiert
    //    Passe die Selektoren ggf. an deine Struktur an
    const cell = t.closest('.results-table td[data-norm-key][data-openable="ergebnisse"]');
    if (cell) {
      const { normKey, szenario } = cell.dataset;
      if (normKey) openErgebnisseModal(normKey, szenario || null);
      return;
    }
  }, { passive: true });
}

// Bequemer Sammelaufruf
export function setupErgebnisseUI() {
  registerErgebnisseContextTooltip();
  setupErgebnisseTriggers();
}
