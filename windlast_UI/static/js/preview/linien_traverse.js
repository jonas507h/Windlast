// linien_traverse.js — 4-Gurt Rechteck + Endrahmen + A/B-Diagonalen (vektorbasiert)

function vAdd(a,b){ return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function vSub(a,b){ return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function vMul(a,s){ return [a[0]*s, a[1]*s, a[2]*s]; }
function vDot(a,b){ return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
function vLen(a){ return Math.sqrt(vDot(a,a)); }
function vNorm(a){ const L=vLen(a); return L>1e-9?vMul(a,1/L):[0,0,0]; }
function vCross(a,b){ return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }

function computePanelStations(L, run, gap) {
  // L: Streckenlänge, run: Längsanteil pro Diagonale (delta/tan(ang)), gap: Abstand zwischen Diagonalen
  const EPS = 1e-9;
  const stations = [];

  // 90° → run ≈ 0: Diagonal verläuft quer; wir setzen s0==s1 (gleicher Längs-Parameter)
  if (run < EPS) {
    if (gap > EPS) {
      const n = Math.max(1, Math.floor(L / gap));
      const rest = L - n * gap;
      let s = rest / 2; // mittig starten
      for (let i = 0; i < n; i++) {
        const t = (s) / L;
        stations.push([t, t]); // s0==s1 => rein quer
        s += gap;
      }
    } else {
      // Kein Abstand angegeben: genau eine Querdiagonale in der Mitte
      const t = 0.5;
      stations.push([t, t]);
    }
    return stations;
  }

  // allgemeiner Fall: Schrittweite = run + gap
  const step = Math.max(EPS, run + Math.max(0, gap));
  const n = Math.max(1, Math.floor(L / step));
  const rest = L - n * step;
  let s0 = rest / 2;

  for (let i = 0; i < n; i++) {
    const s_start = (s0 + i * step) / L;
    const s_end   = (s0 + i * step + run) / L;
    stations.push([s_start, s_end]);
  }
  return stations;
}

export function traversenstrecke_linien(strecke){
  const a0 = strecke.start ?? [0,0,0];
  const b0 = strecke.ende  ?? [0,0,0];

  // --- Lokales Koordinatensystem (beliebige Raumlage robust) -------------
  const tangent = vNorm(vSub(b0,a0));                    // Längsrichtung
  let upBase = vNorm(strecke.orientierung ?? [0,0,1]);   // aus build_tor übergeben
  let side = vCross(tangent, upBase);
  if (vLen(side) < 1e-6) {                               // (fast) parallel → Fallback
    upBase = Math.abs(tangent[2]) < 0.9 ? [0,0,1] : [1,0,0];
    side = vCross(tangent, upBase);
  }
  side = vNorm(side);
  const up = vNorm(vCross(side, tangent));

  // --- Katalogdaten holen -------------------------------------------------
  const spec = window?.TorCatalog?.getTraverse?.(strecke.traverse_name_intern);
  if (!spec) {
    console.warn("Traverse nicht im Katalog:", strecke.traverse_name_intern);
    return { segments: [], metadata: { typ:'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename } };
  }

  // A-Achse = die Achse (up|side), die der gegebenen "orientierung" (upBase) am nächsten liegt
  const dotUp  = Math.abs(vDot(upBase, up));
  const dotSid = Math.abs(vDot(upBase, side));
  const Aaxis = (dotSid > dotUp) ? 'side' : 'up';
  const Baxis = (Aaxis === 'up') ? 'side' : 'up';

  // Querschnittshalben in lok. up/side — aus A_hoehe / B_hoehe gemäß Achszuordnung
  const halfA = Number(spec.A_hoehe ?? 0.30) / 2;
  const halfB = Number(spec.B_hoehe ?? 0.30) / 2;
  const half_up   = (Aaxis === 'up')   ? halfA : halfB;
  const half_side = (Aaxis === 'side') ? halfA : halfB;

  const du = vMul(up,   half_up);
  const ds = vMul(side, half_side);

  // Hilfen
  const a = a0, b = b0, L = vLen(vSub(b,a));
  const at = (t) => vAdd(a, vMul(tangent, t * L));
  const nodes = (p) => {
    const upP=du, dnP=vMul(du,-1), sdP=ds, snP=vMul(ds,-1);
    return {
      up_sd: vAdd(p,vAdd(upP,sdP)),  // +up +side
      up_sn: vAdd(p,vAdd(upP,snP)),  // +up -side
      dn_sd: vAdd(p,vAdd(dnP,sdP)),  // -up +side
      dn_sn: vAdd(p,vAdd(dnP,snP)),  // -up -side
    };
  };

  const segs = [];

  // --- 4 Gurte ------------------------------------------------------------
  const offs = [ vAdd(du,ds), vAdd(du,vMul(ds,-1)), vAdd(vMul(du,-1),ds), vAdd(vMul(du,-1),vMul(ds,-1)) ];
  for (const off of offs) segs.push([ vAdd(a,off), vAdd(b,off) ]);

  // --- Endrahmen (global) -------------------------------------------------
  if (spec.end) {
    for (const p of [a,b]) {
      const n = nodes(p);
      // Rechteck im Querschnitt: beide Richtungen
      segs.push([ n.up_sd, n.up_sn ], [ n.up_sn, n.dn_sn ], [ n.dn_sn, n.dn_sd ], [ n.dn_sd, n.up_sd ]);
    }
  }

  // --- Helper: Face-Knoten je Ebene --------------------------------------
  // A-Face: Ebene (tangent + Aaxis), an Baxis = ±
  function faceNodesA(n, signB){ // signB: +1 oder -1
    if (Baxis === 'side') {
      return signB>0 ? [ n.up_sd, n.dn_sd ] : [ n.up_sn, n.dn_sn ]; // A variiert entlang up
    } else { // Baxis === 'up'
      return signB>0 ? [ n.up_sd, n.up_sn ] : [ n.dn_sd, n.dn_sn ]; // A variiert entlang side
    }
  }
  // B-Face: Ebene (tangent + Baxis), an Aaxis = ±
  function faceNodesB(n, signA){
    if (Aaxis === 'side') {
      return signA>0 ? [ n.up_sd, n.dn_sd ] : [ n.up_sn, n.dn_sn ]; // B variiert entlang up
    } else { // Aaxis === 'up'
      return signA>0 ? [ n.up_sd, n.up_sn ] : [ n.dn_sd, n.dn_sn ]; // B variiert entlang side
    }
  }

  // --- Diagonalen pro Ebene: A -------------------------------------------
  (function drawA(){
    const ang = Number(spec.A_winkel ?? 45) * Math.PI/180;
    const gap = Number(spec.A_abstand ?? 0);
    const inv = !!spec.A_invert;

    const deltaA = 2 * ((Aaxis==='up') ? half_up : half_side);   // Gurtabstand in A-Ebene
    const tanA = Math.tan(ang);
    const run = (Math.abs(tanA) < 1e-9) ? Infinity : (deltaA / tanA); // 0° → tan≈0 => kein sinnvoller Schnitt → Infinity

    const stations = computePanelStations(L, isFinite(run) ? run : L+1, gap);
    // isFinite(run)?run: L+1 sorgt bei 0° dafür, dass genau eine sehr lange Diagonale berechnet würde (praktisch unterbunden durch Endpunkte)

    stations.forEach(([s0, s1], i) => {
      const N0 = nodes(at(s0)), N1 = nodes(at(s1));
      const even = (i % 2) === 0;
      const flip = inv ? !even : even;

      // Zwei Faces: B = + und B = -
      // Face-Knoten wie zuvor definiert
      const [Apos_p, Aneg_p] = faceNodesA(N0, +1);
      const [Apos_q, Aneg_q] = faceNodesA(N1, +1);
      const [Apos_p2, Aneg_p2] = faceNodesA(N0, -1);
      const [Apos_q2, Aneg_q2] = faceNodesA(N1, -1);

      // A-Face @ B=+:
      segs.push(flip ? [Apos_p, Aneg_q] : [Aneg_p, Apos_q]);
      // A-Face @ B=-:
      segs.push(flip ? [Apos_p2, Aneg_q2] : [Aneg_p2, Apos_q2]);
    });
  })();

  // --- Diagonalen pro Ebene: B -------------------------------------------
  (function drawB(){
    const ang = Number(spec.B_winkel ?? 45) * Math.PI/180;
    const gap = Number(spec.B_abstand ?? 0);
    const inv = !!spec.B_invert;

    const deltaB = 2 * ((Baxis==='up') ? half_up : half_side);   // Gurtabstand in B-Ebene
    const tanB = Math.tan(ang);
    const run = (Math.abs(tanB) < 1e-9) ? Infinity : (deltaB / tanB);

    const stations = computePanelStations(L, isFinite(run) ? run : L+1, gap);

    stations.forEach(([s0, s1], i) => {
      const N0 = nodes(at(s0)), N1 = nodes(at(s1));
      const even = (i % 2) === 0;
      const flip = inv ? !even : even;

      // Zwei Faces: A = + und A = -
      const [Bpos_p, Bneg_p] = faceNodesB(N0, +1);
      const [Bpos_q, Bneg_q] = faceNodesB(N1, +1);
      const [Bpos_p2, Bneg_p2] = faceNodesB(N0, -1);
      const [Bpos_q2, Bneg_q2] = faceNodesB(N1, -1);

      // B-Face @ A=+:
      segs.push(flip ? [Bpos_p, Bneg_q] : [Bneg_p, Bpos_q]);
      // B-Face @ A=-:
      segs.push(flip ? [Bpos_p2, Bneg_q2] : [Bneg_p2, Bpos_q2]);
    });
  })();

  return {
    segments: segs,
    metadata: { typ:'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename },
  };
}
