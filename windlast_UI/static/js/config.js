// config.js
(function () {
  const VERSION = "2.0.0-dev";
  const BUILD_ROLE = "godmode";
  // 1) Flags pro Rolle definieren
  const ROLE_FLAGS = {
    user:  Object.freeze({
      show_zwischenergebnisse_tooltip: false,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: false,
      show_meldungen_tooltip: false,
      show_nullpunkt: false,
    }),
    debug: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: true,
      show_meldungen_tooltip: true,
      show_nullpunkt: true,
    }),
    admin: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: false,
      show_doppelte_meldungen: true,
      show_meldungen_tooltip: true,
      show_nullpunkt: true,
    }),
    godmode: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: true,
      show_meldungen_tooltip: true,
      show_nullpunkt: true,
    }),
  };

  // 2) Startrolle = Build-Rolle (unveränderbar), evtl. durch LocalStorage überschrieben
  let currentRole = BUILD_ROLE; // "user" | "debug" | "admin"

  // 3) Spätere Runtime-Overrides zulassen (Konsole/Passwort/LocalStorage)
  const LS_KEY = "windlast_ui_role";
  const fromStorage = (() => {
    try {
      return localStorage.getItem(LS_KEY);
    } catch (_) {
      return null;
    }
  })();
  if (fromStorage && ROLE_FLAGS[fromStorage]) {
    // Dev-Rolle nur verwenden, wenn Build-Rolle dev ist
    if (fromStorage === "godmode" && BUILD_ROLE !== "godmode") {
      try { localStorage.removeItem(LS_KEY); } catch (_) {}
    } else if (fromStorage === "admin" && (BUILD_ROLE === "user" || BUILD_ROLE === "debug")) {
      // Admin aus LocalStorage NICHT automatisch übernehmen, wenn das Programm
      // nicht als admin/dev gebaut wurde → verhindert trivialen Passwort-Bypass.
      try { localStorage.removeItem(LS_KEY); } catch (_) {}
    } else {
      currentRole = fromStorage;
    }
  }

  const ADMIN_PWD_MASK = 37;
  const ADMIN_PWD_BYTES = [
    20, 23, 22, 17
  ];

  function checkAdminPassword(input) {
    if (!input) return false;
    const expected = ADMIN_PWD_BYTES
      .map(code => String.fromCharCode(code ^ ADMIN_PWD_MASK))
      .join("");
    return input === expected;
  }

  // 4) DOM-Hook
  const state = {
    get role() { return currentRole; },
    get flags() { return ROLE_FLAGS[currentRole]; },
    get version() { return VERSION; },
    get buildRole() { return BUILD_ROLE; },
    applyDomAttributes() {
      document.documentElement.setAttribute("data-role", currentRole);
    },
    setRole(nextRole, { persist = true } = {}) {
      if (!ROLE_FLAGS[nextRole]) {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      // 4. Rolle ("dev") nur, wenn Build damit erzeugt wurde
      if (nextRole === "godmode" && BUILD_ROLE !== "godmode") {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      // Admin-Wechsel ggf. mit Passwort schützen
      const goingToAdmin = nextRole === "admin" && currentRole !== "admin";

      if (goingToAdmin) {
        const buildIsFreeAdmin = (BUILD_ROLE === "admin" || BUILD_ROLE === "godmode");
        if (!buildIsFreeAdmin) {
          // Nur in user/debug-Builds nach Passwort fragen
          const pwd = typeof window !== "undefined"
            ? window.prompt("Admin-Passwort eingeben:")
            : null;

          if (!checkAdminPassword(pwd)) {
            throw new Error("Falsches Passwort oder Abbruch.");
          }
        }
      }

      // Rolle setzen
      currentRole = nextRole;

      if (persist) {
        try {
          localStorage.setItem(LS_KEY, nextRole);
        } catch (_) {
          // Ignorieren, wenn LocalStorage nicht verfügbar ist
        }
      }

      state.applyDomAttributes();
      document.dispatchEvent(
        new CustomEvent("ui:role-changed", { detail: { role: nextRole } })
      );
    },
    get ROLE_FLAGS() { return ROLE_FLAGS; },
  };

  // 5) Globale, schreibgeschützte API
  window.APP_STATE = Object.freeze({
    get role()      { return state.role; },
    get flags()     { return state.flags; },
    get version()   { return state.version; },
    get buildRole() { return state.buildRole; },
    setRole: state.setRole,
    onRoleChanged(handler) {
      document.addEventListener("ui:role-changed", e => handler(e.detail.role));
    },
  });

  // initial anwenden
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", state.applyDomAttributes);
  else
    state.applyDomAttributes();
})();
