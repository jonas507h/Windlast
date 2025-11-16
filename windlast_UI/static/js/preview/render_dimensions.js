// render_dimensions.js — generischer Renderer für Maßpfeile (V0: linear)
import * as THREE from '/static/vendor/three.module.js';
import { getPreviewTheme } from './preview_farben.js';

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
    size = 0.20,                 // Texthöhe in m
    fillStyle = '#2d6cdf',
    strokeStyle = '#1b3f8b',
    strokeWidth = 6,             // Outline (px)
    backgroundColor = '#ffffff', // Kasten
    borderColor = '#2d6cdf',
    borderWidth = 2,             // Rahmen (px)
    paddingX = 28,               // horizontaler Innenabstand (px)
    paddingY = 20,               // vertikaler Innenabstand (px)
    cornerRadius = 12            // (px)
  } = {}
) {
  const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) ? window.devicePixelRatio : 1;

  // 1) Erst in "CSS-Pixeln" messen
  const measure = document.createElement('canvas').getContext('2d');
  const fontPx = 200; // groß messen -> später skaliert Sprite das auf "size" in m
  measure.font = `bold ${fontPx}px Inter, system-ui, Arial`;
  const textW = measure.measureText(text).width;
  const boxW_css = Math.ceil(textW + paddingX * 2 + strokeWidth * 2);
  const boxH_css = Math.ceil(fontPx + paddingY * 2 + strokeWidth * 2);

  // 2) Canvas physisch auf dpr skalieren (scharfe Textur)
  const canvas = document.createElement('canvas');
  canvas.width  = Math.ceil(boxW_css * dpr);
  canvas.height = Math.ceil(boxH_css * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  // 3) Styles & Schrift
  ctx.font = `bold ${fontPx}px Inter, system-ui, Arial`;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'center';

  // 4) Hintergrund + Rahmen (rundes Rechteck über gesamte Box)
  const r = Math.min(cornerRadius, boxH_css / 2, boxW_css / 2);
  const x = 0, y = 0, w = boxW_css, h = boxH_css;

  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y,     x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x,     y + h, r);
  ctx.arcTo(x,     y + h, x,     y,     r);
  ctx.arcTo(x,     y,     x + w, y,     r);
  ctx.closePath();

  ctx.fillStyle = backgroundColor;
  ctx.fill();
  if (borderWidth > 0) {
    ctx.lineWidth = borderWidth;
    ctx.strokeStyle = borderColor;
    ctx.stroke();
  }

  // 5) Text mit kräftiger Outline
  const cx = w / 2;
  const cy = h / 2;
  if (strokeWidth > 0) {
    ctx.lineWidth = strokeWidth;
    ctx.strokeStyle = strokeStyle;
    ctx.strokeText(text, cx, cy);
  }
  ctx.fillStyle = fillStyle;
  ctx.fillText(text, cx, cy);

  // 6) Sprite bauen (immer im Vordergrund)
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  const mat = new THREE.SpriteMaterial({
    map: tex,
    transparent: true,
    depthTest: false,
    depthWrite: false,
    toneMapped: false
  });
  const spr = new THREE.Sprite(mat);
  const aspect = boxW_css / boxH_css;
  spr.scale.set(size * aspect, size, 1); // Höhe = size (≈ 0,20 m)
  spr.renderOrder = 10000;
  spr.frustumCulled = false;
  return spr;
}

