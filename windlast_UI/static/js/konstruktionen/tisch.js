import { buildTisch } from '../build/build_tisch.js';
import { showFieldError } from '../utils/error.js';

async function fetchOptions(url) {
  // Holt Dropdown-Inhalte von der API
  const res = await fetch(url, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  const data = await res.json();
  return data.options || [];
}

function fillSelect(el, options, { placeholder = null, defaultValue = null } = {}) {
  // Füllt ein <select> mit Optionen
  el.innerHTML = "";
  if (placeholder) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    el.appendChild(opt);
  }
  for (const { value, label } of options) {
    if (value.startsWith("test_") && !window.APP_STATE?.flags?.show_test_options_dropdown) {
      continue;
    }
    const opt = document.createElement("option");
    opt.value = value;      // Request-Wert (name_intern bzw. "beton"/"stahl"/...)
    opt.textContent = label; // Anzeige (anzeige_name bzw. Enum.value)
    el.appendChild(opt);
  }
  if (defaultValue !== null && defaultValue !== undefined) {
    el.value = defaultValue;
  }
}

async function initTischDropdowns() {
  // Initialisiert die Dropdowns für den Tisch
  try {
    // Inhalte aus API laden
    const [traversen, bps, untergruende] = await Promise.all([
      fetchOptions("/api/v1/catalog/traversen"),
      fetchOptions("/api/v1/catalog/bodenplatten"),
      fetchOptions("/api/v1/catalog/untergruende"),
    ]);

    // Dropdowns füllen
    fillSelect(document.getElementById("traverse_name_intern"), traversen, { defaultValue: "prolyte_h30v" });
    fillSelect(document.getElementById("bodenplatte_name_intern"), bps, { defaultValue: "bp_stahl_100x100" });
    fillSelect(document.getElementById("untergrund_typ"), untergruende, { defaultValue: "BETON" });

    // Statisches Dropdown: Gummimatte (Ja/Nein), Default = Ja
    const gm = document.getElementById("gummimatte");
    if (gm) {
      fillSelect(gm, [
        { value: "ja",   label: "Ja" },
        { value: "nein", label: "Nein" },
      ], { defaultValue: "ja" });
    }

    window.Catalog = {
      traversen,
      bps,
      untergruende,
      getTraverse(nameIntern) {
        return traversen.find(t => t.value === nameIntern);
      },
      getBodenplatte(nameIntern) {
        return bps.find(b => b.value === nameIntern);
      }
    };
  } catch (e) {
    console.error("Tor-Dropdowns konnten nicht geladen werden:", e);
  }
}

async function fetchJSON(url, opts) {
  // Sendet Anfrage an API und wertet die Antwort aus
  // hier: sendet Eingaben an API und empfängt Rechenergebnisse
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }
  return res.json();
}

function getHeaderDoc() {
  return document;
}

function readHeaderValues() {
  // Liest Werte aus header.html
  const hdoc = getHeaderDoc();
  if (!hdoc) throw new Error("Header-Dokument nicht gefunden");
  const wert = parseInt(hdoc.getElementById("aufstelldauer_wert")?.value ?? "0", 10);
  const einheit = hdoc.getElementById("aufstelldauer_einheit")?.value;
  const windzone = hdoc.getElementById("windzone")?.value;

  return {
    aufstelldauer: isFinite(wert) && wert > 0 && einheit ? { wert, einheit } : null,
    windzone,
  };
}

function isPositiveNumber(v) {
  return typeof v === 'number' && isFinite(v) && v > 0;
}

function validateTischForm() {
  let ok = true;

  // Header: Windzone ist Pflicht (Aufstelldauer explizit NICHT)
  const windzoneEl = document.getElementById('windzone'); // kommt aus dem Header
  const windzoneOK = !!(windzoneEl && windzoneEl.value);
  if (windzoneEl) {
    const wrap = windzoneEl.closest('.field') || windzoneEl.parentElement;
    if (wrap) wrap.classList.toggle('is-invalid', !windzoneOK);
    windzoneEl.setAttribute('aria-invalid', windzoneOK ? 'false' : 'true');
  }
  ok = ok && windzoneOK;

  // Zahlenfelder > 0
  const hoeheEl  = document.getElementById('hoehe_m');
  const breiteEl = document.getElementById('breite_m');
  const tiefeEl  = document.getElementById('tiefe_m');

  const errH = document.getElementById('err-hoehe');
  const errB = document.getElementById('err-breite');
  const errT = document.getElementById('err-tiefe');

  const hOK = isPositiveNumber(parseFloat(hoeheEl?.value));
  showFieldError(hoeheEl, errH, !hOK, 'Bitte eine gültige Höhe > 0 angeben.');
  ok = ok && hOK;

  const bOK = isPositiveNumber(parseFloat(breiteEl?.value));
  showFieldError(breiteEl, errB, !bOK, 'Bitte eine gültige Breite > 0 angeben.');
  ok = ok && bOK;

  const tOK = isPositiveNumber(parseFloat(tiefeEl?.value));
  showFieldError(tiefeEl, errT, !tOK, 'Bitte eine gültige Tiefe > 0 angeben.');
  ok = ok && tOK;

  // Pflicht-Dropdowns (z. T. mit Defaults aus initTischDropdowns)
  const reqSelectIds = [
    'traverse_name_intern',
    'bodenplatte_name_intern',
    'untergrund_typ',
    'gummimatte'
  ];
  for (const id of reqSelectIds) {
    const el = document.getElementById(id);
    if (!el) continue;
    const hasValue = !!el.value;
    const wrap = el.closest('.field');
    if (wrap) wrap.classList.toggle('is-invalid', !hasValue);
    el.setAttribute('aria-invalid', hasValue ? 'false' : 'true');
    ok = ok && hasValue;
  }

  return ok;
}

