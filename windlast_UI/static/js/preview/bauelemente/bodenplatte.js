// preview/bauelemente/bodenplatte.js
// Adapter für die Vorschau: Bodenplatte als zentriertes, drehbares Rechteck.
// Exportiert:
// - makeBodenplatte(dto)
// - drawBodenplatte(svgRoot, el, helpers?)
// Optional: registriert sich unter window.Bauelemente.Bodenplatte


// --- Isometrische Projektion (wie im Renderer) — Fallback, falls kein Helper übergeben wird
const DEG = Math.PI / 180;
const AX = 35.264 * DEG; // ≈ arctan(sin(45°))
const AZ = 45 * DEG;
const cx = Math.cos(AX), sx = Math.sin(AX);
const cz = Math.cos(AZ), sz = Math.sin(AZ);


function projectIso(p){
const x1 = cz*p.x - sz*p.y;
const y1 = sz*p.x + cz*p.y;
const z1 = p.z;
const X = x1;
const Y = cx*y1 - sx*z1;
const Z = sx*y1 + cx*z1;
return { X, Y, Z };
}


function S(tag, attrs = {}, text){
const NS = 'http://www.w3.org/2000/svg';
const n = document.createElementNS(NS, tag);
for (const [k,v] of Object.entries(attrs)) n.setAttribute(k, v);
if (text != null) n.textContent = text;
return n;
}

/**
* Erzeugt ein render-agnostisches DTO der Bodenplatte
* @param {Object} p
* @param {string} [p.id]
* @param {string} [p.name_intern]
* @param {[number,number,number]} p.mittelpunkt // [x,y,z] in m
* @param {[number,number,number]} p.orientierung // Normalvektor
* @param {[number,number,number]} p.drehung // Richtungsvektor entlang langer Kante
* @param {number} p.a // Kantenlänge in m (quadratisch)
* @param {string} [p.label]
* @param {Object} [p.style]
*/
export function makeBodenplatte(p){
const {
id = 'Bodenplatte', name_intern = null, mittelpunkt, orientierung,
drehung, a = 0.6, label = null, style = {}
} = p;
return {
type: 'Bodenplatte', id, name_intern,
mittelpunkt: [...mittelpunkt], orientierung: [...orientierung], drehung: [...drehung],
a: Number(a) || 0.6, label, style
};
}

/**
* Zeichnet die Bodenplatte als drehbares, zentriertes Rechteck
* @param {SVGElement} svgRoot – Elternknoten/Gruppe im selben Koordinatensystem wie der Renderer
* @param {ReturnType<typeof makeBodenplatte>} el
* @param {Object} [helpers]
* @param {(p:{x:number,y:number,z:number})=>{X:number,Y:number,Z:number}} [helpers.project]
* @param {(tag:string,attrs?:Object,text?:string)=>SVGElement} [helpers.S]
*/
export function drawBodenplatte(svgRoot, el, helpers = {}){
const project = helpers.project || projectIso;
const _S = helpers.S || S;


const a = el.a; // Seitenlänge in m (weltkoords)
const [cxW, cyW, czW] = el.mittelpunkt;
const c2 = a/2;


// Screen-Position des Mittelpunkts
const C = project({ x: cxW, y: cyW, z: czW });


// Bildschirm-Richtung der Drehachse (drehung)
const dirW = { x: cxW + el.drehung[0], y: cyW + el.drehung[1], z: czW + el.drehung[2] };
const D = project(dirW);
const vx = D.X - C.X, vy = D.Y - C.Y;
const angleDeg = Math.atan2(vy, vx) * 180 / Math.PI;


// Gruppe mit Drehung um den Mittelpunkt
const g = _S('g', { class: 'baseplate', transform: `rotate(${angleDeg} ${C.X} ${C.Y})` });


// Rechteck: center-basiert (SVG kennt das nicht, daher via x/y)
g.appendChild(_S('rect', {
  x: (C.X - c2), y: (C.Y - c2),
  width: a, height: a,
  rx: 0.06, ry: 0.06,               // leichte Rundung (in m, nicht px)
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 0.04               // ~4 cm in der Vorschau
}));

// Label (optional)
if (el.label) {
g.appendChild(_S('text', {
x: C.X, y: C.Y + (a*0.65), 'text-anchor': 'middle', class: 'bp-label'
}, el.label));
}


// Stil-Defaults via <style> in Renderer; Klassen: .baseplate .bp-shape .bp-label
svgRoot.appendChild(g);
return g;
}

// Global Registry (optional, falls ohne Module genutzt)
if (typeof window !== 'undefined') {
window.Bauelemente = window.Bauelemente || {};
window.Bauelemente.Bodenplatte = { make: makeBodenplatte, draw: drawBodenplatte };
}