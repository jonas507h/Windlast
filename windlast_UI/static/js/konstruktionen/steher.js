import { buildSteher } from '../build/build_steher.js';
import { showFieldError } from '../utils/error.js';
import { showLoading, hideLoading } from "/static/js/utils/loading.js";
import { fetchOptions } from "../utils/catalog.js";
import { fillSelect } from "../utils/forms.js";
import { fetchJSON } from "../utils/api.js";
import { readHeaderValues } from "../utils/header.js";
import { isPositiveNumber } from "../utils/number.js";
import { fetchKompatibilitaet } from "../utils/reibwert.js";

let _isApplyingReibwertFilterSteher = false;

async function applyReibwertDropdownFilteringSteher({ rerunIfChanged = true } = {}) {
  if (_isApplyingReibwertFilterSteher) return;
  _isApplyingReibwertFilterSteher = true;

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

    // (1) Gummimatte filtern
    const gmOptionsAll = [
      { value: "ja", label: "Ja" },
      { value: "nein", label: "Nein" },
    ];
    const gmOptions = gmOptionsAll.filter(o => gmAllowed.includes(o.value));

    const prevGm = gmEl.value;
    fillSelect(gmEl, gmOptions, { defaultValue: gmEffective });

    // (2) Untergrund filtern
    const ugAll = window.Catalog.untergruende || [];
    const allowedSet = new Set(ugAllowed);

    const ugFiltered = (ugAllowed.length > 0)
      ? ugAll.filter(o => allowedSet.has(o.value))
      : ugAll;

    const prevUg = ugEl.value;
    const nextUg = ugFiltered.some(o => o.value === prevUg)
      ? prevUg
      : (ugFiltered[0]?.value ?? "");

    fillSelect(ugEl, ugFiltered, { defaultValue: nextUg });

    // Wenn GM durch effective umspringt: einmal nachziehen
    if (rerunIfChanged && prevGm !== gmEl.value) {
      _isApplyingReibwertFilterSteher = false;
      return applyReibwertDropdownFilteringSteher({ rerunIfChanged: false });
    }
  } catch (e) {
    console.error("Reibwert-Filterung (Steher) fehlgeschlagen:", e);
  } finally {
    _isApplyingReibwertFilterSteher = false;
  }
}

async function initSteherDropdowns() {
  // Initialisiert die Dropdowns für das Steher
  try {
    // Inhalte aus API laden
    const [traversen, rohre, bps, untergruende] = await Promise.all([
      fetchOptions("/api/v1/catalog/traversen"),
      fetchOptions("/api/v1/catalog/rohre"),
      fetchOptions("/api/v1/catalog/bodenplatten"),
      fetchOptions("/api/v1/catalog/untergruende"),
    ]);

    // Dropdowns füllen
    fillSelect(document.getElementById("traverse_name_intern"), traversen, { defaultValue: "prolyte_h30v" });
    fillSelect(document.getElementById("rohr_name_intern"), rohre, { defaultValue: "alu_48x3" });
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
      rohre,
      bps,
      untergruende,
      getTraverse(nameIntern) {
        return traversen.find(t => t.value === nameIntern);
      },
      getRohr(nameIntern) {
        return rohre.find(r => r.value === nameIntern);
      },
      getBodenplatte(nameIntern) {
        return bps.find(b => b.value === nameIntern);
      }
    };

    // --- Reibwert-Filterung -------------------------------
    await applyReibwertDropdownFilteringSteher({ rerunIfChanged: true });

    const bpEl = document.getElementById("bodenplatte_name_intern");
    const gmEl = document.getElementById("gummimatte");

    const triggerFilter = () => applyReibwertDropdownFilteringSteher({ rerunIfChanged: true });

    bpEl?.addEventListener("change", triggerFilter);
    gmEl?.addEventListener("change", triggerFilter);

    // extra robust (wie ihr es kennt), aber direkt am Element – nicht delegiert
    bpEl?.addEventListener("blur", triggerFilter);
    gmEl?.addEventListener("blur", triggerFilter);
  } catch (e) {
    console.error("Steher-Dropdowns konnten nicht geladen werden:", e);
  }
}

// --- Einzelfeld-Validierungen ---------------------------------------------

