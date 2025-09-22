const NORM_ID = {
  "EN_13814_2005": "en13814_2005",
  "EN_17879_2024": "en17879_2024",
  "EN_1991_1_4_2010": "en1991_2010",
};

function setCell(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  if (val === null || val === undefined || Number.isNaN(val)) {
    el.textContent = "—";
  } else {
    el.textContent = (Math.round(val * 100) / 100).toFixed(2);
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
