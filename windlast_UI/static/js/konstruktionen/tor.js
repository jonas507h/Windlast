import { buildTor } from '../build/build_tor.js';
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
    const opt = document.createElement("option");
    opt.value = value;      // Request-Wert (name_intern bzw. "beton"/"stahl"/...)
    opt.textContent = label; // Anzeige (anzeige_name bzw. Enum.value)
    el.appendChild(opt);
  }
  if (defaultValue !== null && defaultValue !== undefined) {
    el.value = defaultValue;
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
    fillSelect(document.getElementById("traverse_name_intern"), traversen);
    fillSelect(document.getElementById("bodenplatte_name_intern"), bps);
    fillSelect(document.getElementById("untergrund_typ"), untergruende, { defaultValue: "Beton" });

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

function validateTorForm() {
  let ok = true;

  // --- Header: Windzone ist Pflicht (Aufstelldauer explizit NICHT) ---
  const windzoneEl = document.getElementById('windzone');      // aus header form
  const windzoneOK = !!(windzoneEl && windzoneEl.value);
  // Header hat kein .field-Wrapper/Fehltext – wir markieren nur optisch (kein Text)
  if (windzoneEl) {
    const fakeField = windzoneEl.closest('.field') || windzoneEl.parentElement;
    if (fakeField) fakeField.classList.toggle('is-invalid', !windzoneOK);
    windzoneEl.setAttribute('aria-invalid', windzoneOK ? 'false' : 'true');
  }
  ok = ok && windzoneOK;

  // --- Tor-Eingaben: Höhe/Breite > 0 ---
  const hoeheEl = document.getElementById('hoehe_m');
  const breiteEl = document.getElementById('breite_m');
  const errH = document.getElementById('err-hoehe');
  const errB = document.getElementById('err-breite');

  const hoehe = parseFloat(hoeheEl?.value);
  const breite = parseFloat(breiteEl?.value);

  const hOK = isPositiveNumber(hoehe);
  showFieldError(hoeheEl, errH, !hOK, 'Bitte eine gültige Höhe > 0 angeben.');
  ok = ok && hOK;

  const bOK = isPositiveNumber(breite);
  showFieldError(breiteEl, errB, !bOK, 'Bitte eine gültige Breite > 0 angeben.');
  ok = ok && bOK;

  // --- Tor-Dropdowns: i. d. R. bereits gültig vorbelegt ---
  // traverse_name_intern, bodenplatte_name_intern, traversen_orientierung,
  // gummimatte, untergrund_typ: werden durch initTorDropdowns gefüllt,
  // inkl. Defaults (up/ja/Beton). → kein Fehlerfall zu erwarten. :contentReference[oaicite:4]{index=4}

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

    const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
    const gummimatte_bool = (gmVal === "ja");

    const breite_m = parseFloat(document.getElementById("breite_m").value);
    const hoehe_m  = parseFloat(document.getElementById("hoehe_m").value);
    const traverse_name_intern    = document.getElementById("traverse_name_intern").value;
    const bodenplatte_name_intern = document.getElementById("bodenplatte_name_intern").value;
    const orientierung            = readTraversenOrientierung();

    // 1) UI-Build → generische KONSTRUKTION
    const konstruktion = buildTor({
      breite_m,
      hoehe_m,
      traverse_name_intern,
      bodenplatte_name_intern,
      gummimatte: gummimatte_bool,
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
  }
}

// Funktion für Berechnen-Button, wenn das Dokument geladen ist
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitTor);
});

// --- Globale Hooks für index.html ---
window.initTorDropdowns = initTorDropdowns;
window.submitTor = submitTor;