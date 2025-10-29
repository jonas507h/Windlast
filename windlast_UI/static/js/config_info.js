/* ================================
 * info.js — HowTo & kleine Helfer
 * Voraussetzungen:
 *   - config.js liefert window.APP_STATE mit:
 *       - APP_STATE.role   -> "user" | "debug" | "admin"
 *       - APP_STATE.flags  -> { show_debug_tooltip, ... }
 *       - APP_STATE.setRole(nextRole, { persist=true })
 *       - APP_STATE.onRoleChanged(handler)
 *
 * Einbinden (nach config.js):
 *   <script src="/static/config.js"></script>
 *   <script src="/static/info.js"></script>
 * ================================ */

/* --------------------------------
 * 0) Kurz-Hilfe im Console-Log
 * -------------------------------- */
(function helpBanner() {
  const lines = [
    "Windlast UI — Quick Help:",
    "• Aktuelle Rolle:           APP_STATE.role",
    "• Aktuelle Flags:           APP_STATE.flags",
    "• Rolle setzen:             APP_STATE.setRole('debug')   // 'user' | 'debug' | 'admin'",
    "• Persistente Rolle setzen: APP_STATE.setRole('admin', { persist: true })",
    "• Persistenz löschen:       localStorage.removeItem('windlast_ui_role')",
    "• Seite neu laden:          location.reload()",
    "• Passwort-Umschalter:      UI.promptRoleWithPassword()  // Demo",
    "• Elemente via Attribute:   data-requires-flag, data-requires-role",
    "• Elemente via JS:          UI.showIfFlag('#sel','show_debug_tooltip');",
    "                            UI.showIfRole('#sel',['admin','debug']);",
  ];
  if (typeof console !== "undefined") {
    console.log(lines.join("\n"));
  }
})();

/* --------------------------------
 * 1) Kleine UI-Helfer
 * -------------------------------- */
(function initUIHelpers() {
  const $all = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const hasFlag = (flag) => !!(APP_STATE && APP_STATE.flags && APP_STATE.flags[flag]);
  const hasRole = (roles) => {
    const role = APP_STATE && APP_STATE.role;
    return Array.isArray(roles) ? roles.includes(role) : role === roles;
  };

  function show(el)  { el.style.removeProperty("display"); }
  function hide(el)  { el.style.setProperty("display", "none"); }

  /** UI.showIfFlag(selector, flagKey) / hideIfFlag(...) */
  function showIfFlag(selector, flagKey) {
    const on = hasFlag(flagKey);
    $all(selector).forEach(el => on ? show(el) : hide(el));
  }
  function hideIfFlag(selector, flagKey) {
    const on = hasFlag(flagKey);
    $all(selector).forEach(el => on ? hide(el) : show(el));
  }

  /** UI.showIfRole(selector, rolesArray) / hideIfRole(...) */
  function showIfRole(selector, roles) {
    const on = hasRole(roles);
    $all(selector).forEach(el => on ? show(el) : hide(el));
  }
  function hideIfRole(selector, roles) {
    const on = hasRole(roles);
    $all(selector).forEach(el => on ? hide(el) : show(el));
  }

  /** UI.guard(flagKey, fn) — Code nur ausführen, wenn Flag aktiv */
  function guard(flagKey, fn) {
    if (hasFlag(flagKey)) fn();
  }

  /** UI.guardRole(roles, fn) — Code nur in bestimmten Rollen ausführen */
  function guardRole(roles, fn) {
    if (hasRole(roles)) fn();
  }

  /** Auto-Binding: Attribute-basierte Sichtbarkeit
   *  <div data-requires-flag="show_debug_tooltip">…</div>
   *  <div data-requires-role="admin,debug">…</div>
   */
  function applyAttributeVisibility(root = document) {
    $all("[data-requires-flag]", root).forEach(el => {
      const key = (el.getAttribute("data-requires-flag") || "").trim();
      if (!key) return;
      hasFlag(key) ? show(el) : hide(el);
    });

    $all("[data-requires-role]", root).forEach(el => {
      const roles = (el.getAttribute("data-requires-role") || "")
        .split(",").map(s => s.trim()).filter(Boolean);
      if (roles.length === 0) return;
      hasRole(roles) ? show(el) : hide(el);
    });
  }

  /** Auf Rollenwechsel reagieren (alles neu anwenden) */
  APP_STATE.onRoleChanged(() => {
    applyAttributeVisibility();
  });

  /** Beim ersten Load anwenden */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => applyAttributeVisibility());
  } else {
    applyAttributeVisibility();
  }

  /** Öffentlich machen */
  window.UI = {
    showIfFlag, hideIfFlag,
    showIfRole, hideIfRole,
    guard, guardRole,
    applyAttributeVisibility, // falls du nachträglich DOM einfügst
    /* --------------------------------
     * 2) Beispiele zur Nutzung im Code
     * --------------------------------
     * // a) Ereignisse nur registrieren, wenn Flag aktiv:
     * UI.guard('show_debug_tooltip', () => registerDebugTooltips());
     *
     * // b) Admin-only Logik:
     * UI.guardRole(['admin'], () => enableDangerZone());
     *
     * // c) Selektive Anzeige:
     * UI.showIfFlag('.debug-panel', 'show_debug_tooltip');
     * UI.showIfRole('#adminButton', ['admin']);
     */

    /* --------------------------------
     * 3) Einfacher Passwort-Umschalter (Demo)
     *    — NICHT sicher, nur Komfort!
     * -------------------------------- */
    promptRoleWithPassword() {
      const role = prompt("Rolle setzen (user/debug/admin):");
      if (!role) return;

      if (role === "admin") {
        // ⚠️ Demo: statisches Passwort. Für echte Sicherheit: serverseitig prüfen!
        const pwd = prompt("Admin-Passwort:");
        const OK = checkPasswordDemo(pwd);
        if (!OK) return alert("Falsches Passwort.");
      }

      try {
        APP_STATE.setRole(role, { persist: true });
        alert(`Rolle ist jetzt '${APP_STATE.role}'.`);
      } catch (e) {
        alert(e.message);
      }
    },
  };

  /** Demo-Passwortprüfung:
   *  - aktuell nur ein fester String
   *  - du kannst das leicht ersetzen durch:
   *      - Hashvergleich,
   *      - oder einen Flask-Endpoint, der ein Token ausstellt.
   */
  function checkPasswordDemo(input) {
    const DEMO_PASSWORD = "MEIN_GEHEIMES_PASSWORT"; // TODO: ersetzen
    return input === DEMO_PASSWORD;
  }
})();


/* HTML Beispiele:

<!-- Wird automatisch von info.js sichtbar/unsichtbar geschaltet -->
<div class="debug-panel" data-requires-flag="show_debug_tooltip">
  Debug Infos …
</div>

<button data-requires-role="admin,debug" onclick="doSomething()">Interner Button</button>
<button data-requires-role="admin" onclick="UI.promptRoleWithPassword()">Rolle wechseln (Demo)</button>

*/