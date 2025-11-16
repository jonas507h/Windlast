// config.js
(function () {
  const VERSION = "2.0.0-dev";

  // Echte Build-Rolle (unveränderbar, wird nur gelesen)
  const BUILD_ROLE = "admin"; // "user" | "debug" | "admin" | "godmode"

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

  // 2) Aktive Build-Rolle (simuliert) + aktuelle Laufzeitrolle
  let activeBuildRole = BUILD_ROLE;  // kann NUR im godmode-Build via setBuild geändert werden
  let currentRole     = BUILD_ROLE;  // "user" | "debug" | "admin" | "godmode"

  const LS_KEY = "windlast_ui_role";

  // 3) Admin-Passwort leicht verschleiert
  const ADMIN_PWD_MASK = 37;
  const ADMIN_PWD_BYTES = [
    // dein XOR-codiertes Passwort (hier nur Platzhalter)
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
    // Default: Rolle = aktive Build-Rolle
    currentRole = activeBuildRole;

    let fromStorage = null;
    try {
      fromStorage = localStorage.getItem(LS_KEY);
    } catch (_) {
      fromStorage = null;
    }

    if (!fromStorage || !ROLE_FLAGS[fromStorage]) return;

    // godmode aus Storage nur erlauben, wenn aktiver Build godmode ist
    if (fromStorage === "godmode" && activeBuildRole !== "godmode") {
      try { localStorage.removeItem(LS_KEY); } catch (_) {}
      return;
    }

    // admin aus Storage NICHT automatisch übernehmen, wenn aktiver Build user/debug ist
    if (fromStorage === "admin" && (activeBuildRole === "user" || activeBuildRole === "debug")) {
      try { localStorage.removeItem(LS_KEY); } catch (_) {}
      return;
    }

    // ansonsten darf die gespeicherte Rolle übernommen werden
    currentRole = fromStorage;
  }

  // beim ersten Laden einmal anwenden
  applyRoleFromStorage();

  // 5) DOM-Hook + State
  const state = {
    get role()       { return currentRole; },
    get flags()      { return ROLE_FLAGS[currentRole]; },
    get version()    { return VERSION; },
    get buildRole()  { return BUILD_ROLE; },     // echte Build-Rolle (unveränderbar)
    get activeBuild(){ return activeBuildRole; },// aktuell simulierte Build-Rolle (nur godmode kann ändern)

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

      // godmode-Rolle nur, wenn aktiver Build godmode ist
      if (nextRole === "godmode" && activeBuildRole !== "godmode") {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      // Admin-Wechsel ggf. mit Passwort schützen – abhängig von *aktiver* Build-Rolle
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

    // NUR im godmode-Build vorhanden (siehe unten beim Export von APP_STATE)
    setBuild(nextBuildRole) {
      if (BUILD_ROLE !== "godmode") {
        throw new Error("APP_STATE.setBuild ist nicht verfügbar.");
      }
      if (!ROLE_FLAGS[nextBuildRole]) {
        throw new Error(`Unknown build role: ${nextBuildRole}`);
      }

      // aktive Build-Rolle umschalten
      activeBuildRole = nextBuildRole;
      currentRole = activeBuildRole; // Rolle zurücksetzen

      // Rolle so setzen, wie es ein *echter* Start mit diesem Build tun würde
      applyRoleFromStorage();
      state.applyDomAttributes();

      // Optional: Event für UI, falls du darauf reagieren willst
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
    get buildRole()   { return state.buildRole; },   // echte Build-Rolle
    get activeBuild() { return state.activeBuild; }, // simulierte Build-Rolle
    setRole: state.setRole,
    onRoleChanged(handler) {
      document.addEventListener("ui:role-changed", e => handler(e.detail.role));
    },
  };

  // Nur im godmode-Build: Build-Switcher nach außen freigeben
  if (BUILD_ROLE === "godmode") {
    api.setBuild = function(nextBuildRole) {
      state.setBuild(nextBuildRole);
    };
    api.onBuildChanged = function(handler) {
      document.addEventListener("ui:build-changed", e => handler(e.detail));
    };
  }

  window.APP_STATE = Object.freeze(api);

  // initial DOM-Attribute setzen
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", state.applyDomAttributes);
  else
    state.applyDomAttributes();
})();
