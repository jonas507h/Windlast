  // steher_preview.js — verbindet Formwerte → build_steher → render_konstruktion
// Erwartet: build_steher.js, linien_* und render_konstruktion.js sind erreichbar (ES-Module)

import { buildSteher } from '../build/build_steher.js';
import { render_konstruktion } from './render_konstruktion.js';
import { computeDimensionsSteher } from './dimensions_steher.js';

function readFormForSteher() {
  const hoehe  = parseFloat(document.getElementById('hoehe_m')?.value);
  const rohr_laenge  = parseFloat(document.getElementById('rohr_laenge_m')?.value);
  const rohr_hoehe  = parseFloat(document.getElementById('rohr_hoehe_m')?.value);
  const hoeheFlaeche = document.getElementById('hoehe_flaeche_m')?.value;

  const traverse_name_intern   = document.getElementById('traverse_name_intern')?.value || 'TRUSS';
  const bodenplatte_name_intern= document.getElementById('bodenplatte_name_intern')?.value || 'BP';
  const rohr_name_intern       = document.getElementById('rohr_name_intern')?.value || 'ROHR';
  const gmVal = document.getElementById('gummimatte')?.value || 'ja';
  const gummimatte = (gmVal === 'ja');
  const untergrund = document.getElementById('untergrund_typ')?.value || 'BETON';

  return {
    hoehe_m:  isFinite(hoehe)  && hoehe  > 0 ? hoehe  : 4.5,
    rohr_laenge_m: isFinite(rohr_laenge) && rohr_laenge > 0 ? rohr_laenge : 1.5,
    rohr_hoehe_m: isFinite(rohr_hoehe) && rohr_hoehe > 0 ? rohr_hoehe : 4.0,
    hoehe_flaeche_m: isFinite(parseFloat(hoeheFlaeche)) ? parseFloat(hoeheFlaeche) : null,
    traverse_name_intern,
    bodenplatte_name_intern,
    rohr_name_intern,
    gummimatte,
    untergrund,
  };
}

export function mountSteherPreview(mountEl) {
  let handle = null;

  function rerender() {
    const katalog = window.Catalog || null;
    const konstruktion = buildSteher(readFormForSteher(), katalog || undefined);
    // erst Container leeren (altes Canvas raus), aber alten Handle noch NICHT dispose'n,
    // damit wir seine Kamera/Target als prevView verwenden können
    try { mountEl.innerHTML = ''; } catch {}

    const next = render_konstruktion(
      mountEl,
      konstruktion,
      {
        preserveView: true,
        prevView: handle,
        showDimensions: true,
        computeDimensions: computeDimensionsSteher,
      }
    );

    // alten Renderer jetzt entsorgen
    try { handle?.dispose?.(); } catch {}
    handle = next;
  }

  // initial
  rerender();

  // simple live update: auf Änderungen der relevanten Inputs reagieren
  const ids = ['hoehe_m','rohr_laenge_m','rohr_hoehe_m','traverse_name_intern','bodenplatte_name_intern','rohr_name_intern','gummimatte','untergrund_typ','hoehe_flaeche_m'];
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
window.PreviewKonstruktionen.Steher = { mountSteherPreview };