function validateWindzoneField() {
  const windzoneEl = document.getElementById('windzone'); // kommt aus dem Header
  if (!windzoneEl) return true;

  const windzoneOK = !!windzoneEl.value;
  const fakeField = windzoneEl.closest('.field') || windzoneEl.parentElement;
  if (fakeField) fakeField.classList.toggle('is-invalid', !windzoneOK);
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

function validateRohrLaengeField() {
  const rLaengeEl = document.getElementById('rohr_laenge_m');
  const errL = document.getElementById('err-laenge');
  if (!rLaengeEl) return true;

  const lOK = isPositiveNumber(parseFloat(rLaengeEl.value));
  showFieldError(rLaengeEl, errL, !lOK, 'Bitte eine gültige Länge > 0 angeben.');
  return lOK;
}

function validateRohrHoeheField() {
  const hoeheEl = document.getElementById('hoehe_m');
  const rHoeheEl = document.getElementById('rohr_hoehe_m');
  const errRH = document.getElementById('err-rhoehe');
  if (!rHoeheEl) return true;

  let rhOK = true;
  let rhMsg = '';

  const rh = parseFloat(rHoeheEl.value);
  if (!isPositiveNumber(rh)) {
    rhOK = false;
    rhMsg = 'Bitte eine gültige Rohrhöhe > 0 angeben.';
  } else {
    const hGes = parseFloat(hoeheEl?.value);
    if (isFinite(hGes) && rh > hGes) {
      rhOK = false;
      rhMsg = 'Die Rohrhöhe darf die Gesamthöhe nicht überschreiten.';
    }
  }

  showFieldError(rHoeheEl, errRH, !rhOK, rhMsg);
  return rhOK;
}

function validateHoeheFlaecheField() {
  const rHoeheEl = document.getElementById('rohr_hoehe_m');
  const hoeheFlaecheEl = document.getElementById('hoehe_flaeche_m');
  const errHF = document.getElementById('err-hoehe_flaeche');
  if (!hoeheFlaecheEl) return true;

  const rawHF = hoeheFlaecheEl.value?.trim();
  const hf = rawHF === "" ? null : parseFloat(rawHF);

  let uOK = true;
  let uMsg = '';

  if (!(rawHF === "" || (isFinite(hf) && hf > 0))) {
    uOK = false;
    uMsg = 'Bitte eine Zahl > 0 angeben oder leer lassen.';
  } else if (hf !== null && isFinite(hf)) {
    const rh = parseFloat(rHoeheEl?.value);
    if (isFinite(rh) && hf > rh) {
      uOK = false;
      uMsg = 'Die Höhe der Fläche darf nicht größer als die Rohrhöhe sein.';
    }
  }

  showFieldError(hoeheFlaecheEl, errHF, !uOK, uMsg);
  return uOK;
}

// --- Formular-Gesamtvalidierung -------------------------------------------

function validateSteherForm() {
  let ok = true;

  ok = validateWindzoneField()      && ok;
  ok = validateHoeheField()         && ok;
  ok = validateRohrLaengeField()    && ok;
  ok = validateRohrHoeheField()     && ok;
  ok = validateHoeheFlaecheField()  && ok;

  return ok;
}

// async function submitSteher() {
//   // Formulardaten sammeln und an API senden
//   try {
//     if (!validateSteherForm()) {
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
//       hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
//       rohr_laenge_m: parseFloat(document.getElementById("rohr_laenge_m").value),
//       rohr_hoehe_m: parseFloat(document.getElementById("rohr_hoehe_m").value),
//       traverse_name_intern: document.getElementById("traverse_name_intern").value,
//       rohr_name_intern: document.getElementById("rohr_name_intern").value,
//       bodenplatte_name_intern: document.getElementById("bodenplatte_name_intern").value,
//       untergrund_typ: document.getElementById("untergrund_typ").value, // z.B. "beton"
//       gummimatte: gummimatte_bool,
//       ...readHeaderValues(),
//     };

//     const data = await fetchJSON("/api/v1/steher/berechnen", {
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
//     console.error("Steher-Berechnung fehlgeschlagen:", e);
//     // optional: ein schlichtes Toast-Event, falls du es nutzen willst
//     document.dispatchEvent(new CustomEvent("toast", {
//       detail: { level: "error", text: String(e?.message || e) }
//     }));
//   }
// }

async function submitSteher() {
  try {
    if (!validateSteherForm()) {
      const firstInvalid = document.querySelector('.field.is-invalid select, .field.is-invalid input');
      firstInvalid?.focus();
      return;
    }

    const okConfirm = await window.UI_WARN?.confirmNichtZertifiziert?.();
    if (okConfirm === false) return;
    showLoading();

    const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
    const gummimatte_bool = (gmVal === "ja");

    const inputs = {
      hoehe_m:        parseFloat(document.getElementById("hoehe_m").value),
      rohr_laenge_m:  parseFloat(document.getElementById("rohr_laenge_m").value),
      rohr_hoehe_m:   parseFloat(document.getElementById("rohr_hoehe_m").value),
      hoehe_flaeche_m: document.getElementById("hoehe_flaeche_m").value,
      traverse_name_intern:   document.getElementById("traverse_name_intern").value,
      bodenplatte_name_intern:document.getElementById("bodenplatte_name_intern").value,
      rohr_name_intern:       document.getElementById("rohr_name_intern").value,
      gummimatte: gummimatte_bool,
      untergrund: document.getElementById("untergrund_typ").value,
      name: "Steher",
      // untergrund_typ evtl kippen
    };

    // 1) UI-Build erzeugen (komplett generische Struktur)
    const konstruktion = buildSteher(inputs, window.Catalog);

    // 2) Header dazu und an GENERIC-Endpoint schicken
    const payload = {
      konstruktion,
      ...readHeaderValues(),
    };

    const data = await fetchJSON("/api/v1/konstruktion/berechnen", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (typeof window.updateFooterResults === "function") {
      window.updateFooterResults(data);
    } else {
      document.dispatchEvent(new CustomEvent("results:update", { detail: data }));
    }
  } catch (e) {
    console.error("Steher-Berechnung fehlgeschlagen:", e);
    document.dispatchEvent(new CustomEvent("toast", {
      detail: { level: "error", text: String(e?.message || e) }
    }));
  } finally {
    hideLoading();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitSteher);

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
        // abhängig: Rohrhöhe darf Gesamthöhe nicht überschreiten
        validateRohrHoeheField();
        // und Fläche hängt indirekt an Rohrhöhe
        validateHoeheFlaecheField();
        break;

      case "rohr_laenge_m":
        validateRohrLaengeField();
        break;

      case "rohr_hoehe_m":
        validateRohrHoeheField();
        // abhängig: Fläche darf nicht größer als Rohrhöhe sein
        validateHoeheFlaecheField();
        break;

      case "hoehe_flaeche_m":
        validateHoeheFlaecheField();
        break;

      default:
        break;
    }
  }, true); // << wichtig: blur bubbelt nicht
});

// --- Globale Hooks für index.html ---
window.initSteherDropdowns = initSteherDropdowns;
window.submitSteher = submitSteher;