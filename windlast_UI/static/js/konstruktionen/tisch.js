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

async function submitTor() {
  // Formulardaten sammeln und an API senden
  try {
    // Gummimatte-Wert holen (ja/nein); wir reichen ihn als Boolean weiter
    const gmVal = document.getElementById("gummimatte")?.value ?? "ja";
    const gummimatte_bool = (gmVal === "ja");

    // Sammeln der Eingabewerte und verpacken
    const payload = {
      breite_m: parseFloat(document.getElementById("breite_m").value),
      hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
      traverse_name_intern: document.getElementById("traverse_name_intern").value,
      bodenplatte_name_intern: document.getElementById("bodenplatte_name_intern").value,
      untergrund_typ: document.getElementById("untergrund_typ").value, // z.B. "beton"
      gummimatte: gummimatte_bool,
      orientierung: readTraversenOrientierung(), // z.B. "up"
      ...readHeaderValues(),
    };

    const data = await fetchJSON("/api/v1/tor/berechnen", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // 1) bevorzugt: direkte Funktion (falls Footer sie anbietet)
    if (typeof window.updateFooterResults === "function") {
      window.updateFooterResults(data);
    } else {
      // 2) Fallback: CustomEvent im selben Dokument
      document.dispatchEvent(new CustomEvent("results:update", { detail: data }));
    }
  } catch (e) {
    console.error("Tor-Berechnung fehlgeschlagen:", e);
    // optional: ein schlichtes Toast-Event, falls du es nutzen willst
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
