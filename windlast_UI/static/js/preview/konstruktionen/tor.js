// preview/konstruktionen/tor.js
// Baut die Bauelemente für ein Tor (wie im Core) und rendert eine Vorschau
// Abhängigkeiten: preview/bauelemente/bodenplatte.js, preview/bauelemente/traversenstrecke.js
// Nutzung:
//   import { mountTorPreview, renderTor, buildTorElements } from './preview/konstruktionen/tor.js';
//   const { unmount } = mountTorPreview(document.querySelector('#preview-iso'));
//   // oder manuell: renderTor(svgEl, params)

import { makeBodenplatte, drawBodenplatte } from '../bauelemente/bodenplatte.js';
import { makeTraversenstrecke, drawTraversenstrecke } from '../bauelemente/traversenstrecke.js';

// --- kleine Helper
const DEG = Math.PI / 180;
const AZ = 45 * DEG;
const SX = Math.sin(35.264 * DEG);
const CZ = Math.cos(AZ);

function ensureSvg(container){
  if (container instanceof SVGSVGElement) return container;
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('width','100%');
  svg.setAttribute('height','100%');
  svg.setAttribute('viewBox','0 0 100 100');
  svg.classList.add('tor-preview');
  container.innerHTML = '';
  container.appendChild(svg);
  return svg;
}

function clear(el){ while(el.firstChild) el.removeChild(el.firstChild); }

