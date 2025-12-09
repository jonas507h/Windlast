// linien_senkrechteFlaeche.js — gefüllte, senkrechte Rechteckfläche in beliebiger Raumlage

const EPS = 1e-9;
function vAdd(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function vSub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function vMul(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
function vDot(a, b) { return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function vLen(a)    { return Math.sqrt(vDot(a, a)); }
function vNorm(a)   { const L = vLen(a); return L > EPS ? vMul(a, 1/L) : [0,0,0]; }
function vCross(a,b){ return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }

export function senkrechteFlaeche_linien(flaeche) {
  const pts = flaeche?.eckpunkte || [];
  if (!Array.isArray(pts) || pts.length < 3) {
    return { segments: [], polygon: [], frame: null, metadata: { typ: 'SENKRECHTE_FLAECHE' } };
  }

  // Wir erwarten ein 4-Eck in Umlaufrichtung, aber machen es halbwegs robust:
  const p0 = pts[0];
  const p1 = pts[1 % pts.length];
  const p3 = pts[pts.length - 1]; // gegenüber von p1 bei Rechteck

  const e1 = vSub(p1, p0);
  const e2 = vSub(p3, p0);

  let u = vNorm(e1);           // z.B. Höhe
  let n = vNorm(vCross(e1,e2)); // Normalenvektor auf der Fläche
  if (vLen(n) < EPS) {
    // Fallback: Falls Punkte degeneriert sind
    n = [0,1,0];
  }
  const v = vNorm(vCross(n, u)); // zweite Achse in der Ebene

  // Schwerpunkt der Fläche
  let C = [0,0,0];
  for (const p of pts) {
    C = vAdd(C, p);
  }
  C = vMul(C, 1 / pts.length);

  // Linien-Segmente (Umriss)
  const segments = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i];
    const b = pts[(i + 1) % pts.length];
    segments.push([a, b]);
  }

  const polygon = [...pts];

  return {
    segments,
    polygon,
    frame: { u, v, n, C },
    metadata: {
      typ: 'SENKRECHTE_FLAECHE',
      id: flaeche?.element_id_intern,
      anzeigename: flaeche?.anzeigename ?? 'senkrechte Fläche',
    },
  };
}
