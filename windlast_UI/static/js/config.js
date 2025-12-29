// config.js
(function () {
  const VERSION = "2.0.0-alpha.2";

  // Echte Build-Rolle
  const BUILD_ROLE = "user"; // "user" | "debug" | "admin" | "godmode"

  // 1) Flags pro Rolle definieren (dynamisch)
  // value: aktueller Zustand
  // lock:  true => nicht änderbar, false => änderbar (persistiert pro Rolle)
  const ROLE_FLAG_DEFS = {
    user: {
      show_zwischenergebnisse_tooltip: { value: false, lock: true  },
      show_nichtZertifiziert_warnung:  { value: true,  lock: true  },
      show_doppelte_meldungen:         { value: false, lock: false },
      show_meldungen_tooltip:          { value: false, lock: false },
      show_real_kontext_keys:          { value: false, lock: true  },
      show_nullpunkt:                  { value: false, lock: false },
      show_suche_tooltip:              { value: false, lock: false },
      show_test_options_dropdown:      { value: false, lock: true  },
      use_eps_on_anzeige:              { value: true,  lock: true  },
    },
    debug: {
      show_zwischenergebnisse_tooltip: { value: true,  lock: true  },
      show_nichtZertifiziert_warnung:  { value: true,  lock: true  },
      show_doppelte_meldungen:         { value: true,  lock: false },
      show_meldungen_tooltip:          { value: true,  lock: false },
      show_real_kontext_keys:          { value: false, lock: true  },
      show_nullpunkt:                  { value: true,  lock: false },
      show_suche_tooltip:              { value: true,  lock: false },
      show_test_options_dropdown:      { value: false, lock: true  },
      use_eps_on_anzeige:              { value: true,  lock: true  },
    },
    admin: {
      show_zwischenergebnisse_tooltip: { value: true,  lock: true  },
      show_nichtZertifiziert_warnung:  { value: false, lock: true  },
      show_doppelte_meldungen:         { value: true,  lock: false },
      show_meldungen_tooltip:          { value: true,  lock: false },
      show_real_kontext_keys:          { value: false, lock: true  },
      show_nullpunkt:                  { value: true,  lock: false },
      show_suche_tooltip:              { value: true,  lock: false },
      show_test_options_dropdown:      { value: false, lock: true  },
      use_eps_on_anzeige:              { value: true,  lock: true  },
    },
    godmode: {
      show_zwischenergebnisse_tooltip: { value: true,  lock: true  },
      show_nichtZertifiziert_warnung:  { value: false, lock: true  },
      show_doppelte_meldungen:         { value: true,  lock: false },
      show_meldungen_tooltip:          { value: true,  lock: false },
      show_real_kontext_keys:          { value: true,  lock: false },
      show_nullpunkt:                  { value: true,  lock: false },
      show_suche_tooltip:              { value: true,  lock: false },
      show_test_options_dropdown:      { value: true,  lock: false },
      use_eps_on_anzeige:              { value: false, lock: false },
    },
  };

  const LS_ROLE_KEY  = "windlast_ui_role";
  const LS_FLAGS_KEY = "windlast_ui_flags_by_role";
  const LS_KEY       = LS_ROLE_KEY;

  // Laufzeitkopie (wird aus DEFS + Overrides gebaut)
  const roleFlagState = structuredClone(ROLE_FLAG_DEFS);

  // Overrides laden (nur value pro Rolle/Key)
  function loadFlagOverrides() {
    let raw = null;
    try { raw = localStorage.getItem(LS_FLAGS_KEY); } catch (_) {}
    if (!raw) return;

    let data = null;
    try { data = JSON.parse(raw); } catch (_) { return; }
    if (!data || typeof data !== "object") return;

    for (const role of Object.keys(roleFlagState)) {
      const perRole = data[role];
      if (!perRole || typeof perRole !== "object") continue;

      for (const key of Object.keys(perRole)) {
        if (!roleFlagState[role]?.[key]) continue;
        // override nur value; lock bleibt aus dem Code
        roleFlagState[role][key].value = !!perRole[key];
      }
    }
  }

  function persistFlagOverride(role, key, value) {
    let data = {};
    try { data = JSON.parse(localStorage.getItem(LS_FLAGS_KEY) || "{}"); } catch (_) {}
    if (!data || typeof data !== "object") data = {};
    if (!data[role] || typeof data[role] !== "object") data[role] = {};
    data[role][key] = !!value;
    try { localStorage.setItem(LS_FLAGS_KEY, JSON.stringify(data)); } catch (_) {}
  }

  // booleans für Kompatibilität (APP_STATE.flags wie bisher)
  function getFlagsBooleanMap(role) {
    const src = roleFlagState[role] || {};
    const out = {};
    for (const k of Object.keys(src)) out[k] = !!src[k].value;
    return out;
  }

  // lock-map fürs UI/Checkbox
  function getFlagsLockMap(role) {
    const src = roleFlagState[role] || {};
    const out = {};
    for (const k of Object.keys(src)) out[k] = !!src[k].lock;
    return out;
  }

  loadFlagOverrides();

  // 2) Aktive Build-Rolle (simuliert) + aktuelle Laufzeitrolle
  let activeBuildRole = BUILD_ROLE;
  let currentRole     = BUILD_ROLE;

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

  let roleChangeInFlight = false;

  async function requestAdminPasswordViaModal() {
    // Modal.js wird in index.html später geladen; falls jemand super-früh admin will:
    if (typeof window.Modal === "undefined") {
      const pwd = window.prompt("Admin-Passwort eingeben:");
      return pwd;
    }

    // passwort.js ist ein ES-module (export function askAdminPassword)
    const mod = await import("/static/js/modal/passwort.js");
    if (!mod?.askAdminPassword) {
      // Fallback (sollte praktisch nie passieren)
      return window.prompt("Admin-Passwort eingeben:");
    }
    return await mod.askAdminPassword();
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

    if (!fromStorage || !roleFlagState[fromStorage]) return;

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

  // Admin-Unlock (one-shot) — wird nach erfolgreicher Passwortprüfung gesetzt
  let adminUnlockUntil = 0;

  function unlockAdminOnce(ttlMs = 30_000) {
    adminUnlockUntil = Date.now() + ttlMs;
  }

  function consumeAdminUnlock() {
    if (Date.now() <= adminUnlockUntil) {
      adminUnlockUntil = 0; // one-shot: sofort verbrauchen
      return true;
    }
    return false;
  }

  function finalizeRoleSwitch(nextRole, { persist = true } = {}) {
    currentRole = nextRole;

    if (persist) {
      try { localStorage.setItem(LS_ROLE_KEY, nextRole); } catch (_) {}
    }

    state.applyDomAttributes();
    document.dispatchEvent(new CustomEvent("ui:role-changed", { detail: { role: nextRole } }));
  }

  // 5) DOM-Hook + State
  const state = {
    get role()       { return currentRole; },
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
      if (!roleFlagState[nextRole]) {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      if (nextRole === "godmode" && activeBuildRole !== "godmode") {
        throw new Error(`Unknown role: ${nextRole}`);
      }

      const goingToAdmin = nextRole === "admin" && currentRole !== "admin";
      if (goingToAdmin) {
        const buildIsFreeAdmin = (activeBuildRole === "admin" || activeBuildRole === "godmode");

        if (!buildIsFreeAdmin) {
          if (roleChangeInFlight) return; // kein Chaos bei Doppelaufruf
          roleChangeInFlight = true;

          // async Flow starten, aber setRole selbst bleibt synchron
          requestAdminPasswordViaModal()
            .then((pwd) => {
              if (!checkAdminPassword(pwd)) return; // Abbruch / falsch => nichts tun
              finalizeRoleSwitch("admin", { persist });
            })
            .finally(() => { roleChangeInFlight = false; });

          return; // wichtig: hier abbrechen, weil Auth noch läuft
        }
      }

      finalizeRoleSwitch(nextRole, { persist });
    },

    async requestAdmin({ persist = true, ttlMs = 30_000 } = {}) {
      const buildIsFreeAdmin =
        (activeBuildRole === "admin" || activeBuildRole === "godmode");

      // Wenn Build schon admin/godmode: kein Passwort nötig
      if (buildIsFreeAdmin) {
        state.setRole("admin", { persist });
        return true;
      }

      // Modal-Funktion muss global verfügbar sein (siehe Schritt 2)
      const ask = window.askAdminPassword;
      if (typeof ask !== "function") {
        // Notnagel: Verhalten wie früher
        const pwd = window.prompt("Admin-Passwort eingeben:");
        if (!checkAdminPassword(pwd)) return false;
        unlockAdminOnce(ttlMs);
        state.setRole("admin", { persist });
        return true;
      }

      const pwd = await ask();              // <- dein Modal (Promise)
      if (!checkAdminPassword(pwd)) return false;

      unlockAdminOnce(ttlMs);               // one-shot unlock setzen
      state.setRole("admin", { persist });  // synchroner Rollenwechsel
      return true;
    },

    setBuild(nextBuildRole) {
      if (BUILD_ROLE !== "godmode") {
        throw new Error("APP_STATE.setBuild ist nicht verfügbar.");
      }
      if (!roleFlagState[nextBuildRole]) {
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

    get flags() { return getFlagsBooleanMap(currentRole); },

    getFlag(key) {
      const def = roleFlagState[currentRole]?.[key];
      if (!def) throw new Error(`Unknown flag: ${key}`);
      return !!def.value;
    },

    getFlagLock(key) {
      const def = roleFlagState[currentRole]?.[key];
      if (!def) throw new Error(`Unknown flag: ${key}`);
      return !!def.lock;
    },

    setFlag(key, value) {
      const def = roleFlagState[currentRole]?.[key];
      if (!def) throw new Error(`Unknown flag: ${key}`);
      if (def.lock) throw new Error(`Flag '${key}' ist gesperrt (lock=true).`);

      def.value = !!value;
      persistFlagOverride(currentRole, key, def.value);

      document.dispatchEvent(new CustomEvent("ui:flags-changed", {
        detail: { role: currentRole, key, value: def.value }
      }));
    },

    toggleFlag(key) {
      state.setFlag(key, !state.getFlag(key));
    },

    get flagsMeta() {
      // für UI: { key: {value, lock} } im aktuellen Role-Kontext
      const src = roleFlagState[currentRole] || {};
      const out = {};
      for (const k of Object.keys(src)) out[k] = { value: !!src[k].value, lock: !!src[k].lock };
      return out;
    },
  };

  // 6) Globale, schreibgeschützte API aufbauen
  const api = {
    get role()        { return state.role; },
    get flags()       { return state.flags; },
    get version()     { return state.version; },
    get buildRole()   { return state.buildRole; },
    get activeBuild() { return state.activeBuild; },
    setRole: state.setRole,
    requestAdmin: state.requestAdmin,
    setFlag: state.setFlag,
    toggleFlag: state.toggleFlag,
    getFlag: state.getFlag,
    getFlagLock: state.getFlagLock,
    get flagsMeta() { return state.flagsMeta; },
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
