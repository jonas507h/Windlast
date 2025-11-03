// render_dimensions.js — generischer Renderer für Maßpfeile (V0: linear)
import * as THREE from '/static/vendor/three.module.js';

// --- kleine Vektor-Utils (Array<3> kompatibel) ---
const v = {
  add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]],
  sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]],
  mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s],
  dot:(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],
  len:(a)=>Math.hypot(a[0],a[1],a[2]),
  norm:(a)=>{const L=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/L,a[1]/L,a[2]/L];},
  cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],
};

function makeTextSprite(
  text,
  {
    size = 0.22,
    fillStyle = '#0000ff',       // Textfarbe
    strokeStyle = '#1b3f8b',     // dunkle Outline für Kontrast
    strokeWidth = 6,             // kräftiger
    backgroundColor = '#ffffff', // opaker, weißer Hintergrund
    backgroundMargin = 0.04
  } = {}
) {
  // --- Text-Canvas vorbereiten ---
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const px = Math.floor(canvas.height * 0.78);
  ctx.font = `bold ${px}px Inter, system-ui, Arial`;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'center';

  // Hintergrund (weiß)
  ctx.fillStyle = backgroundColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Text mit Kontur
  ctx.fillStyle = fillStyle;
  if (strokeWidth > 0) {
    ctx.lineWidth = strokeWidth;
    ctx.strokeStyle = strokeStyle;
    ctx.strokeText(text, canvas.width / 2, canvas.height / 2);
  }
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);

  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;

  const mat = new THREE.SpriteMaterial({
    map: tex,
    depthTest: false,     // ← immer im Vordergrund
    depthWrite: false,
    transparent: false,   // ← opak (weißer Hintergrund!)
    toneMapped: false
  });
  const spr = new THREE.Sprite(mat);
  const aspect = canvas.width / canvas.height;

  // weiße Fläche etwas größer als Text
  spr.scale.set(size * aspect + backgroundMargin, size + backgroundMargin, 1);
  spr.renderOrder = 10000;    // ← sicher vor Linien/Pfeilen
  spr.frustumCulled = false;  // nicht versehentlich wegculllen
  return spr;
}

function pushLine(lines, a, b){
  lines.push(a[0],a[1],a[2], b[0],b[1],b[2]);
}

function renderLinear(spec, group){
  const { anchors, style={}, label } = spec;
  const a=anchors.a, b=anchors.b;
  const nRaw = anchors.dir ?? anchors.normal ?? [0,0,1];
  const n = v.norm(nRaw);
  const off = anchors.offset ?? 0.4;
  const a1 = v.add(a, v.mul(n, off));
  const b1 = v.add(b, v.mul(n, off));

  // Linien sammeln
  const points=[]; // Float32Array data
  const W = style.lineWidth ?? 2;                 // Liniendicke
  const color = style.color ?? 0x2d6cdf;   

  // Hilfslinien (von Anker zu Maßlinie)
  pushLine(points,a,a1); pushLine(points,b,b1);

  // Maßlinie
  pushLine(points,a1,b1);

  // --- Gefüllte Pfeile nach außen (DIN):
  // Spitze exakt am Maßende (a1/b1), Körper zeigt nach außen
  const d    = v.norm(v.sub(b1,a1));           // Richtung b1 - a1
  const ah   = anchors.arrowSize  ?? 0.18;     // halbe Pfeillänge (m)
  const aw   = anchors.arrowWidth ?? 0.09;     // halbe Pfeilbreite (m)
  addFilledArrow(group, a1, v.mul(d, +1), n, ah, aw, color); // a-Ende -> außen
  addFilledArrow(group, b1, v.mul(d, -1), n, ah, aw, color); // b-Ende -> außen

  // Linien-Mesh bauen
  const geom=new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(points,3));
  const mat=new THREE.LineBasicMaterial({
    color,
    depthTest: true,     // ← normale 3D-Sichtbarkeit
    depthWrite: true,
    transparent: false
  });
  const lines=new THREE.LineSegments(geom,mat);
  group.add(lines);

  // Label in der Mitte
  const mid = v.add(a1, v.mul(d, v.len(v.sub(b1,a1))/2));
  const txt = typeof label==='function' ? label({a,b,a1,b1}) : (label ?? '');
  if (txt) {
    const spr=makeTextSprite(txt, {
      size: anchors.textSize ?? 0.20,
      fillStyle: style.textColor ?? '#0000ff',
      strokeStyle: style.textOutline ?? '#ffffff',
      strokeWidth: style.textOutlineWidth ?? 4
    });
    spr.position.set(mid[0],mid[1],mid[2]);
    group.add(spr);
  }
}

export function render_dimensions(specs, {scene}){
  if (!specs || !specs.length) return null;
  const group=new THREE.Group();
  group.renderOrder = 10; // etwas später rendern lassen
  scene.add(group);

  for (const s of specs){
    if (s.kind === 'linear') renderLinear(s, group);
    // weitere Arten später: angle, chain, radial, …
  }
  return group;
}

// --- Helper: gefüllte Dreiecks-Pfeilspitze ---
function addFilledArrow(group, tip, dirOut, n, ah, aw, color){
  const d = v.norm(dirOut);                    // Außenrichtung
  const perp = v.norm(v.cross(d, n));          // Quer im Maß-Ebene
  const baseC = v.add(tip, v.mul(d, ah));      // Basismittelpunkt (außen)
  const p1 = tip;                               // Spitze liegt exakt am Maßende
  const p2 = v.add(baseC, v.mul(perp, +aw));    // Basis-Ecke 1
  const p3 = v.add(baseC, v.mul(perp, -aw));    // Basis-Ecke 2

  const pos = new Float32Array([...p1, ...p2, ...p3]);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
  g.setIndex([0,1,2]);

  const m = new THREE.MeshBasicMaterial({
    color,
    side: THREE.DoubleSide,
    depthTest:true,
    depthWrite:true,
    transparent:false,
    toneMapped: false
  });
  const mesh = new THREE.Mesh(g,m);
  group.add(mesh);

  // (optional) dünne Kontur für scharfe Kante
  const edgeGeom = new THREE.BufferGeometry();
  edgeGeom.setAttribute('position', new THREE.Float32BufferAttribute(
    [...p1,...p2,  ...p2,...p3,  ...p3,...p1], 3));
  const edgeMat = new THREE.LineBasicMaterial({
    color,
    depthTest: true,
    depthWrite: true,
    transparent: false,
    toneMapped: false
  });
  const edge = new THREE.LineSegments(edgeGeom, edgeMat);
  group.add(edge);
}