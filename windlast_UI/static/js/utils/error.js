// static/js/utils/error.js

/**
 * Setzt oder entfernt eine Fehlermarkierung für ein Eingabefeld.
 * 
 * @param {HTMLElement} fieldEl - Das <input> oder <select> Element.
 * @param {HTMLElement|null} msgEl - Das Element für die Fehlermeldung (optional).
 * @param {boolean} show - Ob der Fehler angezeigt werden soll.
 * @param {string} [msg] - Optional eine neue Fehlermeldung.
 */
export function showFieldError(fieldEl, msgEl, show, msg) {
  const wrapper = fieldEl?.closest('.field');
  if (!wrapper) return;

  wrapper.classList.toggle('is-invalid', !!show);

  if (msgEl) {
    if (show) {
      if (msg) msgEl.textContent = msg;
      msgEl.hidden = false;
    } else {
      msgEl.hidden = true;
    }
  }

  fieldEl.setAttribute('aria-invalid', show ? 'true' : 'false');
}
