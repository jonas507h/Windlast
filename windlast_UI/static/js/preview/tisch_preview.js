// tisch_preview.js — verbindet Formwerte → build_tisch → render_konstruktion
// Erwartet: build_tisch.js, linien_* und render_konstruktion.js sind erreichbar (ES-Module)

import { buildTisch, validateTischInputs} from '../build/build_tisch.js';
import { render_konstruktion } from './render_konstruktion.js';
import { computeDimensionsTisch } from './dimensions_tisch.js';

function readFormForTisch() {
  const breite = parseFloat(document.getElementById('breite_m')?.value);
  const hoehe  = parseFloat(document.getElementById('hoehe_m')?.value);
  const tiefe  = parseFloat(document.getElementById('tiefe_m')?.value);
  const hoeheFlaeche = document.getElementById('hoehe_flaeche_m')?.value;

  const traverse_name_intern   = document.getElementById('traverse_name_intern')?.value || 'TRUSS';
  const bodenplatte_name_intern= document.getElementById('bodenplatte_name_intern')?.value || 'BP';
  const gmVal = document.getElementById('gummimatte')?.value || 'ja';
  const gummimatte = (gmVal === 'ja');
  const untergrund = document.getElementById('untergrund_typ')?.value || 'BETON';

  return {
    breite_m: isFinite(breite) && breite > 0 ? breite : 8,
    hoehe_m:  isFinite(hoehe)  && hoehe  > 0 ? hoehe  : 4,
    tiefe_m:  isFinite(tiefe)  && tiefe  > 0 ? tiefe  : 6,
    hoehe_flaeche_m: isFinite(parseFloat(hoeheFlaeche)) ? parseFloat(hoeheFlaeche) : null,
    traverse_name_intern,
    bodenplatte_name_intern,
    gummimatte,
    untergrund,
  };
}

export function mountTischPreview(mountEl) {
  let handle = null;

  function rerender() {
    const katalog = window.Catalog;
    if (!katalog) return;

    let inputs;
    try { inputs = readFormForTisch() } catch { return }
    try { validateTischInputs(inputs, katalog) } catch { return }

    let konstruktion;
    try { konstruktion = buildTisch(inputs, katalog) } catch { return}
    
    try { mountEl.innerHTML = ''; } catch {}

    const next = render_konstruktion(
      mountEl,
      konstruktion,
      {
        preserveView: true,
        prevView: handle,
        showDimensions: true,
        computeDimensions: computeDimensionsTisch,
      }
    );

    try { handle?.dispose?.(); } catch {}
    handle = next;
  }

  // initial
  rerender();

  // simple live update: auf Änderungen der relevanten Inputs reagieren
  const ids = ['breite_m','hoehe_m','tiefe_m','traverse_name_intern','bodenplatte_name_intern','gummimatte','untergrund_typ', 'hoehe_flaeche_m'];
  const listeners = [];
  for (const id of ids) {
    const el = document.getElementById(id);
    if (!el) continue;
    const fn = () => rerender();
    const ev = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(ev, fn);
    listeners.push([el, ev, fn]);
  }

  // public API (zum unmounten bei View-Wechsel)
  return {
    unmount(){
      for (const [el, ev, fn] of listeners) {
        try { el.removeEventListener(ev, fn); } catch {}
      }
      try { mountEl.innerHTML = ''; } catch {}
      try { handle?.dispose?.(); } catch {}
      handle = null;
    }
  };
}

// globale Bridge, damit index.html die Preview montieren kann
window.PreviewKonstruktionen = window.PreviewKonstruktionen || {};
window.PreviewKonstruktionen.Tisch = { mountTischPreview };