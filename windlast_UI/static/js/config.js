// config.js
(function () {
  const VERSION = "2.0.0-dev";
  // 1) Flags pro Rolle definieren
  const ROLE_FLAGS = {
    user:  Object.freeze({
      show_zwischenergebnisse_tooltip: false,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: false,
    }),
    debug: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: true,
    }),
    admin: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: false,
      show_doppelte_meldungen: true,
    }),
  };

  // 2) Heutige „harte“ Voreinstellung: einfach hier ändern
  let currentRole = "user"; // "user" | "debug" | "admin"

  // 3) Spätere Runtime-Overrides zulassen (Konsole/Passwort/LocalStorage)
  const LS_KEY = "windlast_ui_role";
  const fromStorage = localStorage.getItem(LS_KEY);
  if (fromStorage && ROLE_FLAGS[fromStorage]) currentRole = fromStorage;

  // 4) Globale, schreibgeschützte API
  const state = {
    get role() { return currentRole; },
    get flags() { return ROLE_FLAGS[currentRole]; },
    get version() { return VERSION; },
    // DOM-Hook für CSS (siehe unten)
    applyDomAttributes() {
      document.documentElement.setAttribute("data-role", currentRole);
      document.documentElement.setAttribute("data-debug", String(state.flags.show_debug_tooltip));
    },
    // sicherer Setter mit Validierung + Persistenz (Konsole/Passwort-UI)
    setRole(nextRole, { persist=true } = {}) {
      if (!ROLE_FLAGS[nextRole]) throw new Error(`Unknown role: ${nextRole}`);
      currentRole = nextRole;
      if (persist) localStorage.setItem(LS_KEY, nextRole);
      state.applyDomAttributes();
      // simple PubSub für UI-Updates
      document.dispatchEvent(new CustomEvent("ui:role-changed", { detail: { role: nextRole }}));
    },
    // Nur Lesen; schützt die Map
    get ROLE_FLAGS() { return ROLE_FLAGS; },
  };

  // global verfügbar machen
  window.APP_STATE = Object.freeze({
    get role() { return state.role; },
    get flags() { return state.flags; },
    get version() { return state.version; },
    setRole: state.setRole,                 // bewusst freigegeben
    onRoleChanged(handler) {                // kleine Helfer-API
      document.addEventListener("ui:role-changed", e => handler(e.detail.role));
    },
  });

  // initial anwenden
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", state.applyDomAttributes);
  else
    state.applyDomAttributes();
})();