// async function submitTisch() {
//   // Formulardaten sammeln und an API senden
//   try {
//     if (!validateTischForm()) {
//       const firstInvalid = document.querySelector('.field.is-invalid select, .field.is-invalid input');
//       firstInvalid?.focus();
//       return;
//     }

//     const ok = await UI_WARN.confirmNichtZertifiziert();
//     if (!ok) return;

//     // Gummimatte-Wert holen (ja/nein); wir reichen ihn als Boolean weiter
//     const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
//     const gummimatte_bool = (gmVal === "ja");

//     // Sammeln der Eingabewerte und verpacken
//     const payload = {
//       breite_m: parseFloat(document.getElementById("breite_m").value),
//       tiefe_m:  parseFloat(document.getElementById("tiefe_m").value),
//       hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
//       traverse_name_intern: document.getElementById("traverse_name_intern").value,
//       bodenplatte_name_intern: document.getElementById("bodenplatte_name_intern").value,
//       untergrund_typ: document.getElementById("untergrund_typ").value, // z.B. "beton"
//       gummimatte: gummimatte_bool,
//       ...readHeaderValues(),
//     };

//     const data = await fetchJSON("/api/v1/tisch/berechnen", {
//       method: "POST",
//       body: JSON.stringify(payload),
//     });

//     // 1) bevorzugt: direkte Funktion (falls Footer sie anbietet)
//     if (typeof window.updateFooterResults === "function") {
//       window.updateFooterResults(data);
//     } else {
//       // 2) Fallback: CustomEvent im selben Dokument
//       document.dispatchEvent(new CustomEvent("results:update", { detail: data }));
//     }
//   } catch (e) {
//     console.error("Tisch-Berechnung fehlgeschlagen:", e);
//     // optional: ein schlichtes Toast-Event, falls du es nutzen willst
//     document.dispatchEvent(new CustomEvent("toast", {
//       detail: { level: "error", text: String(e?.message || e) }
//     }));
//   }
// }

async function submitTisch() {
  try {
    // 1) Validierung wie bisher
    if (!validateTischForm()) {
      const firstInvalid = document.querySelector('.field.is-invalid select, .field.is-invalid input');
      firstInvalid?.focus();
      return;
    }

    const ok = await UI_WARN.confirmNichtZertifiziert();
    if (!ok) return;

    // 2) Gummimatte (ja/nein) -> Boolean
    const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
    const gummimatte_bool = (gmVal === "ja");
    const untergrund = document.getElementById("untergrund_typ")?.value ?? "Beton";

    // 3) UI-Inputs einsammeln
    const inputs = {
      breite_m: parseFloat(document.getElementById("breite_m").value),
      tiefe_m:  parseFloat(document.getElementById("tiefe_m").value),
      hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
      traverse_name_intern:    document.getElementById("traverse_name_intern").value,
      bodenplatte_name_intern: document.getElementById("bodenplatte_name_intern").value,
      gummimatte: gummimatte_bool,
      untergrund: untergrund,
      name: "Tisch",
    };

    // 4) Generische KONSTRUKTION über UI-Build erzeugen
    const konstruktion = buildTisch(inputs, window.Catalog);

    // 5) Headerwerte (windzone + aufstelldauer) dazu
    const header = readHeaderValues(); // { aufstelldauer, windzone }

    const payload = {
      konstruktion,
      ...header,
    };

    // 6) Generischen Endpoint aufrufen
    const data = await fetchJSON("/api/v1/konstruktion/berechnen", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // 7) Ergebnis wie gehabt in den Footer
    if (typeof window.updateFooterResults === "function") {
      window.updateFooterResults(data);
    } else {
      document.dispatchEvent(new CustomEvent("results:update", { detail: data }));
    }
  } catch (e) {
    console.error("Tisch-Berechnung fehlgeschlagen:", e);
    document.dispatchEvent(new CustomEvent("toast", {
      detail: { level: "error", text: String(e?.message || e) }
    }));
  }
}

// Funktion für Berechnen-Button, wenn das Dokument geladen ist
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitTisch);
});

// --- Globale Hooks für index.html ---
window.initTischDropdowns = initTischDropdowns;
window.submitTisch = submitTisch;