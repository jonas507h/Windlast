// utils/forms.js
import { fetchKompatibilitaet } from "./reibwert.js";
import { showFieldWarn } from "./error.js";

export function fillSelect(el, options, { placeholder = null, defaultValue = null } = {}) {
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
    opt.value = value;
    opt.textContent = label;
    el.appendChild(opt);
  }
  if (defaultValue !== null && defaultValue !== undefined) {
    el.value = defaultValue;
  }
}

export function applyBodenplattenFilterByTraverse({ keepIfPossible = true } = {}) {
  const trEl = document.getElementById("traverse_name_intern");
  const bpEl = document.getElementById("bodenplatte_name_intern");
  if (!trEl || !bpEl || !window.Catalog) return;

  const trVal = trEl.value;
  const trav = window.Catalog.getTraverse?.(trVal);
  const travSystem = trav?.traversensystem;
  if (!travSystem) return;

  const allBps = window.Catalog.bps || [];

  const filtered = allBps.filter(bp => {
    const systems = bp?.traversensysteme || [];
    return systems.includes("ALLE") || systems.includes(travSystem);
  });

  // Auswahl möglichst beibehalten, sonst auf erstes erlaubtes setzen
  const prev = bpEl.value;
  const next = (keepIfPossible && filtered.some(o => o.value === prev))
    ? prev
    : (filtered[0]?.value ?? "");

  fillSelect(bpEl, filtered, { defaultValue: next });

  const warnBp = document.getElementById("warn-bodenplatte");
  if (prev && prev !== bpEl.value) {
    showFieldWarn(bpEl, warnBp, true, "Achtung: Auswahl wurde automatisch angepasst.");
  }
}

let _isApplyingReibwertFilter = false;
export async function applyReibwertDropdownFiltering({ rerunIfChanged = true } = {}) {
  // verhindert Re-Entrancy/Loops
  if (_isApplyingReibwertFilter) return;
  _isApplyingReibwertFilter = true;

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

    // --- (1) Gummimatte Optionen filtern ---
    const gmOptionsAll = [
      { value: "ja", label: "Ja" },
      { value: "nein", label: "Nein" },
    ];
    const gmOptions = gmOptionsAll.filter(o => gmAllowed.includes(o.value));

    const prevGm = gmEl.value;
    fillSelect(gmEl, gmOptions, { defaultValue: gmEffective });
    const warnGm = document.getElementById("warn-gummimatte");
    if (prevGm && prevGm !== gmEl.value) {
      showFieldWarn(gmEl, warnGm, true, "Achtung: Auswahl wurde automatisch angepasst.");
    }

    // --- (2) Untergrund filtern ---
    const ugAll = window.Catalog.untergruende || [];
    const allowedSet = new Set(ugAllowed);

    // Wenn API leer liefert, lieber NICHT alles wegfiltern:
    const ugFiltered = (ugAllowed.length > 0)
      ? ugAll.filter(o => allowedSet.has(o.value))
      : ugAll;

    const prevUg = ugEl.value;
    const nextUg = ugFiltered.some(o => o.value === prevUg)
      ? prevUg
      : (ugFiltered[0]?.value ?? "");

    fillSelect(ugEl, ugFiltered, { defaultValue: nextUg });
    const warnUg = document.getElementById("warn-untergrund");
    if (prevUg && prevUg !== ugEl.value) {
      showFieldWarn(ugEl, warnUg, true, "Achtung: Auswahl wurde automatisch angepasst.");
    }

    // Wenn sich gm durch "effective" geändert hat, kann sich die Untergrund-Menge ändern.
    // Einmal sauber nachziehen (max. 1x), damit state konsistent ist.
    if (rerunIfChanged && prevGm !== gmEl.value) {
      _isApplyingReibwertFilter = false;
      return applyReibwertDropdownFiltering({ rerunIfChanged: false });
    }
  } catch (e) {
    console.error("Reibwert-Filterung fehlgeschlagen:", e);
  } finally {
    _isApplyingReibwertFilter = false;
  }
}