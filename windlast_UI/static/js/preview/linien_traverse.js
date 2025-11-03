// linien_traverse.js — 4 Gurte + End-Querstreben + 45°-Diagonalen

function vAdd(a,b){ return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function vSub(a,b){ return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function vMul(a,s){ return [a[0]*s, a[1]*s, a[2]*s]; }
function vDot(a,b){ return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function vLen(a){ return Math.sqrt(vDot(a,a)); }
function vNorm(a){ const L = vLen(a); return L>1e-9 ? vMul(a,1/L) : [0,0,0]; }
function vCross(a,b){ return [ a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0] ]; }

export function traversenstrecke_linien(strecke) {
  const a0 = strecke.start ?? [0,0,0];
  const b0 = strecke.ende  ?? [0,0,0];

  // --- lokale Basis ---
  const tangent = vNorm(vSub(b0,a0));
  let upBase = vNorm(strecke.orientierung ?? [0,0,1]);

  // robustes side/up-Orthonormalisieren
  let side = vCross(tangent, upBase);
  if (vLen(side) < 1e-6) {
    upBase = Math.abs(tangent[2]) < 0.9 ? [0,0,1] : [1,0,0];
    side = vCross(tangent, upBase);
  }
  side = vNorm(side);
  const up = vNorm(vCross(side, tangent));

  // --- Parameter ---
  const half = 0.15;                    // 0.30 m Gurtabstand → Halbversatz
  const du = vMul(up,   half);
  const ds = vMul(side, half);

  // Mittelachse (start/ende sind Centerline); hier keine Korrektur mehr nötig,
  // weil du die Platten bereits richtig gesetzt hast.
  const a = a0;
  const b = b0;

  // --- Gurtknoten-Funktion an Position t in [0..1] entlang der Strecke ---
  const at = (t) => vAdd(a, vMul(tangent, t * vLen(vSub(b,a))));
  const chordNodes = (p) => {
    // vier Knoten (±up, ±side) um Punkt p
    const upP = du, dnP = vMul(du,-1);
    const sdP = ds, snP = vMul(ds,-1);
    return {
      up_sd: vAdd(p, vAdd(upP, sdP)),   // +up +side
      up_sn: vAdd(p, vAdd(upP, snP)),   // +up -side
      dn_sd: vAdd(p, vAdd(dnP, sdP)),   // -up +side
      dn_sn: vAdd(p, vAdd(dnP, snP)),   // -up -side
    };
  };

  const segs = [];

  // --- 4 Gurtlinien ---
  const offs = [ vAdd(du,ds), vAdd(du,vMul(ds,-1)), vAdd(vMul(du,-1),ds), vAdd(vMul(du,-1),vMul(ds,-1)) ];
  for (const off of offs) segs.push([ vAdd(a,off), vAdd(b,off) ]);

  // --- End-Querstreben (Rechteck an beiden Enden, im Querschnitt) ---
  const ends = [a, b];
  for (const p of ends) {
    const n = chordNodes(p);
    // Verbindungen quer über side (bei +up und -up)
    segs.push([ n.up_sd, n.up_sn ], [ n.dn_sd, n.dn_sn ]);
    // Verbindungen quer über up (bei +side und -side)
    segs.push([ n.up_sd, n.dn_sd ], [ n.up_sn, n.dn_sn ]);
  }

  // --- 45°-Diagonalen auf beiden Faces ---
  // 45° relativ zur Längsachse heißt: Schrittweite entlang Tangente == Abstand zwischen den Gurten der jeweiligen Face.
  // up-Face (Abstand in up-Richtung = 2*half), side-Face (Abstand in side-Richtung = 2*half)
  const L = vLen(vSub(b,a));
  const panel = Math.max(0.05, 2 * half); // 0.30 m
  const nPanels = Math.max(1, Math.floor(L / panel));
  const rest = L - nPanels * panel;
  const startOffset = rest * 0.5; // Randabstand links/rechts gleich verteilen

  // Knoten entlang der Länge (0..nPanels), jeweils Start-/Ende-Knoten pro Panel
  for (let i = 0; i < nPanels; i++) {
    const s0 = (startOffset + i*panel) / L;
    const s1 = (startOffset + (i+1)*panel) / L;

    const P0 = at(s0);
    const P1 = at(s1);

    const N0 = chordNodes(P0);
    const N1 = chordNodes(P1);

    const even = (i % 2) === 0;

    // --- up-Face Diagonalen (je Seite +side und -side), 45°: oben ↔ unten ---
    // Seite +side
    if (even) segs.push([ N0.up_sd, N1.dn_sd ]); else segs.push([ N0.dn_sd, N1.up_sd ]);
    // Seite -side
    if (even) segs.push([ N0.up_sn, N1.dn_sn ]); else segs.push([ N0.dn_sn, N1.up_sn ]);

    // --- side-Face Diagonalen (je Oben +up und Unten -up), 45°: rechts ↔ links ---
    // Oben (+up)
    if (even) segs.push([ N0.up_sd, N1.up_sn ]); else segs.push([ N0.up_sn, N1.up_sd ]);
    // Unten (-up)
    if (even) segs.push([ N0.dn_sd, N1.dn_sn ]); else segs.push([ N0.dn_sn, N1.dn_sd ]);
  }

  return {
    segments: segs,
    metadata: { typ: 'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename },
  };
}
