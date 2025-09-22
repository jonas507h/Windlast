const NORM_ID = {
  "EN_13814_2005": "en13814_2005",
  "EN_17879_2024": "en17879_2024",
  "EN_1991_1_4_2010": "en1991_2010",
};

function setCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;

  // ∞-Darstellung
  if (val === "INF" || val === "-INF") {
    el.textContent = val === "INF" ? "∞" : "−∞";
    el.title = "Keine ungünstigen Kräfte → Sicherheit → ∞";
    return;
  }

  const num = typeof val === "string" ? Number(val) : val;
  if (num === null || num === undefined || Number.isNaN(num)) {
    el.textContent = "—";
    el.title = "";
  } else {
    el.textContent = (Math.round(num * 100) / 100).toFixed(2);
    el.title = "";
  }
}

function updateFooter(payload) {
  const normen = payload?.normen || {};
  for (const [normKey, vals] of Object.entries(normen)) {
    const suf = NORM_ID[normKey];
    if (!suf) continue;
    setCell(`kipp_${suf}`,   vals.kipp);
    setCell(`gleit_${suf}`,  vals.gleit);
    setCell(`abhebe_${suf}`, vals.abhebe);
  }
}

window.addEventListener("message", (ev) => {
  const msg = ev.data;
  if (msg?.type === "results/update") {
    updateFooter(msg.payload);
  }
});
