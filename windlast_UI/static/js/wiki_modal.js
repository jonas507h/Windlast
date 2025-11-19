// static/js/wiki_modal.js
// Eigenes, leichtgewichtiges Wiki-/Help-Modal
(function (global) {
  const root = (() => {
    let el = document.getElementById("wiki-modal-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "wiki-modal-root";
      el.innerHTML = `
        <div class="wiki-modal" role="dialog" aria-modal="false" aria-label="Hilfe/Wiki" tabindex="-1" hidden>
          <div class="wiki-modal-header" data-drag-handle="1">
            <div class="wiki-modal-title"></div>
            <div class="wiki-modal-header-actions">
              <button type="button" class="wiki-nav-btn wiki-nav-back" aria-label="Zurück" disabled>←</button>
              <button type="button" class="wiki-nav-btn wiki-nav-forward" aria-label="Vor" disabled>→</button>
              <button type="button" class="wiki-close-btn" aria-label="Schließen">×</button>
            </div>
          </div>
          <div class="wiki-modal-body"></div>
        </div>
      `;
      document.body.appendChild(el);
    }
    return el;
  })();

  const dialog   = root.querySelector(".wiki-modal");
  const titleEl  = root.querySelector(".wiki-modal-title");
  const bodyEl   = root.querySelector(".wiki-modal-body");
  const btnClose = root.querySelector(".wiki-close-btn");
  const btnBack  = root.querySelector(".wiki-nav-back");
  const btnFwd   = root.querySelector(".wiki-nav-forward");

  let _isOpen = false;

  function setVisible(v) {
    _isOpen = !!v;
    if (v) {
      dialog.hidden = false;
      dialog.setAttribute("aria-hidden", "false");
    } else {
      dialog.hidden = true;
      dialog.setAttribute("aria-hidden", "true");
    }
  }

  function setContent({ title, node }) {
    titleEl.textContent = title || "Hilfe";
    bodyEl.textContent = "";
    bodyEl.replaceChildren();
    if (node instanceof Node) {
      bodyEl.appendChild(node);
    } else if (node != null) {
      bodyEl.textContent = String(node);
    }
  }

  /**
   * Öffnet das Wiki-Modal.
   * opts: { title: string, contentNode: Node }
   */
  function open(opts = {}) {
    const { title, contentNode } = opts;
    setContent({ title, node: contentNode });
    setVisible(true);
    try {
      dialog.focus({ preventScroll: false });
    } catch {}
  }

  function close() {
    setVisible(false);
  }

  // Buttons
  btnClose.addEventListener("click", close);

  // (Back/Forward werden in späteren Schritten verdrahtet)
  btnBack.addEventListener("click", () => {
    if (typeof WikiModal.back === "function") WikiModal.back();
  });
  btnFwd.addEventListener("click", () => {
    if (typeof WikiModal.forward === "function") WikiModal.forward();
  });

  const WikiModal = {
    open,
    close,
    isOpen: () => _isOpen,
    // diese Elemente brauchen wir später für Drag & History
    _elements: { root, dialog, titleEl, bodyEl, btnBack, btnFwd, btnClose },
    // Platzhalter für spätere Schritte:
    setNavState({ canBack, canForward } = {}) {
      btnBack.disabled = !canBack;
      btnFwd.disabled  = !canForward;
    }
  };

  global.WikiModal = WikiModal;
})(window);
