// validierung.js – einfache UI-Preflight-Prüfung vor der Berechnung
(function (global) {

  const MAX_BAUELEMENTE = 100;

  async function validateKonstruktion(konstruktion) {
    const fehler = [];

    const anzahlBauelemente =
      Array.isArray(konstruktion?.bauelemente)
        ? konstruktion.bauelemente.length
        : 0;

    if (anzahlBauelemente > MAX_BAUELEMENTE) {
      fehler.push(
        `Die Konstruktion enthält ${anzahlBauelemente} Bauelemente. ` +
        `Zulässig sind maximal ${MAX_BAUELEMENTE}.`
      );
    }

    if (fehler.length === 0) {
      return true;
    }

    return showValidationError(fehler);
  }


  function showValidationError(fehler) {
    return new Promise((resolve) => {
      const wrap = document.createElement('div');
      wrap.className = 'validierungsfehler';

      const liste = fehler
        .map(text => `<li>${escapeHtml(text)}</li>`)
        .join('');

      wrap.innerHTML = `
        <h2
          id="modal-title"
          class="text-lg"
          style="margin:0 0 .5rem 0;"
        >
          Berechnung nicht möglich
        </h2>

        <p style="margin:0 0 .75rem 0;">
          Die Konstruktion kann in dieser Form nicht berechnet werden:
        </p>

        <ul style="margin:0 0 1rem 1.25rem;">
          ${liste}
        </ul>

        <div style="display:flex; justify-content:flex-end;">
          <button
            type="button"
            class="btn btn-primary"
            data-action="ok"
          >
            OK
          </button>
        </div>
      `;

      function close() {
        global.Modal.close();
        resolve(false);
      }

      wrap
        .querySelector('[data-action="ok"]')
        .addEventListener('click', close);

      global.Modal.open(wrap, {
        onOpen: () => {
          wrap
            .querySelector('[data-action="ok"]')
            ?.focus({ preventScroll: true });
        },
      });
    });
  }


  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }


  global.UI_VALIDATION = {
    validateKonstruktion,
  };

})(window);