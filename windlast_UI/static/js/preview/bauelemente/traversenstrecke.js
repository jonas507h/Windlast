// preview/bauelemente/traversenstrecke.js
// Adapter für die Vorschau: Traversenstrecke als 3D-Linie (+ optionale Profil-/Orientierungs-Markierung)
// Exportiert:
// - makeTraversenstrecke(dto)
// - drawTraversenstrecke(svgRoot, el, helpers?)
// Registriert sich optional unter window.Bauelemente.Traversenstrecke


// --- Isometrische Projektion (Fallback)
const DEG = Math.PI / 180;
const AX = 35.264 * DEG;
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
* DTO für Traversenstrecke
* @param {Object} p
* @param {string} [p.id]
* @param {[number,number,number]} p.start // [x,y,z] in m
* @param {[number,number,number]} p.ende // [x,y,z] in m
* @param {[number,number,number]} [p.orientierung] // Richtung der „Spitze“ (nur für Marker)
* @param {number} [p.t] // Profilhöhe (nur für optionale Darstellung)
* @param {string} [p.label]
* @param {Object} [p.style]
*/
export function makeTraversenstrecke(p){
const { id = 'Traversenstrecke', start, ende, orientierung = [0,0,1], t = 0.29, label = null, style = {} } = p;
return { type: 'Traversenstrecke', id, start: [...start], ende: [...ende], orientierung: [...orientierung], t: Number(t)||0, label, style };
}


/**
* Zeichnet eine Traversenstrecke als Linie inkl. optionalem Orientation-Marker
* @param {SVGElement} svgRoot
* @param {ReturnType<typeof makeTraversenstrecke>} el
* @param {Object} [helpers]
* @param {(p:{x:number,y:number,z:number})=>{X:number,Y:number,Z:number}} [helpers.project]
* @param {(tag:string,attrs?:Object,text?:string)=>SVGElement} [helpers.S]
*/
export function drawTraversenstrecke(svgRoot, el, helpers = {}){
const project = helpers.project || projectIso;
const _S = helpers.S || S;


const [x1,y1,z1] = el.start;
const [x2,y2,z2] = el.ende;
const P1 = project({ x:x1, y:y1, z:z1 });
const P2 = project({ x:x2, y:y2, z:z2 });

const g = _S('g', { class: 'truss' });

// Kante (sichtbar/verdeckt: naive Regel über Z-Mittelwert)
g.appendChild(_S('line', {
  x1: P1.X, y1: P1.Y, x2: P2.X, y2: P2.Y,
  stroke: 'currentColor', 'stroke-width': 0.04, fill: 'none'
}));


// Optional: kurzer Marker orthogonal zur Stabachse, zeigt „Spitze“-Richtung
/*
if (el.orientierung) {
const tip = { x: x1 + el.orientierung[0], y: y1 + el.orientierung[1], z: z1 + el.orientierung[2] };
const T = project(tip);
const vx = T.X - P1.X, vy = T.Y - P1.Y;
// Kleines Dreieck an P1
const L = 0.25; // Marker-Länge in m (Previewmaß)
const nx = -(P2.Y - P1.Y), ny = (P2.X - P1.X); // 2D-Normalvektor (Bildraum)
const nlen = Math.hypot(nx, ny) || 1;
const ux = nx / nlen, uy = ny / nlen;
const a = _S('polygon', {
points: [
`${P1.X},${P1.Y}`,
`${P1.X + vx*0.2 + ux*L},${P1.Y + vy*0.2 + uy*L}`,
`${P1.X + vx*0.2 - ux*L},${P1.Y + vy*0.2 - uy*L}`
].join(' '),
class: 'truss-marker'
});
g.appendChild(a);
}
*/


// Label (mittig)
if (el.label) {
  const mx = (P1.X + P2.X) / 2;
  const my = (P1.Y + P2.Y) / 2;
  g.appendChild(_S('text', {
    x: mx, y: my - 0.08, 'text-anchor': 'middle',
    class: 'truss-label'
  }, el.label));
}


svgRoot.appendChild(g);
return g;
}

if (typeof window !== 'undefined') {
window.Bauelemente = window.Bauelemente || {};
window.Bauelemente.Traversenstrecke = { make: makeTraversenstrecke, draw: drawTraversenstrecke };
}