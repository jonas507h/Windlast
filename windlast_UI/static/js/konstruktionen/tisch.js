import { buildTisch } from '../build/build_tisch.js';
import { showFieldError } from '../utils/error.js';
import { showLoading, hideLoading } from "/static/js/utils/loading.js";

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

// --- Einzelfeld-Validierungen ---------------------------------------------

function validateWindzoneField() {
  const windzoneEl = document.getElementById('windzone'); // kommt aus dem Header
  if (!windzoneEl) return true;

  const windzoneOK = !!windzoneEl.value;
  const wrap = windzoneEl.closest('.field') || windzoneEl.parentElement;
  if (wrap) wrap.classList.toggle('is-invalid', !windzoneOK);
  windzoneEl.setAttribute('aria-invalid', windzoneOK ? 'false' : 'true');

  return windzoneOK;
}

function validateHoeheField() {
  const hoeheEl = document.getElementById('hoehe_m');
  const errH = document.getElementById('err-hoehe');
  if (!hoeheEl) return true;

  const hOK = isPositiveNumber(parseFloat(hoeheEl.value));
  showFieldError(hoeheEl, errH, !hOK, 'Bitte eine gültige Höhe > 0 angeben.');
  return hOK;
}

function validateBreiteField() {
  const breiteEl = document.getElementById('breite_m');
  const errB = document.getElementById('err-breite');
  if (!breiteEl) return true;

  const bOK = isPositiveNumber(parseFloat(breiteEl.value));
  showFieldError(breiteEl, errB, !bOK, 'Bitte eine gültige Breite > 0 angeben.');
  return bOK;
}

function validateTiefeField() {
  const tiefeEl = document.getElementById('tiefe_m');
  const errT = document.getElementById('err-tiefe');
  if (!tiefeEl) return true;

  const tOK = isPositiveNumber(parseFloat(tiefeEl.value));
  showFieldError(tiefeEl, errT, !tOK, 'Bitte eine gültige Tiefe > 0 angeben.');
  return tOK;
}

function validateHoeheFlaecheField() {
  const hoeheEl = document.getElementById('hoehe_m');
  const hoeheFlaecheEl = document.getElementById('hoehe_flaeche_m');
  const errHF = document.getElementById('err-hoehe_flaeche');
  if (!hoeheFlaecheEl) return true;

  const rawHF = hoeheFlaecheEl.value?.trim();
  const hoeheFlaeche = rawHF === "" ? null : parseFloat(rawHF);

  let uOK = true;
  let uMsg = '';

  if (!(rawHF === "" || (isFinite(hoeheFlaeche) && hoeheFlaeche > 0))) {
    uOK = false;
    uMsg = 'Bitte eine Zahl > 0 angeben oder leer lassen.';
  } else if (hoeheFlaeche !== null && isFinite(hoeheFlaeche)) {
    const hGes = parseFloat(hoeheEl?.value);
    if (isFinite(hGes) && hoeheFlaeche > hGes) {
      uOK = false;
      uMsg = 'Die Höhe der Fläche darf nicht größer als die Gesamthöhe sein.';
    }
  }

  showFieldError(hoeheFlaecheEl, errHF, !uOK, uMsg);
  return uOK;
}

function validateAnzahlSteherBreiteField() {
  const anzahlEl  = document.getElementById('anzahl_steher_breite');
  const errA = document.getElementById('err-anzahl_steher_breite');
  if (!anzahlEl) return true;

  const n = parseInt(anzahlEl.value, 10);
  const aOK = Number.isInteger(n) && n >= 2;

  showFieldError(anzahlEl, errA, !aOK, 'Bitte eine ganze Zahl ≥ 2 angeben.');
  return aOK;
}

function validateAnzahlSteherTiefeField() {
  const anzahlEl  = document.getElementById('anzahl_steher_tiefe');
  const errA = document.getElementById('err-anzahl_steher_tiefe');
  if (!anzahlEl) return true;

  const n = parseInt(anzahlEl.value, 10);
  const aOK = Number.isInteger(n) && n >= 2;

  showFieldError(anzahlEl, errA, !aOK, 'Bitte eine ganze Zahl ≥ 2 angeben.');
  return aOK;
}

// --- Formular-Gesamtvalidierung -------------------------------------------

function validateTischForm() {
  let ok = true;

  ok = validateWindzoneField()      && ok;
  ok = validateHoeheField()         && ok;
  ok = validateBreiteField()        && ok;
  ok = validateTiefeField()         && ok;
  ok = validateHoeheFlaecheField()  && ok;
  ok = validateAnzahlSteherBreiteField() && ok;
  ok = validateAnzahlSteherTiefeField()  && ok;

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

    showLoading();

    // 2) Gummimatte (ja/nein) -> Boolean
    const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
    const gummimatte_bool = (gmVal === "ja");
    const untergrund = document.getElementById("untergrund_typ")?.value ?? "Beton";

    // 3) UI-Inputs einsammeln
    const inputs = {
      breite_m: parseFloat(document.getElementById("breite_m").value),
      tiefe_m:  parseFloat(document.getElementById("tiefe_m").value),
      hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
      hoehe_flaeche_m: document.getElementById("hoehe_flaeche_m").value,
      anzahl_steher_breite: parseInt(document.getElementById("anzahl_steher_breite").value, 10),
      anzahl_steher_tiefe:  parseInt(document.getElementById("anzahl_steher_tiefe").value, 10),
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
  } finally {
    hideLoading();
  }
}

// Funktion für Berechnen-Button, wenn das Dokument geladen ist
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitTisch);

  // Delegierter blur-Handler (capturing!), damit es auch bei dynamischem DOM klappt
  document.addEventListener("blur", (ev) => {
    const el = ev.target;
    if (!el || !(el instanceof HTMLInputElement || el instanceof HTMLSelectElement)) return;

    switch (el.id) {
      case "windzone":
        validateWindzoneField();
        break;

      case "hoehe_m":
        validateHoeheField();
        // abhängig: Fläche darf nicht größer als Gesamthöhe sein
        validateHoeheFlaecheField();
        break;

      case "breite_m":
        validateBreiteField();
        break;

      case "tiefe_m":
        validateTiefeField();
        break;

      case "hoehe_flaeche_m":
        validateHoeheFlaecheField();
        break;

      case "anzahl_steher_breite":
        validateAnzahlSteherBreiteField();
        break;
      
      case "anzahl_steher_tiefe":
        validateAnzahlSteherTiefeField();
        break;

      default:
        break;
    }
  }, true); // << wichtig: blur bubbelt nicht
});

// --- Globale Hooks für index.html ---
window.initTischDropdowns = initTischDropdowns;
window.submitTisch = submitTisch;