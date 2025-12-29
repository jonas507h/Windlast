// config_info.js

/* --------------------------------
 * 0) Kurz-Hilfe im Console-Log
 * -------------------------------- */
(function helpBanner() {
  const lines = [
    "Windlast UI — Quick Help:",
    `• Build-Rolle:              ${window.APP_STATE?.buildRole}`,
    "• Aktuelle Rolle:           APP_STATE.role",
    "• Rolle setzen:             APP_STATE.setRole('debug')   // 'user' | 'debug' | 'admin'",
    "• Aktuelle Flags:           APP_STATE.flags",
    "• Flag setzen:              APP_STATE.setFlag('show_nullpunkt', true)",
    "• Flag togglen:             APP_STATE.toggleFlag('show_nullpunkt')",
  ];
  if (typeof console !== "undefined") {
    console.log(lines.join("\n"));
  }
})();

/* --------------------------------
 * 1) UI-Helfer
 * -------------------------------- */
(function initUIHelpers() {
  const $all = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const hasFlag = (flag) => !!(APP_STATE && APP_STATE.flags && APP_STATE.flags[flag]);
  const hasRole = (roles) => {
    const role = APP_STATE && APP_STATE.role;
    return Array.isArray(roles) ? roles.includes(role) : role === roles;
  };

  function hide(el)  { el.hidden = true; }
  function show(el)  { el.hidden = false; }

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

  /** Auf Rollenwechsel & Flags-Änderungen reagieren (alles neu anwenden) */
  APP_STATE.onRoleChanged(() => {
    applyAttributeVisibility();
  });
  document.addEventListener("ui:flags-changed", () => {
    applyAttributeVisibility();
  });

  /** Beim ersten Load anwenden */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => applyAttributeVisibility());
  } else {
    applyAttributeVisibility();
  }

  window.UI = {
    showIfFlag, hideIfFlag,
    showIfRole, hideIfRole,
    guard, guardRole,
    applyAttributeVisibility,
  };
})();