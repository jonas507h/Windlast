// config.js
(function () {
  const VERSION = "2.0.0-alpha.2";

  // Echte Build-Rolle
  const BUILD_ROLE = "user"; // "user" | "debug" | "admin" | "godmode"

  // 1) Flags pro Rolle definieren.
  const ROLE_FLAGS = {
    user:  Object.freeze({
      show_zwischenergebnisse_tooltip: false,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: false,
      show_meldungen_tooltip: false,
      show_real_kontext_keys: false,
      show_nullpunkt: false,
      show_suche_tooltip: false,
      show_test_options_dropdown: false,
      use_eps_on_anzeige: true,
    }),
    debug: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: true,
      show_doppelte_meldungen: true,
      show_meldungen_tooltip: true,
      show_real_kontext_keys: false,
      show_nullpunkt: true,
      show_suche_tooltip: true,
      show_test_options_dropdown: false,
      use_eps_on_anzeige: true,
    }),
    admin: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: false,
      show_doppelte_meldungen: true,
      show_meldungen_tooltip: true,
      show_real_kontext_keys: false,
      show_nullpunkt: true,
      show_suche_tooltip: true,
      show_test_options_dropdown: false,
      use_eps_on_anzeige: true,
    }),
    godmode: Object.freeze({
      show_zwischenergebnisse_tooltip: true,
      show_nichtZertifiziert_warnung: false,
      show_doppelte_meldungen: true,
      show_meldungen_tooltip: true,
      show_real_kontext_keys: true,
      show_nullpunkt: true,
      show_suche_tooltip: true,
      show_test_options_dropdown: true,
      use_eps_on_anzeige: false,
    }),
  };

  // 2) Aktive Build-Rolle (simuliert) + aktuelle Laufzeitrolle
  let activeBuildRole = BUILD_ROLE;
  let currentRole     = BUILD_ROLE;

  const LS_KEY = "windlast_ui_role";

  // 3) Admin-Passwort
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

  // 4) Rolle aus LocalStorage anwenden, abhängig von der *aktiven* Build-Rolle
  function applyRoleFromStorage() {
    currentRole = activeBuildRole;

    let fromStorage = null;
    try {
      fromStorage = localStorage.getItem(LS_KEY);
    } catch (_) {
      fromStorage = null;
    }

    if (!fromStorage || !ROLE_FLAGS[fromStorage]) return;

    if (fromStorage === "godmode" && activeBuildRole !== "godmode") {
      try { localStorage.removeItem(LS_KEY); } catch (_) {}
      return;
    }

    if (fromStorage === "admin" && (activeBuildRole === "user" || activeBuildRole === "debug")) {
      try { localStorage.removeItem(LS_KEY); } catch (_) {}
      return;
    }

    currentRole = fromStorage;
  }

  applyRoleFromStorage();

  // 5) DOM-Hook + State
  const state = {
    get role()       { return currentRole; },
    get flags()      { return ROLE_FLAGS[currentRole]; },
    get version()    { return VERSION; },
    get buildRole()  { return BUILD_ROLE; },
    get activeBuild(){ return activeBuildRole; },

    applyDomAttributes() {
      document.documentElement.setAttribute("data-role", currentRole);
      document.documentElement.setAttribute("data-build-role", BUILD_ROLE);
      if (activeBuildRole !== BUILD_ROLE) {
        document.documentElement.setAttribute("data-active-build", activeBuildRole);
      } else {
        document.documentElement.removeAttribute("data-active-build");
      }
    },

    setRole(nextRole, { persist = true } = {}) {
      if (!ROLE_FLAGS[nextRole]) {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      if (nextRole === "godmode" && activeBuildRole !== "godmode") {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      const goingToAdmin = nextRole === "admin" && currentRole !== "admin";
      if (goingToAdmin) {
        const buildIsFreeAdmin =
          (activeBuildRole === "admin" || activeBuildRole === "godmode");
        if (!buildIsFreeAdmin) {
          const pwd = typeof window !== "undefined"
            ? window.prompt("Admin-Passwort eingeben:")
            : null;
          if (!checkAdminPassword(pwd)) {
            throw new Error("Falsches Passwort oder Abbruch.");
          }
        }
      }

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

    setBuild(nextBuildRole) {
      if (BUILD_ROLE !== "godmode") {
        throw new Error("APP_STATE.setBuild ist nicht verfügbar.");
      }
      if (!ROLE_FLAGS[nextBuildRole]) {
        throw new Error(`Unknown build role: ${nextBuildRole}`);
      }

      activeBuildRole = nextBuildRole;
      currentRole = activeBuildRole;

      applyRoleFromStorage();
      state.applyDomAttributes();

      document.dispatchEvent(
        new CustomEvent("ui:build-changed", {
          detail: { build: activeBuildRole, role: currentRole }
        })
      );
    },

    get ROLE_FLAGS() { return ROLE_FLAGS; },
  };

  // 6) Globale, schreibgeschützte API aufbauen
  const api = {
    get role()        { return state.role; },
    get flags()       { return state.flags; },
    get version()     { return state.version; },
    get buildRole()   { return state.buildRole; },
    get activeBuild() { return state.activeBuild; },
    setRole: state.setRole,
    onRoleChanged(handler) {
      document.addEventListener("ui:role-changed", e => handler(e.detail.role));
    },
  };

  if (BUILD_ROLE === "godmode") {
    api.setBuild = function(nextBuildRole) {
      state.setBuild(nextBuildRole);
    };
    api.onBuildChanged = function(handler) {
      document.addEventListener("ui:build-changed", e => handler(e.detail));
    };
  }

  window.APP_STATE = Object.freeze(api);

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", state.applyDomAttributes);
  else
    state.applyDomAttributes();
})();
