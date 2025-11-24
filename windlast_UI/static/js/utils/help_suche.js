// static/js/utils/help_suche.js

/**
 * Später: Aufbau des Suchindex etc.
 * Aktuell nur ein Platzhalter-Interface, damit die Aufrufe schon stehen.
 */

/**
 * Wird aufgerufen, sobald das Suchfeld existiert.
 * Hier könntest du später z.B. Keyboard-Shortcuts, ESC-Handling etc. andocken.
 */
export function initHelpSearch(inputElement) {
  // Aktuell bewusst leer.
}

/**
 * Später: echte Suche über HELP-Pages.
 * Für den Moment einfach nur ein Dummy.
 */
export function runHelpSearch(query) {
  const q = String(query || "").trim();
  if (!q) {
    return [];
  }

  // Rückgabe-Struktur kannst du dir schon mal merken:
  // [{ id, title, shortTitle, excerpt, path }, ...]
  return [];
}
