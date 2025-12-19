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

/**
 * Setzt oder entfernt eine Warnmarkierung für ein Eingabefeld
 * (z. B. bei automatisch angepassten Werten).
 * 
 * @param {HTMLElement} fieldEl - Das <input> oder <select> Element.
 * @param {HTMLElement|null} msgEl - Das Element für den Warnhinweis (optional).
 * @param {boolean} show - Ob die Warnung angezeigt werden soll.
 * @param {string} [msg] - Optional ein neuer Warntext.
 */
export function showFieldWarn(fieldEl, msgEl, show, msg) {
  const wrapper = fieldEl?.closest('.field');
  if (!wrapper) return;

  wrapper.classList.toggle('is-warn', !!show);

  if (msgEl) {
    if (show) {
      if (msg) msgEl.textContent = msg;
      msgEl.hidden = false;
    } else {
      msgEl.hidden = true;
    }
  }
}


/**
 * Entfernt eine Warnung automatisch, sobald der Benutzer
 * mit dem Feld interagiert (focus / click / change).
 * 
 * @param {HTMLElement} fieldEl
 * @param {HTMLElement|null} msgEl
 */
export function clearWarnOnInteract(fieldEl, msgEl) {
  if (!fieldEl) return;

  const clear = () => showFieldWarn(fieldEl, msgEl, false);

  fieldEl.addEventListener('focus', clear);
  fieldEl.addEventListener('mousedown', clear);
  fieldEl.addEventListener('change', clear);
}