function S(tag, attrs = {}, text){
  const NS = 'http://www.w3.org/2000/svg';
  const n = document.createElementNS(NS, tag);
  for (const [k,v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (text != null) n.textContent = text;
  return n;
}

// --- Public API
/**
 * Erzeugt die Tor-Bauelemente (1:1 analog zum Core-Aufbau)
 * @param {Object} p
 * @param {number} p.B - Breite (m)
 * @param {number} p.H - Höhe (m)
 * @param {Object} p.traverseSpec - Spez der Traverse (mind. hoehe ODER t, anzeige_name optional)
 * @param {Object} p.platteSpec - Spez der Bodenplatte (mind. kantenlaenge ODER a, anzeige_name optional)
 * @param {('UP'|'DOWN'|'SIDE')} [p.orient='UP'] - Traversenausrichtung
 */
export function buildTorElements(p){
  const B = Number(p.B) || 6;
  const H = Number(p.H) || 4;
  const orient = (p.orient || p.traversen_orientierung || 'UP').toUpperCase();

  // Traverse- & Plattenmaße robust lesen
  const t = Number(p.t ?? p.traverseSpec?.hoehe ?? p.traverseSpec?.t) || 0.29; // Profilhöhe
  const a = Number(p.a ?? p.platteSpec?.kantenlaenge ?? p.platteSpec?.a) || 0.60; // Plattenkante
  const trLabel = p.traverseSpec?.anzeige_name ?? p.traverseSpec?.label ?? null;
  const bpLabel = p.platteSpec?.anzeige_name ?? p.platteSpec?.label ?? null;

  // Orientierungsversionen: einfache Richtungsvektoren (Welt)
  const vecs = orient === 'DOWN'
    ? { links:[ 1,0,0], oben:[ 0,0,-1], rechts:[-1,0,0] }
    : orient === 'SIDE'
      ? { links:[0,1,0], oben:[0,1,0], rechts:[0,1,0] }
      : { links:[-1,0,0], oben:[0,0, 1], rechts:[ 1,0,0] }; // UP (default)

  const elements = [];

  // Traversen: links / oben / rechts (Offsets wie im Core: t/2 von Außenkante)
  elements.push(
    makeTraversenstrecke({ id:'Strecke_Links',  start:[ t/2,0,0],    ende:[ t/2,0,H],      orientierung:vecs.links,  t, label:trLabel }),
    makeTraversenstrecke({ id:'Strecke_Oben',   start:[ 0,  0,H-t/2], ende:[ B,  0,H-t/2], orientierung:vecs.oben,   t, label:trLabel }),
    makeTraversenstrecke({ id:'Strecke_Rechts', start:[ B-t/2,0,0],   ende:[ B-t/2,0,H],   orientierung:vecs.rechts, t, label:trLabel }),
  );

  // Bodenplatten: mittig unter den Pfosten
  elements.push(
    makeBodenplatte({ id:'Bodenplatte_Links',  mittelpunkt:[0,0,0], orientierung:[0,0,1], drehung:vecs.links,  a, label:bpLabel }),
    makeBodenplatte({ id:'Bodenplatte_Rechts', mittelpunkt:[B,0,0], orientierung:[0,0,1], drehung:vecs.rechts, a, label:bpLabel }),
  );

  return elements;
}

/**
 * Rendert das Tor in ein SVG (Container oder <svg>)
 * @param {HTMLElement|SVGSVGElement} containerOrSvg
 * @param {Object} params – siehe buildTorElements
 */
export function renderTor(containerOrSvg, params){
  const svg = ensureSvg(containerOrSvg);
  clear(svg);

  // Skala: Pixel pro Meter
  const SCALE = 100; // 1 m -> 100 px
  const margin = 20; // px (Screenmaß)

  // Elemente erzeugen
  const elems = buildTorElements(params || {});

  // Szene-Gruppe mit Skalierung
  const scene = S('g', { transform: `scale(${SCALE})` });
  svg.appendChild(scene);

  // Zeichnen
  for (const el of elems){
    if (el.type === 'Bodenplatte') drawBodenplatte(scene, el);
    else if (el.type === 'Traversenstrecke') drawTraversenstrecke(scene, el);
  }

  // rudimentäre ViewBox-Anpassung (isometrische Approximation):
  const B = Number(params?.B) || 6;
  const H = Number(params?.H) || 4;
  const a = Number(params?.a ?? params?.platteSpec?.kantenlaenge ?? params?.platteSpec?.a) || 0.60;
  const wMeters = B*CZ + a;            // projizierte Breite ~ x*cz
  const hMeters = H*SX + a*0.8 + 0.5;  // projizierte Höhe ~ z*sin(ax) + etwas Luft für Labels
  const vbW = Math.max(1, wMeters * SCALE) + 2*margin;
  const vbH = Math.max(1, hMeters * SCALE) + 2*margin;
  svg.setAttribute('viewBox', `${-margin} ${-vbH + margin} ${vbW} ${vbH}`);

  return { svg, elements: elems };
}

/**
 * Mountet eine Live-Vorschau: hört auf `tor:params` und resizet mit dem Container
 * @param {HTMLElement|SVGSVGElement} containerOrSvg
 * @returns {{unmount:()=>void, rerender:(p:Object)=>void}}
 */
export function mountTorPreview(containerOrSvg){
  const svg = ensureSvg(containerOrSvg);
  let current = { B:6, H:4 };
  let mounted = true;

  const rerender = (p)=>{
    current = { ...current, ...(p||{}) };
    if (!mounted) return;
    renderTor(svg, current);
  };

  // Erst-Render
  rerender(current);

  // Event-Listener
  const onParams = (ev)=> rerender(ev.detail || {});
  document.addEventListener('tor:params', onParams);

  // Resize-Observer (falls Container ein DIV ist)
  let ro = null;
  if (!(svg instanceof SVGSVGElement) && containerOrSvg instanceof HTMLElement) {
    ro = new ResizeObserver(()=> rerender(current));
    ro.observe(containerOrSvg);
  }

  return {
    unmount(){
      mounted = false;
      document.removeEventListener('tor:params', onParams);
      if (ro) ro.disconnect();
    },
    rerender
  };
}

// Optional: globale Registrierung für Nicht-Module
if (typeof window !== 'undefined') {
  window.PreviewKonstruktionen = window.PreviewKonstruktionen || {};
  window.PreviewKonstruktionen.Tor = { mountTorPreview, renderTor, buildTorElements };
}
