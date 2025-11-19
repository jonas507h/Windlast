// static/js/wiki_modal.js
// Eigenes, leichtgewichtiges Wiki-/Help-Modal mit Drag&Drop
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
  const dragHandle = root.querySelector("[data-drag-handle]");

  let _isOpen = false;

  // --- Sichtbarkeit --------------------------------------------------------
  function setVisible(v) {
    _isOpen = !!v;
    if (v) {
      dialog.hidden = false;
      dialog.setAttribute("aria-hidden", "false");

      // Falls noch keine explizite Position gesetzt ist: Grund-Startposition
      if (!dialog.style.left && !dialog.style.top) {
        const vw = window.innerWidth || document.documentElement.clientWidth;
        const vh = window.innerHeight || document.documentElement.clientHeight;

        const width  = Math.min(dialog.offsetWidth || 420, vw - 32);
        const height = Math.min(dialog.offsetHeight || 300, vh - 32);

        const left = vw - width - 24; // leicht rechts
        const top  = Math.max(16, vh * 0.15);

        dialog.style.left = `${left}px`;
        dialog.style.top  = `${top}px`;
        dialog.style.right = "";  // sicherheitshalber entfernen
        dialog.style.bottom = "";
      }
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

  // --- Buttons -------------------------------------------------------------
  btnClose.addEventListener("click", close);

  btnBack.addEventListener("click", () => {
    if (typeof WikiModal.back === "function") WikiModal.back();
  });
  btnFwd.addEventListener("click", () => {
    if (typeof WikiModal.forward === "function") WikiModal.forward();
  });

  // --- Drag & Drop ---------------------------------------------------------
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let startLeft = 0;
  let startTop = 0;

  function onDragStart(ev) {
    // Nur linke Maustaste
    if (ev.button !== 0) return;

    isDragging = true;
    dragStartX = ev.clientX;
    dragStartY = ev.clientY;

    // aktuelle Position lesen
    const rect = dialog.getBoundingClientRect();
    startLeft = rect.left;
    startTop  = rect.top;

    // sicherstellen, dass wir in absoluten Koordinaten sind
    dialog.style.left = `${startLeft}px`;
    dialog.style.top  = `${startTop}px`;
    dialog.style.right = "";
    dialog.style.bottom = "";

    // während Drag Textauswahl verhindern
    document.body.style.userSelect = "none";

    document.addEventListener("mousemove", onDragMove);
    document.addEventListener("mouseup", onDragEnd);
  }

  function onDragMove(ev) {
    if (!isDragging) return;

    const dx = ev.clientX - dragStartX;
    const dy = ev.clientY - dragStartY;

    let newLeft = startLeft + dx;
    let newTop  = startTop + dy;

    // Optional: im Viewport halten
    const vw = window.innerWidth || document.documentElement.clientWidth;
    const vh = window.innerHeight || document.documentElement.clientHeight;
    const rect = dialog.getBoundingClientRect();
    const width  = rect.width;
    const height = rect.height;

    const margin = 8;

    newLeft = Math.min(Math.max(newLeft, margin - width * 0.8), vw - margin);
    newTop  = Math.min(Math.max(newTop, margin - 40), vh - margin);

    dialog.style.left = `${newLeft}px`;
    dialog.style.top  = `${newTop}px`;
  }

  function onDragEnd() {
    if (!isDragging) return;
    isDragging = false;

    document.body.style.userSelect = "";
    document.removeEventListener("mousemove", onDragMove);
    document.removeEventListener("mouseup", onDragEnd);
  }

  if (dragHandle) {
    dragHandle.addEventListener("mousedown", onDragStart);
  }

  // --- API-Objekt ----------------------------------------------------------
  const WikiModal = {
    open,
    close,
    isOpen: () => _isOpen,
    _elements: { root, dialog, titleEl, bodyEl, btnBack, btnFwd, btnClose },
    setNavState({ canBack, canForward } = {}) {
      btnBack.disabled = !canBack;
      btnFwd.disabled  = !canForward;
    }
    // back/forward werden später in help.js bzw. History-Step ergänzt
  };

  global.WikiModal = WikiModal;
})(window);
