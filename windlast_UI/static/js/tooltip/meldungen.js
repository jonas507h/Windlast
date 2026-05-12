// js/tooltip/meldungen.js

import { prettyMetaKey, prettyMetaValue } from "../utils/formatierung.js";

function appendRow(root, keyText, value) {
  if (value == null || value === "") return;

  const row = document.createElement("div");
  row.className = "ctx-row";

  const key = document.createElement("span");
  key.className = "ctx-k";
  key.textContent = `${keyText}: `;

  const val = document.createElement("span");
  val.className = "ctx-v";
  val.textContent =
    typeof value === "string"
      ? value
      : JSON.stringify(value);

  row.appendChild(key);
  row.appendChild(val);
  root.appendChild(row);
}

function appendDivider(root) {
  const divider = document.createElement("div");
  divider.className = "tt-divider";
  root.appendChild(divider);
}

export function buildMeldungTooltipContent({
  code = null,
  severity = null,
  meta = null,
} = {}) {
  const root = document.createElement("div");
  root.className = "ctx-tooltip";

  appendRow(root, "Severity", severity);
  appendRow(root, "Code", code);

  const entries = Object.entries(meta || {});
  if (entries.length) {
    if (code || severity) appendDivider(root);

    for (const [k, v] of entries) {
      appendRow(root, prettyMetaKey(k), prettyMetaValue(v));
    }
  }

  if (!root.children.length) {
    root.textContent = "Keine Meldungsdetails.";
  }

  return root;
}