// Registry für Pfeilspitzen an einer Dimensions-Gruppe
function ensureArrowRegistry(group) {
  if (!group.userData) group.userData = {};
  if (!group.userData.dimensionArrows) group.userData.dimensionArrows = [];
  return group.userData.dimensionArrows;
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

  // Theme holen (Light/Dark)
  const theme = getPreviewTheme();
  const dimTheme = theme.dimensions || {};

  const color = style.color ?? dimTheme.lineColor ?? 0xff0000;

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
    depthTest: true,
    depthWrite: true,
    transparent: false
  });
  const lines=new THREE.LineSegments(geom,mat);
  group.add(lines);

  // Label in der Mitte
  const mid = v.add(a1, v.mul(d, v.len(v.sub(b1,a1))/2));
  const txt = typeof label==='function' ? label({a,b,a1,b1}) : (label ?? '');
  if (txt) {
    const spr = makeTextSprite(txt, {
      size: anchors.textSize ?? dimTheme.textSize ?? 0.20,
      fillStyle: style.textColor ?? dimTheme.textFill ?? '#ff0000',
      strokeStyle: style.textOutline ?? dimTheme.textOutline ?? '#ffffff',
      strokeWidth: style.textOutlineWidth ?? dimTheme.textOutlineWidth ?? 4,
      backgroundColor: style.textBackground ?? dimTheme.textBackground ?? '#ffffff',
      borderColor: style.textBorder ?? dimTheme.textBorder ?? color,
      borderWidth: style.textBorderWidth ?? dimTheme.textBorderWidth ?? 2,
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

  // 🔥 Pfeil registrieren, für Drehung zur Kamera
  const reg = ensureArrowRegistry(group);
  reg.push({
    tip:      [...tip],   // Kopie, damit wir safe sind
    dirOut:   [...d],     // Bemaßungsachse (Richtungsvektor)
    n:        [...n],     // ursprüngliche Normalenrichtung (Fallback)
    ah,
    aw,
    meshGeom: g,
    edgeGeom: edgeGeom,
  });
}

export function update_dimension_arrows(group, camera) {
  if (!group || !camera || !group.userData || !group.userData.dimensionArrows) return;
  const reg = group.userData.dimensionArrows;
  if (!reg.length) return;

  const camPos = camera.position;
  const cam = [camPos.x, camPos.y, camPos.z];

  for (const a of reg) {
    const { tip, dirOut, n, ah, aw, meshGeom, edgeGeom } = a;

    const d = v.norm(dirOut); // Bemaßungsachse

    // Vektor von Spitze zur Kamera
    let camVec = v.sub(cam, tip);
    camVec = v.norm(camVec);

    // Komponente der Kamerarichtung, die senkrecht zur Achse ist
    let camProj = v.sub(camVec, v.mul(d, v.dot(camVec, d)));
    const camProjLen = v.len(camProj);

    let perp;
    if (camProjLen > 1e-4) {
      // gewünschte Pfeil-Ebenen-Normale = projizierte Kamerarichtung
      const N = v.norm(camProj);
      // Pfeil liegt in Ebene aufgespannt von Achse d und perp:
      // Normale dieser Ebene = N
      perp = v.norm(v.cross(N, d));
    } else {
      // Kamera fast parallel zur Achse → auf ursprüngliche Orientierung zurückfallen
      perp = v.norm(v.cross(d, n));
    }

    const baseC = v.add(tip, v.mul(d, ah));
    const p1 = tip;
    const p2 = v.add(baseC, v.mul(perp, +aw));
    const p3 = v.add(baseC, v.mul(perp, -aw));

    // --- gefülltes Dreieck updaten
    const pos = meshGeom.attributes.position.array;
    pos[0] = p1[0]; pos[1] = p1[1]; pos[2] = p1[2];
    pos[3] = p2[0]; pos[4] = p2[1]; pos[5] = p2[2];
    pos[6] = p3[0]; pos[7] = p3[1]; pos[8] = p3[2];
    meshGeom.attributes.position.needsUpdate = true;
    meshGeom.computeVertexNormals();

    // --- Kontur updaten: [p1,p2, p2,p3, p3,p1]
    const epos = edgeGeom.attributes.position.array;
    const pts = [p1, p2,  p2, p3,  p3, p1];
    let i = 0;
    for (const p of pts) {
      epos[i++] = p[0];
      epos[i++] = p[1];
      epos[i++] = p[2];
    }
    edgeGeom.attributes.position.needsUpdate = true;
  }
}
