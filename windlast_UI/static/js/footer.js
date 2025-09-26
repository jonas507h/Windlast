const NORM_ID = {
  "EN_13814_2005": "en13814_2005",
  "EN_17879_2024": "en17879_2024",
  "EN_1991_1_4_2010": "en1991_2010",
};

function klassifizierung_anwenden(el, good) {
  if (!el) return;
  el.classList.remove("val-ok", "val-bad");
  el.classList.add(good ? "val-ok" : "val-bad");
}

function sicherheit_klassifizieren(val) {
  if (val === "INF") return true;
  if (val === "-INF") return false;
  const num = typeof val === "string" ? Number(val) : val;
  if (num === null || num === undefined || Number.isNaN(num)) return false;
  return num >= 1.0;
}

function formatBallast(val_kg) {
  if (val_kg === "INF" || val_kg === "-INF") return val_kg === "INF" ? "∞" : "−∞";
  const n = typeof val_kg === "string" ? Number(val_kg) : val_kg;
  if (!isFinite(n)) return "—";
  if (n <= 0) return "0 kg";

  // > 1000 kg -> in kg, Mindestschritt 10 kg, immer aufrunden
  if (n < 1000) {
    const rounded = Math.ceil(n / 10 ) * 10;
    return `${rounded.toLocaleString("de-DE")} kg`;
  }

  // 1000-9999 kg -> x,x t, Mindestschritt 0,1 t, immer aufrunden
  if (n < 10000) {
    const t = n / 1000;
    const rounded = Math.ceil(t * 10) / 10;
    return `${rounded.toLocaleString("de-DE")} t`;
  }

  // >= 10000 kg -> 3 signifikante Stellen in t, immer aufrunden
  const t = n / 1000;
  const magnitude = Math.pow(10, Math.floor(Math.log10(t)) - 2);
  const rounded = Math.ceil(t / magnitude) * magnitude;
  return `${rounded.toLocaleString("de-DE")} t`;
}

function setBallastCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = formatBallast(val);
  el.title = "";
}

function setCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;

  // Text setzen
  if (val === "INF" || val === "-INF") {
    el.textContent = val === "INF" ? "∞" : "−∞";
    el.title = "";
  } else {
    const num = typeof val === "string" ? Number(val) : val;
    if (num === null || num === undefined || Number.isNaN(num)) {
      el.textContent = "—";
      el.title = "";
    } else {
      el.textContent = (Math.round(num * 100) / 100).toFixed(2);
      el.title = "";
    }
  }

  // Klasse setzen (grün/rot)
  klassifizierung_anwenden(el, sicherheit_klassifizieren(val));
}

function updateFooter(payload) {
  const normen = payload?.normen || {};
  for (const [normKey, vals] of Object.entries(normen)) {
    const suf = NORM_ID[normKey];
    if (!suf) continue;
    setCell(`kipp_${suf}`,   vals.kipp);
    setCell(`gleit_${suf}`,  vals.gleit);
    setCell(`abhebe_${suf}`, vals.abhebe);
    setBallastCell(`ballast_${suf}`, vals.ballast);
  }
}

window.addEventListener("message", (ev) => {
  const msg = ev.data;
  if (msg?.type === "results/update") {
    updateFooter(msg.payload);
  }
});
