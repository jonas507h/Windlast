// tor_preview.js — verbindet Formwerte → build_tor → render_konstruktion
// Erwartet: build_tor.js, linien_* und render_konstruktion.js sind erreichbar (ES-Module)

import { buildTor, ORIENTIERUNG } from '../build/build_tor.js';
import { render_konstruktion } from './render_konstruktion.js';
import { computeDimensionsTor } from './dimensions_tor.js';

function readTraversenOrientierungSafe() {
  const el = document.getElementById('traversen_orientierung');
  const v = String(el?.value ?? 'up').trim().toLowerCase();
  return (v === 'up' || v === 'side' || v === 'down') ? v : 'up';
}

function readFormForTor() {
  const breite = parseFloat(document.getElementById('breite_m')?.value);
  const hoehe  = parseFloat(document.getElementById('hoehe_m')?.value);

  const traverse_name_intern   = document.getElementById('traverse_name_intern')?.value || 'TRUSS';
  const bodenplatte_name_intern= document.getElementById('bodenplatte_name_intern')?.value || 'BP';
  const gmVal = document.getElementById('gummimatte')?.value || 'ja';
  const gummimatte = (gmVal === 'ja');
  const orientierung = readTraversenOrientierungSafe();

  return {
    breite_m: isFinite(breite) && breite > 0 ? breite : 4,
    hoehe_m:  isFinite(hoehe)  && hoehe  > 0 ? hoehe  : 3,
    traverse_name_intern,
    bodenplatte_name_intern,
    gummimatte,
    orientierung,
  };
}

export function mountTorPreview(mountEl) {
  let handle = null;

  function rerender() {
    const katalog = window.Catalog || null;
    const konstruktion = buildTor(readFormForTor(), katalog || undefined);
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
        computeDimensions: computeDimensionsTor,
      }
    );

    // alten Renderer jetzt entsorgen
    try { handle?.dispose?.(); } catch {}
    handle = next;
  }

  // initial
  rerender();

  // simple live update: auf Änderungen der relevanten Inputs reagieren
  const ids = ['breite_m','hoehe_m','traverse_name_intern','bodenplatte_name_intern','gummimatte','traversen_orientierung'];
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
window.PreviewKonstruktionen.Tor = { mountTorPreview };
