async function fetchOptions(url) {
  const res = await fetch(url, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error(`GET ${url} -> ${res.status}`);
  const data = await res.json();
  return data.options || [];
}

function fillSelect(el, options, { placeholder = null, defaultValue = null } = {}) {
  el.innerHTML = "";
  if (placeholder) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    el.appendChild(opt);
  }
  for (const { value, label } of options) {
    const opt = document.createElement("option");
    opt.value = value;   // Enum-Name (z.B. "TAG" / "III_Binnenland")
    opt.textContent = label; // Anzeige (z.B. "Tag" / "3 Binnenland")
    el.appendChild(opt);
  }
  if (defaultValue) el.value = defaultValue;
}

async function initHeaderDropdowns() {
  try {
    const [dauerOpts, windOpts] = await Promise.all([
      fetchOptions("/api/v1/config/dauer-einheiten"),
      fetchOptions("/api/v1/config/windzonen"),
    ]);

    const dauerSel = document.getElementById("aufstelldauer_einheit");
    const windSel  = document.getElementById("windzone");

    // Optional Defaults (kannst du anpassen)
    fillSelect(dauerSel, dauerOpts, { placeholder: null, defaultValue: "MONAT" });
    fillSelect(windSel,  windOpts,  { placeholder: null });

  } catch (err) {
    console.error("Header-Dropdowns konnten nicht geladen werden:", err);
  }
}

document.addEventListener("DOMContentLoaded", initHeaderDropdowns);

document.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("program-version");
  const v  = window.APP_STATE?.version;
  if (el && v) {
    el.textContent = `Version ${v}`;
    el.hidden = false;
  }
});

// Helfer zum Aktualisieren des Rollen-/Build-Labels
function updateRoleLabel() {
  const el  = document.getElementById("role-label");
  const app = window.APP_STATE;
  if (!el || !app) return;

  const role       = app.role;
  const buildRole  = app.buildRole;              // echter Build (z.B. "user", "debug", "admin", "godmode")
  const activeBuild = app.activeBuild || buildRole; // simulierter Build (falls vorhanden)

  if (buildRole === "godmode") {
    // Im echten godmode-Build immer anzeigen, inkl. simuliertem Build
    el.textContent = `Rolle: ${role} (Build: ${activeBuild})`;
    el.hidden = false;
  } else {
    // In normalen Builds wie bisher: nur anzeigen, wenn Rolle != "user"
    if (role && role !== "user") {
      el.textContent = `Rolle: ${role}`;
      el.hidden = false;
    } else {
      el.hidden = true;
    }
  }
}

// Initial bei DOM-Ready
document.addEventListener("DOMContentLoaded", () => {
  updateRoleLabel();
});

// Auf Rollenwechsel reagieren
document.addEventListener("ui:role-changed", () => {
  updateRoleLabel();
});

// Auf Build-Wechsel (setBuild) reagieren – nur im godmode-Build vorhanden
document.addEventListener("ui:build-changed", () => {
  updateRoleLabel();
});