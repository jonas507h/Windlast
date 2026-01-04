// modal.js
// Lightweight Modal Manager (ein Root, simple API: Modal.open(content), Modal.close())
(function (global) {
  // Root erzeugen (einmalig)
  const root = (() => {
    let el = document.getElementById("modal-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "modal-root";
      el.className = "modal-root";
      el.innerHTML = `
        <div class="modal-backdrop" data-close="1"></div>
        <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <button class="modal-close" type="button" aria-label="Schließen" data-close="1">×</button>
          <div class="modal-content"></div>
        </div>
      `;
      document.body.appendChild(el);
    }
    return el;
  })();

  const contentEl = root.querySelector(".modal-content");
  const dialogEl  = root.querySelector(".modal-dialog");

  let lastFocused = null;

  function setVisible(v) {
    root.classList.toggle("is-open", !!v);
    document.body.classList.toggle("modal-open", !!v);
  }

  function setContent(nodeOrString) {
    contentEl.textContent = "";
    contentEl.replaceChildren();
    if (nodeOrString == null) return;
    if (nodeOrString instanceof Node) {
      contentEl.appendChild(nodeOrString);
    } else {
      contentEl.textContent = String(nodeOrString);
    }
  }

  function focusTrap(e) {
    if (!root.classList.contains("is-open")) return;
    if (e.key === "Tab") {
      const focusables = root.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const list = Array.from(focusables).filter(el => el.offsetParent !== null);
      if (!list.length) return;
      const first = list[0];
      const last  = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        last.focus(); e.preventDefault();
      } else if (!e.shiftKey && document.activeElement === last) {
        first.focus(); e.preventDefault();
      }
    }
    if (e.key === "Escape") {
      Modal.close();
    }
  }

  function open(content, { onOpen } = {}) {
    lastFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setContent(content);
    setVisible(true);
    // Fokus ins Dialogfenster
    (root.querySelector(".modal-close") || dialogEl).focus({ preventScroll: true });
    onOpen && onOpen(dialogEl);
  }

  function close() {
    setVisible(false);
    setContent("");
    if (lastFocused && document.contains(lastFocused)) {
      lastFocused.focus({ preventScroll: true });
    }
  }

  // Close-Handler (Backdrop / X-Button)
  root.addEventListener("click", (ev) => {
    const t = ev.target;
    if (t && t.getAttribute && t.getAttribute("data-close") === "1") {
      close();
    }
  });

  // Escape + Focus-Trap
  document.addEventListener("keydown", focusTrap);

  const Modal = { open, close };
  global.Modal = Modal;
})(window);
