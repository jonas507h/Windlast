import { buildTor } from '../build/build_tor.js';
import { showFieldError } from '../utils/error.js';
import { showLoading, hideLoading } from "/static/js/utils/loading.js";

import { fetchOptions } from "../utils/catalog.js";
import { fillSelect } from "../utils/forms.js";
import { fetchJSON } from "../utils/api.js";
import { readHeaderValues } from "../utils/header.js";
import { isPositiveNumber } from "../utils/number.js";
import { fetchKompatibilitaet } from "../utils/reibwert.js";

let _isApplyingReibwertFilter = false;

async function applyReibwertDropdownFiltering({ rerunIfChanged = true } = {}) {
  // verhindert Re-Entrancy/Loops
  if (_isApplyingReibwertFilter) return;
  _isApplyingReibwertFilter = true;

  try {
    const bpEl = document.getElementById("bodenplatte_name_intern");
    const gmEl = document.getElementById("gummimatte");
    const ugEl = document.getElementById("untergrund_typ");
    if (!bpEl || !gmEl || !ugEl || !window.Catalog) return;

    const bpVal = bpEl.value;
    if (!bpVal) return;

    const gmRequested = gmEl.value || "nein";

    const data = await fetchKompatibilitaet({
      bodenplatte: bpVal,
      gummimatte: gmRequested
    });

    const gmAllowed = data?.gummimatte?.allowed || ["ja", "nein"];
    const gmEffective = data?.gummimatte?.effective || gmRequested;
    const ugAllowed = data?.untergruende?.allowed || [];

    // --- (1) Gummimatte Optionen filtern ---
    const gmOptionsAll = [
      { value: "ja", label: "Ja" },
      { value: "nein", label: "Nein" },
    ];
    const gmOptions = gmOptionsAll.filter(o => gmAllowed.includes(o.value));

    const prevGm = gmEl.value;
    fillSelect(gmEl, gmOptions, { defaultValue: gmEffective });

    // --- (2) Untergrund filtern ---
    const ugAll = window.Catalog.untergruende || [];
    const allowedSet = new Set(ugAllowed);

    // Wenn API leer liefert, lieber NICHT alles wegfiltern:
    const ugFiltered = (ugAllowed.length > 0)
      ? ugAll.filter(o => allowedSet.has(o.value))
      : ugAll;

    const prevUg = ugEl.value;
    const nextUg = ugFiltered.some(o => o.value === prevUg)
      ? prevUg
      : (ugFiltered[0]?.value ?? "");

    fillSelect(ugEl, ugFiltered, { defaultValue: nextUg });

    // Wenn sich gm durch "effective" geändert hat, kann sich die Untergrund-Menge ändern.
    // Einmal sauber nachziehen (max. 1x), damit state konsistent ist.
    if (rerunIfChanged && prevGm !== gmEl.value) {
      _isApplyingReibwertFilter = false;
      return applyReibwertDropdownFiltering({ rerunIfChanged: false });
    }
  } catch (e) {
    console.error("Reibwert-Filterung fehlgeschlagen:", e);
  } finally {
    _isApplyingReibwertFilter = false;
  }
}

async function initTorDropdowns() {
  // Initialisiert die Dropdowns für das Tor
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

    // Statisches Dropdown: Traversen-Orientierung (Default: Spitze nach oben)
    const trOri = document.getElementById("traversen_orientierung");
    if (trOri) {
      fillSelect(trOri, [
        { value: "up",   label: "Spitze nach oben"   },
        { value: "side", label: "Spitze seitlich"    },
        { value: "down", label: "Spitze nach unten"  },
      ], { defaultValue: "up" });
    }

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

    // --- Reibwert-Filterung initial + Listener ----------------------------
    await applyReibwertDropdownFiltering({ rerunIfChanged: true });

    const bpEl = document.getElementById("bodenplatte_name_intern");
    const gmEl = document.getElementById("gummimatte");

    const triggerFilter = () => applyReibwertDropdownFiltering({ rerunIfChanged: true });

    // Primär: change
    bpEl?.addEventListener("change", triggerFilter);
    gmEl?.addEventListener("change", triggerFilter);

    // Fallback: blur (weil ihr das schon öfter als zuverlässiger erlebt habt)
    bpEl?.addEventListener("blur", triggerFilter);
    gmEl?.addEventListener("blur", triggerFilter);
  } catch (e) {
    console.error("Tor-Dropdowns konnten nicht geladen werden:", e);
  }
}

