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
          <div class="wiki-resize-handle wiki-resize-n"></div>
          <div class="wiki-resize-handle wiki-resize-s"></div>
          <div class="wiki-resize-handle wiki-resize-e"></div>
          <div class="wiki-resize-handle wiki-resize-w"></div>

          <div class="wiki-resize-handle wiki-resize-ne"></div>
          <div class="wiki-resize-handle wiki-resize-nw"></div>
          <div class="wiki-resize-handle wiki-resize-se"></div>
          <div class="wiki-resize-handle wiki-resize-sw"></div>
          <div class="wiki-modal-header" data-drag-handle="1">
            <div class="wiki-modal-header-left">
              <button type="button" class="wiki-nav-btn wiki-nav-back" aria-label="Zurück" disabled>←</button>
              <button type="button" class="wiki-nav-btn wiki-nav-forward" aria-label="Vor" disabled>→</button>
            </div>
            <div class="wiki-modal-header-center">
              Windlastrechner – Hilfe
            </div>
            <div class="wiki-modal-header-actions">
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

  const dialog     = root.querySelector(".wiki-modal");
  const bodyEl     = root.querySelector(".wiki-modal-body");
  const btnClose   = root.querySelector(".wiki-close-btn");
  const btnBack    = root.querySelector(".wiki-nav-back");
  const btnForward = root.querySelector(".wiki-nav-forward");
  const dragHandle = root.querySelector("[data-drag-handle]");

  let _isOpen = false;

  // --- Sichtbarkeit --------------------------------------------------------
  function setVisible(v) {
    _isOpen = !!v;
    if (v) {
      dialog.hidden = false;
      dialog.style.display = "flex";
      dialog.setAttribute("aria-hidden", "false");

      // Startposition setzen, falls noch nichts da ist
      if (!dialog.dataset.positioned) {
        dialog.dataset.positioned = "1";

        // 1) sichtbar im DOM, aber unsichtbar (Layout läuft, Bilder laden)
        dialog.style.visibility = "hidden";
        dialog.hidden = false;

        // 2) Warte auf Bilder (falls keine da: sofort)
        const imgs = Array.from(bodyEl.querySelectorAll("img"));
        const pending = imgs.filter(img => !img.complete);

        const proceed = () => {
          const vw = window.innerWidth || document.documentElement.clientWidth;
          const vh = window.innerHeight || document.documentElement.clientHeight;

          const rect = dialog.getBoundingClientRect();
          const width  = Math.min(rect.width  || 420, vw - 32);
          const height = Math.min(rect.height || 300, vh - 32);

          const left = Math.max(16, (vw - width) / 2);
          const topPref = Math.max(16, (vh - height) / 3);
          const topMax  = Math.max(16, vh - height - 16);
          const top = Math.min(topPref, topMax);

          dialog.style.left = `${left}px`;
          dialog.style.top  = `${top}px`;

          // 3) jetzt anzeigen
          dialog.style.visibility = "";
        };

        if (pending.length === 0) {
          requestAnimationFrame(proceed);
        } else {
          let leftToLoad = pending.length;
          const done = () => (--leftToLoad <= 0) && requestAnimationFrame(proceed);

          pending.forEach(img => {
            img.addEventListener("load", done, { once: true });
            img.addEventListener("error", done, { once: true });
          });

          // Fallback: nicht ewig warten
          setTimeout(() => requestAnimationFrame(proceed), 700);
        }

        return; // wichtig: nicht direkt "sichtbar" machen/weiterpositionieren
      }
    } else {
      dialog.hidden = true;
      dialog.style.display = "none";
      dialog.setAttribute("aria-hidden", "true");
    }
  }

  function setContent({ title, node }) {
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

    if (typeof global.closeHelpSearchResults === "function") {
      try {
        global.closeHelpSearchResults();
      } catch (e) {
        console.error("Fehler beim Schließen der Hilfe-Suchergebnisse:", e);
      }
    }
  }

  // --- Buttons -------------------------------------------------------------
  btnClose.addEventListener("click", (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    close();
  });

  // Back/Forward werden von help.js mit Logik gefüllt
  btnBack.addEventListener("click", (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    if (typeof WikiModal.back === "function") {
      WikiModal.back();
    }
  });

  btnForward.addEventListener("click", (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    if (typeof WikiModal.forward === "function") {
      WikiModal.forward();
    }
  });

  // --- Drag & Drop ---------------------------------------------------------
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let startLeft = 0;
  let startTop = 0;

  function onDragStart(ev) {
    if (ev.button !== 0) return; // nur linke Maustaste
    isDragging = true;
    dragStartX = ev.clientX;
    dragStartY = ev.clientY;

    const rect = dialog.getBoundingClientRect();
    startLeft = rect.left;
    startTop  = rect.top;

    dialog.style.left = `${startLeft}px`;
    dialog.style.top  = `${startTop}px`;
    dialog.style.right = "";
    dialog.style.bottom = "";

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

  // --- Resize ---------------------------------------------------------------
  const MIN_WIDTH  = 420;
  const MIN_HEIGHT = 260;

  let isResizing = false;
  let resizeDir = ""; // z.B. "ne", "w", "sw"
  let rsStartX, rsStartY;
  let rsStartW, rsStartH, rsStartL, rsStartT;

  dialog.querySelectorAll(".wiki-resize-handle").forEach(handle => {
    handle.addEventListener("mousedown", ev => {
      ev.preventDefault();
      ev.stopPropagation();

      // Richtung aus Klassenname EXAKT extrahieren (n/s/e/w/ne/nw/se/sw)
      const m = handle.className.match(/\bwiki-resize-(ne|nw|se|sw|n|s|e|w)\b/);
      resizeDir = m ? m[1] : "";

      isResizing = true;

      const rect = dialog.getBoundingClientRect();
      rsStartX = ev.clientX;
      rsStartY = ev.clientY;
      rsStartW = rect.width;
      rsStartH = rect.height;
      rsStartL = rect.left;
      rsStartT = rect.top;

      document.body.style.userSelect = "none";
      document.addEventListener("mousemove", onResizeMove);
      document.addEventListener("mouseup", onResizeEnd);
    });
  });

  function onResizeMove(ev) {
    if (!isResizing) return;

    const dx = ev.clientX - rsStartX;
    const dy = ev.clientY - rsStartY;

    let w = rsStartW;
    let h = rsStartH;
    let l = rsStartL;
    let t = rsStartT;

    // rechts (e) / links (w)
    if (resizeDir.includes("e")) {
      w = Math.max(MIN_WIDTH, rsStartW + dx);
    }
    if (resizeDir.includes("w")) {
      w = Math.max(MIN_WIDTH, rsStartW - dx);
      l = rsStartL + (rsStartW - w);
    }

    // unten (s) / oben (n)
    if (resizeDir.includes("s")) {
      h = Math.max(MIN_HEIGHT, rsStartH + dy);
    }
    if (resizeDir.includes("n")) {
      h = Math.max(MIN_HEIGHT, rsStartH - dy);
      t = rsStartT + (rsStartH - h);
    }

    dialog.style.width  = w + "px";
    dialog.style.height = h + "px";
    dialog.style.left   = l + "px";
    dialog.style.top    = t + "px";
  }

  function onResizeEnd() {
    isResizing = false;
    document.body.style.userSelect = "";
    document.removeEventListener("mousemove", onResizeMove);
    document.removeEventListener("mouseup", onResizeEnd);
  }
  // --- API-Objekt ----------------------------------------------------------
  const WikiModal = {
    open,
    close,
    isOpen: () => _isOpen,
    _elements: { root, dialog, bodyEl, btnBack, btnForward, btnClose },
    setNavState({ canBack, canForward } = {}) {
      btnBack.disabled    = !canBack;
      btnForward.disabled = !canForward;
    },
    // werden in help.js befüllt:
    back: null,
    forward: null,
  };

  global.WikiModal = WikiModal;
})(window);
