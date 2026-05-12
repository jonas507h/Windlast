import { prettyMetaKey, prettyMetaValue } from "../utils/formatierung.js";

function appendRow(root, keyText, value) {
  const row = document.createElement("div");
  row.className = "ctx-row";

  const key = document.createElement("span");
  key.className = "ctx-k";
  key.textContent = `${keyText}: `;

  const val = document.createElement("span");
  val.className = "ctx-v";
  val.textContent = prettyMetaValue(value);

  row.appendChild(key);
  row.appendChild(val);
  root.appendChild(row);
}

export function buildErgebnisTooltipContent(meta = {}) {
  const root = document.createElement("div");
  root.className = "ctx-tooltip";

  const entries = Object.entries(meta || {});

  if (!entries.length) {
    root.textContent = "Keine Meta-Daten.";
    return root;
  }

  const realKeyFlag = !!(window.APP_STATE?.flags?.show_real_meta_keys);

  for (const [k, v] of entries) {
    let metaKey = k;
    let metaValue = v;
    if (!realKeyFlag) {
      metaKey = prettyMetaKey(k);
      metaValue = prettyMetaValue(v);
    }
    appendRow(root, metaKey, metaValue);
  }

  return root;
}