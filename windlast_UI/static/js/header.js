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