function readTraversenOrientierung() {
  const el = document.getElementById("traversen_orientierung");
  const v = String(el?.value ?? "up").trim().toLowerCase();
  // Nur erlaubte Tokens durchlassen; ansonsten Default "up"
  return (v === "up" || v === "side" || v === "down") ? v : "up";
}

// --- Einzelfeld-Validierungen ---------------------------------------------

function validateWindzoneField() {
  const windzoneEl = document.getElementById('windzone');
  if (!windzoneEl) return true;

  const windzoneOK = !!windzoneEl.value;

  const fakeField = windzoneEl.closest('.field') || windzoneEl.parentElement;
  if (fakeField) fakeField.classList.toggle('is-invalid', !windzoneOK);
  windzoneEl.setAttribute('aria-invalid', windzoneOK ? 'false' : 'true');

  return windzoneOK;
}

function validateHoeheField() {
  const hoeheEl = document.getElementById('hoehe_m');
  const errH    = document.getElementById('err-hoehe');
  if (!hoeheEl) return true;

  const hoehe = parseFloat(hoeheEl.value);
  const hOK   = isPositiveNumber(hoehe);

  showFieldError(hoeheEl, errH, !hOK, 'Bitte eine gültige Höhe > 0 angeben.');
  return hOK;
}

function validateBreiteField() {
  const breiteEl = document.getElementById('breite_m');
  const errB     = document.getElementById('err-breite');
  if (!breiteEl) return true;

  const breite = parseFloat(breiteEl.value);
  const bOK    = isPositiveNumber(breite);

  showFieldError(breiteEl, errB, !bOK, 'Bitte eine gültige Breite > 0 angeben.');
  return bOK;
}

function validateHoeheFlaecheField() {
  const hoeheEl        = document.getElementById('hoehe_m');
  const hoeheFlaecheEl = document.getElementById('hoehe_flaeche_m');
  const errHF          = document.getElementById('err-hoehe_flaeche');

  if (!hoeheFlaecheEl) return true;

  const rawHF        = hoeheFlaecheEl.value?.trim();
  const hoeheFlaeche = rawHF === "" ? null : parseFloat(rawHF);

  let uOK  = true;
  let uMsg = '';

  if (!(rawHF === "" || (isFinite(hoeheFlaeche) && hoeheFlaeche > 0))) {
    uOK  = false;
    uMsg = 'Bitte eine Zahl > 0 angeben oder leer lassen.';
  } else if (hoeheFlaeche !== null && isFinite(hoeheFlaeche) && hoeheEl) {
    const hGes = parseFloat(hoeheEl.value);
    const maxU = isFinite(hGes) && (hoeheFlaeche <= hGes);
    if (!maxU) {
      uOK  = false;
      uMsg = 'Die Höhe der Fläche darf nicht größer als die Gesamthöhe sein.';
    }
  }

  showFieldError(hoeheFlaecheEl, errHF, !uOK, uMsg);
  return uOK;
}

function validateAnzahlSteherField() {
  const anzahlEl  = document.getElementById('anzahl_steher');
  const errA = document.getElementById('err-anzahl_steher');
  if (!anzahlEl) return true;

  const n = parseInt(anzahlEl.value, 10);
  const aOK = Number.isInteger(n) && n >= 2;

  showFieldError(anzahlEl, errA, !aOK, 'Bitte eine ganze Zahl ≥ 2 angeben.');
  return aOK;
}

// --- Formular-Gesamtvalidierung -------------------------------------------

function validateTorForm() {
  let ok = true;

  // Header: Windzone ist Pflicht
  ok = validateWindzoneField() && ok;

  // Tor-Eingaben
  ok = validateHoeheField() && ok;
  ok = validateBreiteField() && ok;
  ok = validateHoeheFlaecheField() && ok;
  ok = validateAnzahlSteherField() && ok;

  // Dropdowns sind durch initTorDropdowns vorbelegt → kein weiterer Check nötig

  return ok;
}

// async function submitTor() {
//   // Formulardaten sammeln und an API senden
//   try {
//     // Gummimatte-Wert holen (ja/nein); wir reichen ihn als Boolean weiter
//     if (!validateTorForm()) {
//       // Fokus auf erstes fehlerhaftes Feld
//       const firstInvalid = document.querySelector('.field.is-invalid select, .field.is-invalid input');
//       firstInvalid?.focus();
//       return;
//     }

