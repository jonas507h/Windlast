// linien_traverse.js — 4-Gurt-Traverse (V0: nur die vier Gurt-Linien, keine Stege/Diagonalen)

function vAdd(a,b){ return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function vSub(a,b){ return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function vMul(a,s){ return [a[0]*s, a[1]*s, a[2]*s]; }
function vDot(a,b){ return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function vLen(a){ return Math.sqrt(vDot(a,a)); }
function vNorm(a){ const L = vLen(a); return L>1e-9 ? vMul(a,1/L) : [0,0,0]; }
function vCross(a,b){
  return [ a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0] ];
}

export function traversenstrecke_linien(strecke) {
  const a = strecke.start ?? [0,0,0];
  const b = strecke.ende  ?? [0,0,0];

  // 1) lokale Basis
  const tangent = vNorm(vSub(b,a));
  // "oben"-Vektor kommt aus build_tor.js (Z-up-Kosmos beibehalten)
  let upBase = vNorm(strecke.orientierung ?? [0,0,1]);

  // Falls (fast) parallel → robustes Fallback
  let side = vCross(tangent, upBase);
  if (vLen(side) < 1e-6) {
    upBase = Math.abs(tangent[2]) < 0.9 ? [0,0,1] : [1,0,0];
    side = vCross(tangent, upBase);
  }
  side = vNorm(side);
  const up = vNorm(vCross(side, tangent)); // orthonormale Basis

  // 2) Gurtabstand (Quadrat 0.30m → Halbversatz 0.15m)
  const half = 0.15;
  const du = vMul(up,   half);
  const ds = vMul(side, half);

  // 4 Gurt-Offsets (±up ±side)
  const offsets = [
    vAdd(du, ds),  // +up +side
    vAdd(du, vMul(ds,-1)), // +up -side
    vAdd(vMul(du,-1), ds), // -up +side
    vAdd(vMul(du,-1), vMul(ds,-1)), // -up -side
  ];

  // 3) 4 Linien: start+offset → ende+offset
  const segments = offsets.map(off => [ vAdd(a,off), vAdd(b,off) ]);

  return {
    segments,
    metadata: { typ: 'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename },
  };
}