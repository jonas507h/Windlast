import { buildSteher } from '../build/build_steher.js';
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
  } catch (e) {
    console.error("Steher-Dropdowns konnten nicht geladen werden:", e);
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

function validateSteherForm() {
  let ok = true;

  // --- Header: Windzone ist Pflicht (Aufstelldauer explizit NICHT) ---
  const windzoneEl = document.getElementById('windzone'); // kommt aus dem Header
  const windzoneOK = !!(windzoneEl && windzoneEl.value);
  if (windzoneEl) {
    const fakeField = windzoneEl.closest('.field') || windzoneEl.parentElement;
    if (fakeField) fakeField.classList.toggle('is-invalid', !windzoneOK);
    windzoneEl.setAttribute('aria-invalid', windzoneOK ? 'false' : 'true');
  }
  ok = ok && windzoneOK;

  // --- Pflicht-Zahlenfelder: > 0 ---
  const hoeheEl = document.getElementById('hoehe_m');
  const rLaengeEl = document.getElementById('rohr_laenge_m');
  const rHoeheEl = document.getElementById('rohr_hoehe_m');
  const hoeheFlaecheEl = document.getElementById('hoehe_flaeche_m');

  const errH = document.getElementById('err-hoehe');
  const errL = document.getElementById('err-laenge');
  const errRH = document.getElementById('err-rhoehe');
  const errHF = document.getElementById('err-hoehe_flaeche');

  const rawHF = hoeheFlaecheEl?.value?.trim();
  const hoeheFlaeche = rawHF === "" ? null : parseFloat(rawHF);

  const hOK = isPositiveNumber(parseFloat(hoeheEl?.value));
  showFieldError(hoeheEl, errH, !hOK, 'Bitte eine gültige Höhe > 0 angeben.');
  ok = ok && hOK;

  const lOK = isPositiveNumber(parseFloat(rLaengeEl?.value));
  showFieldError(rLaengeEl, errL, !lOK, 'Bitte eine gültige Länge > 0 angeben.');
  ok = ok && lOK;

  let rhOK = true;
  let rhMsg = '';
  if (!(isPositiveNumber(parseFloat(rHoeheEl?.value)))) {
    rhOK = false;
    rhMsg = 'Bitte eine gültige Rohrhöhe > 0 angeben.';
  } else {
    const maxRH = (parseFloat(rHoeheEl?.value)) <= (parseFloat(hoeheEl?.value));

    if (!maxRH) {
      rhOK = false;
      rhMsg = 'Die Rohrhöhe darf die Gesamthöhe nicht überschreiten.';
    }
  }
  showFieldError(rHoeheEl, errRH, !rhOK, rhMsg);
  ok = ok && rhOK;

  let uOK = true;
  let uMsg = '';
  if (!(rawHF === "" || (isFinite(hoeheFlaeche) && hoeheFlaeche > 0))) {
    uOK = false;
    uMsg = 'Bitte eine Zahl > 0 angeben oder leer lassen.';
  } else if (hoeheFlaeche !== null && isFinite(hoeheFlaeche)) {
    const maxU = hoeheFlaeche < parseFloat(rHoeheEl?.value);
    if (!maxU) {
      uOK = false;
      uMsg = 'Die Höhe der Fläche muss kleiner als die Rohrhöhe sein.';
    }
  }
  showFieldError(hoeheFlaecheEl, errHF, !uOK, uMsg);
  ok = ok && uOK;

  // --- Pflicht-Dropdowns (haben meist Defaults, aber sicherheitshalber prüfen) ---
  // const reqSelectIds = [
  //   'traverse_name_intern',
  //   'rohr_name_intern',
  //   'bodenplatte_name_intern',
  //   'untergrund_typ',
  //   'gummimatte'
  // ];
  // for (const id of reqSelectIds) {
  //   const el = document.getElementById(id);
  //   if (!el) continue;
  //   const hasValue = !!el.value;
  //   const wrap = el.closest('.field');
  //   if (wrap) wrap.classList.toggle('is-invalid', !hasValue);
  //   el.setAttribute('aria-invalid', hasValue ? 'false' : 'true');
  //   ok = ok && hasValue;
  // }

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

// Funktion für Berechnen-Button, wenn das Dokument geladen ist
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitSteher);
});

// --- Globale Hooks für index.html ---
window.initSteherDropdowns = initSteherDropdowns;
window.submitSteher = submitSteher;