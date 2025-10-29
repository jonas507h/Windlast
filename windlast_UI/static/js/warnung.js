// warnung.js – einmal pro Laufzeit anzeigen, wenn Flag aktiv
(function (global) {
  let suppressedForSession = false; // Reset bei Programm-Neustart (kein Storage)

  async function confirmNichtZertifiziert() {
    const flags = global.APP_STATE?.flags || {};
    // wenn Flag aus, oder bereits unterdrückt -> sofort weiter
    if (!flags.show_nichtZertifiziert_warnung || suppressedForSession) return true;

    return new Promise((resolve) => {
      const wrap = document.createElement('div');
      wrap.className = 'nz-hinweis';
      wrap.innerHTML = `
        <h2 id="modal-title" class="text-lg" style="margin:0 0 .5rem 0;">Hinweis</h2>
        <p style="margin:0 0 1rem 0;">
          Diese Anwendung liefert <strong>keine zertifizierten statischen Berechnungen</strong>.
          Ergebnisse dienen als <em>Vorab-Abschätzung</em> ohne Gewähr.
        </p>
        <div style="display:flex; gap:.5rem; justify-content:flex-end;">
          <button type="button" class="btn btn-secondary" data-action="ok">OK</button>
          <button type="button" class="btn btn-primary" data-action="hide">Nicht mehr anzeigen</button>
        </div>
      `;

      function closeAnd(proceed, suppress) {
        if (suppress) suppressedForSession = true;
        global.Modal.close();
        resolve(proceed);
      }

      wrap.querySelector('[data-action="ok"]').addEventListener('click', () => closeAnd(true, false));
      wrap.querySelector('[data-action="hide"]').addEventListener('click', () => closeAnd(true, true));

      global.Modal.open(wrap, { onOpen: () => {
        // Fokusfreundlich: zuerst den OK-Button fokussieren
        wrap.querySelector('[data-action="ok"]')?.focus({ preventScroll: true });
      }});
    });
  }

  // global verfügbar
  global.UI_WARN = { confirmNichtZertifiziert };
})(window);