//     const ok = await UI_WARN.confirmNichtZertifiziert();
//     if (!ok) return;

//     const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
//     const gummimatte_bool = (gmVal === "ja");

//     // Sammeln der Eingabewerte und verpacken
//     const payload = {
//       breite_m: parseFloat(document.getElementById("breite_m").value),
//       hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
//       traverse_name_intern: document.getElementById("traverse_name_intern").value,
//       bodenplatte_name_intern: document.getElementById("bodenplatte_name_intern").value,
//       untergrund_typ: document.getElementById("untergrund_typ").value, // z.B. "beton"
//       gummimatte: gummimatte_bool,
//       orientierung: readTraversenOrientierung(), // z.B. "up"
//       ...readHeaderValues(),
//     };

//     const data = await fetchJSON("/api/v1/tor/berechnen", {
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
//     console.error("Tor-Berechnung fehlgeschlagen:", e);
//     // optional: ein schlichtes Toast-Event, falls du es nutzen willst
//     document.dispatchEvent(new CustomEvent("toast", {
//       detail: { level: "error", text: String(e?.message || e) }
//     }));
//   }
// }

async function submitTor() {
  // Formulardaten sammeln, UI-Build ausführen und an generische API senden
  try {
    if (!validateTorForm()) {
      const firstInvalid = document.querySelector('.field.is-invalid select, .field.is-invalid input');
      firstInvalid?.focus();
      return;
    }

    const ok = await UI_WARN.confirmNichtZertifiziert();
    if (!ok) return;

    showLoading();

    const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
    const gummimatte_bool = (gmVal === "ja");
    const untergrund = document.getElementById("untergrund_typ").value;

    const breite_m = parseFloat(document.getElementById("breite_m").value);
    const hoehe_m  = parseFloat(document.getElementById("hoehe_m").value);
    const hoehe_flaeche_m = document.getElementById("hoehe_flaeche_m").value;
    const anzahl_steher = parseInt(document.getElementById("anzahl_steher").value, 10);
    const traverse_name_intern    = document.getElementById("traverse_name_intern").value;
    const bodenplatte_name_intern = document.getElementById("bodenplatte_name_intern").value;
    const orientierung            = readTraversenOrientierung();

    // 1) UI-Build → generische KONSTRUKTION
    const konstruktion = buildTor({
      breite_m,
      hoehe_m,
      hoehe_flaeche_m: hoehe_flaeche_m,
      anzahl_steher,
      traverse_name_intern,
      bodenplatte_name_intern,
      gummimatte: gummimatte_bool,
      untergrund,
      orientierung,
      name: 'Tor',
    }, window.Catalog);

    // 2) Headerwerte (windzone + aufstelldauer) dazu packen
    const header = readHeaderValues();   // { aufstelldauer, windzone }

    const payload = {
      konstruktion,
      ...header,
    };

    // 3) Generischen Endpoint aufrufen
    const data = await fetchJSON("/api/v1/konstruktion/berechnen", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // 4) Ergebnis wie gewohnt in den Footer schicken
    if (typeof window.updateFooterResults === "function") {
      window.updateFooterResults(data);
    } else {
      document.dispatchEvent(new CustomEvent("results:update", { detail: data }));
    }
  } catch (e) {
    console.error("Tor-Berechnung fehlgeschlagen:", e);
    document.dispatchEvent(new CustomEvent("toast", {
      detail: { level: "error", text: String(e?.message || e) }
    }));
  } finally {
    hideLoading();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitTor);

  // Feldweise Validierung beim Verlassen des Feldes via Event Delegation
  document.addEventListener(
    "blur",
    (ev) => {
      const el = ev.target;
      if (!el || !(el instanceof HTMLInputElement || el instanceof HTMLSelectElement)) {
        return;
      }

      switch (el.id) {
        case "hoehe_m":
          validateHoeheField();
          // abhängig: Fläche darf nicht größer als Höhe sein
          validateHoeheFlaecheField();
          break;

        case "breite_m":
          validateBreiteField();
          break;

        case "hoehe_flaeche_m":
          validateHoeheFlaecheField();
          break;

        case "anzahl_steher":
          validateAnzahlSteherField();
          break;

        case "windzone":
          validateWindzoneField();
          break;

        default:
          break;
      }
    },
    true // <<<< WICHTIG: capturing, weil blur nicht bubbelt
  );
});

// --- Globale Hooks für index.html ---
window.initTorDropdowns = initTorDropdowns;
window.submitTor = submitTor;