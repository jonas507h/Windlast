async function fetchOptions(url) {
  const res = await fetch(url, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
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
    opt.value = value;      // Request-Wert (name_intern bzw. "beton"/"stahl"/...)
    opt.textContent = label; // Anzeige (anzeige_name bzw. Enum.value)
    el.appendChild(opt);
  }
  if (defaultValue !== null && defaultValue !== undefined) {
    el.value = defaultValue;
  }
}

async function initTorDropdowns() {
  try {
    const [traversen, bps, untergruende] = await Promise.all([
      fetchOptions("/api/v1/catalog/traversen"),
      fetchOptions("/api/v1/catalog/bodenplatten"),
      fetchOptions("/api/v1/catalog/untergruende"),
    ]);

    fillSelect(document.getElementById("traverse_name_intern"), traversen);
    fillSelect(document.getElementById("bodenplatte_name_intern"), bps);
    fillSelect(document.getElementById("untergrund_typ"), untergruende, { defaultValue: "beton" });
  } catch (e) {
    console.error("Tor-Dropdowns konnten nicht geladen werden:", e);
  }
}

async function fetchJSON(url, opts) {
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
  // index.html hat 3 iframes, wir suchen den Header
  const topDoc = window.top?.document;
  const hdr = topDoc?.querySelector('iframe[src*="partials/header.html"]');
  return hdr?.contentDocument || hdr?.contentWindow?.document || null;
}

function readHeaderValues() {
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
  try {
    const payload = {
      breite_m: parseFloat(document.getElementById("breite_m").value),
      hoehe_m:  parseFloat(document.getElementById("hoehe_m").value),
      traverse_name_intern: document.getElementById("traverse_name_intern").value,
      bodenplatte_name_intern: document.getElementById("bodenplatte_name_intern").value,
      untergrund_typ: document.getElementById("untergrund_typ").value, // z.B. "beton"
      ...readHeaderValues(),
    };

    const data = await fetchJSON("/api/v1/tor/berechnen", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // an den Parent (index.html) schicken
    window.top?.postMessage({ type: "results", source: "tor", payload: data }, "*");
  } catch (e) {
    console.error("Tor-Berechnung fehlgeschlagen:", e);
    window.top?.postMessage({
      type: "toast",
      payload: { level: "error", text: String(e.message || e) },
    }, "*");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-berechnen");
  if (btn) btn.addEventListener("click", submitTor);
});

document.addEventListener("DOMContentLoaded", initTorDropdowns);
