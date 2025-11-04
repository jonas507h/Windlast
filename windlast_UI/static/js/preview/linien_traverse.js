// linien_traverse.js — 4-Gurt Rechteck + Endrahmen + A/B-Diagonalen (vektorbasiert)

const EPS = 1e-9;
function vAdd(a,b){ return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function vSub(a,b){ return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function vMul(a,s){ return [a[0]*s, a[1]*s, a[2]*s]; }
function vDot(a,b){ return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
function vLen(a){ return Math.sqrt(vDot(a,a)); }
function vNorm(a){ const L=vLen(a); return L>1e-9?vMul(a,1/L):[0,0,0]; }
function vCross(a,b){ return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }
function isNinety(rad){ return Math.abs(Math.cos(rad)) < 1e-6; }

function computePanelStations(L, run, gap){
  const stations = [];
  if (run < EPS){ // 90°: rein quer
    if ((gap ?? 0) > EPS){
      const n = Math.max(1, Math.floor(L / gap));
      const rest = L - n*gap;
      let s = rest/2;
      for (let i=0;i<n;i++,s+=gap) stations.push([s/L, s/L]);
    } else stations.push([0.5,0.5]); // eine mittige Querlinie
    return stations;
  }
  const step = Math.max(EPS, run + Math.max(0,gap||0));
  const n = Math.max(1, Math.floor(L / step));
  const rest = L - n*step;
  let s0 = rest/2;
  for (let i=0;i<n;i++){
    const a = (s0 + i*step) / L;
    const b = (s0 + i*step + run) / L;
    stations.push([a,b]);
  }
  return stations;
}

function shiftStations90(stations, offsetLen, L){
  if (!stations.length || Math.abs(offsetLen) < EPS) return stations;
  return stations.map(([t]) => {
    const s = Math.min(1, Math.max(0, t + offsetLen / L));
    return [s,s];
  });
}

// Liefert die beiden Knoten, die ein Face in der gewünschten Ebene (A oder B)
// und Vorzeichen (+1 / -1) definieren. Das trennt A- und B-Ebene eindeutig.
function getFaceNodes(n, which, Aaxis, Baxis, sign){
  // n: { up_sd, up_sn, dn_sd, dn_sn }
  if (which === 'A'){
    if (Aaxis === 'up'){
      // A entlang up, B ist side → Face B=+ oder B=-
      return sign > 0 ? [ n.up_sd, n.dn_sd ] : [ n.up_sn, n.dn_sn ];
    } else { // Aaxis === 'side'
      // A entlang side, B ist up
      return sign > 0 ? [ n.up_sd, n.up_sn ] : [ n.dn_sd, n.dn_sn ];
    }
  } else { // which === 'B'
    if (Baxis === 'up'){
      // B entlang up, A ist side → Face A=+ oder A=-
      return sign > 0 ? [ n.up_sd, n.dn_sd ] : [ n.up_sn, n.dn_sn ];
    } else { // Baxis === 'side'
      // B entlang side, A ist up
      return sign > 0 ? [ n.up_sd, n.up_sn ] : [ n.dn_sd, n.dn_sn ];
    }
  }
}

function traversenstrecke_linien_3punkt(strecke, basis, spec){
  const { tangent, up, side, L } = basis;

  // A/B-Achsen: Aaxis entlang 'orientierung' (näher zu 'up' oder 'side')
  const upBase = vNorm(strecke.orientierung ?? [0,0,1]);
  const dotUp = Math.abs(vDot(upBase, up));
  const Aaxis = (Math.abs(vDot(upBase, side)) > dotUp) ? 'side' : 'up';
  const Baxis = (Aaxis === 'up') ? 'side' : 'up';
  const ea = (Aaxis==='up') ? up : side;
  const eb = (Baxis==='up') ? up : side;

  // Geometrie aus Katalog: gleichschenklig (Schenkel=A_hoehe, Grundseite=B_hoehe)
  const alt   = Number(spec.A_hoehe ?? 0.3);       // ALTITUDE direkt aus CSV
  const B     = Number(spec.B_hoehe ?? 0.3);
  const halfB = B / 2;
  // Schwerpunkt im Ursprung: Apex bei +2/3*alt, Basis bei -1/3*alt
  const apexOff   = vMul(ea,  +2*alt/3);
  const baseCOff  = vMul(ea,  -1*alt/3);
  const baseLOff  = vAdd(baseCOff, vMul(eb, -halfB));
  const baseROff  = vAdd(baseCOff, vMul(eb, +halfB));

  const a = strecke.start ?? [0,0,0];
  const b = strecke.ende  ?? [0,0,0];
  const at = (t) => vAdd(a, vMul(tangent, t * L));

  const segs = [];

  // 3 Gurte (Apex, BaseL, BaseR)
  for (const off of [apexOff, baseLOff, baseROff]) {
    segs.push([ vAdd(a, off), vAdd(b, off) ]);
  }

  // Endrahmen (Dreiecksperimeter) wenn spec.end
  if (spec.end) {
    const ends = [a, b];
    for (const p of ends) {
      const P = (off)=>vAdd(p, off);
      segs.push( [P(apexOff), P(baseLOff)], [P(baseLOff), P(baseROff)], [P(baseROff), P(apexOff)] );
    }
  }

  // Knoten je Station
  const nodes = (p) => {
    return {
      apex:  vAdd(p, apexOff),
      baseL: vAdd(p, baseLOff),
      baseR: vAdd(p, baseROff),
    };
  };

  // --- A-Ebene: zwei Faces (apex↔baseL, apex↔baseR) ---
  (function drawA(){
    const ang = Number(spec.A_winkel ?? 45) * Math.PI/180;
    const gap = Number(spec.A_abstand ?? 0);
    const inv = !!spec.A_invert;
    // Effektiver A-Face-Abstand (apex↔base): Schenkelsehne
    const deltaA_face = Math.sqrt(alt*alt + halfB*halfB);
    const run = isNinety(ang) ? 0 : (deltaA_face / Math.tan(ang));
    const stations = computePanelStations(L, run, gap);

    if (isNinety(ang)){
      const n = stations.length || 1;
      const offsetLen = inv ? (gap > EPS ? gap/2 : (L/(n+1))/2) : 0;
      const Splus  = stations;
      const Sminus = shiftStations90(stations, offsetLen, L);

      // Face 1: apex↔baseL (B=+ analog)
      for (const [t] of Splus){
        const N = nodes(at(t));
        segs.push([ N.apex, N.baseL ]);
      }
      // Face 2: apex↔baseR (B=- analog) – ggf. phasenversetzt
      for (const [t] of Sminus){
        const N = nodes(at(t));
        segs.push([ N.apex, N.baseR ]);
      }
      return;
    }

    // ≠90°: alternierend + invert spiegelt zwischen den beiden Faces
    stations.forEach(([s0,s1], i) => {
      const P0 = nodes(at(s0)), P1 = nodes(at(s1));
      const altFlip = (i % 2) === 0;

      // Face 1 (apex↔baseL)
      segs.push( altFlip ? [ P0.apex,  P1.baseL ] : [ P0.baseL, P1.apex ] );
      // Face 2 (apex↔baseR) – invert kehrt die Richtung um
      const flip2 = inv ? !altFlip : altFlip;
      segs.push( flip2 ? [ P0.apex,  P1.baseR ] : [ P0.baseR, P1.apex ] );
    });
  })();

  // --- B-Ebene: ein Face (baseL↔baseR) ---
  (function drawB(){
    const ang = Number(spec.B_winkel ?? 45) * Math.PI/180;
    const gap = Number(spec.B_abstand ?? 0);
    const inv = !!spec.B_invert;

    // Abstand der Gurte in B-Ebene = Grundseite 'B'
    const run = isNinety(ang) ? 0 : (B / Math.tan(ang));
    const stations = computePanelStations(L, run, gap);

    if (isNinety(ang)){
      const n = stations.length || 1;
      const offsetLen = inv ? (gap > EPS ? gap/2 : (L/(n+1))/2) : 0;
      const Splus  = stations;
      const Sminus = shiftStations90(stations, offsetLen, L);

      // Ein Face: baseL↔baseR – wir zeichnen beide Sets, um invert sichtbar zu machen
      for (const [t] of Splus){
        const N = nodes(at(t));
        segs.push([ N.baseL, N.baseR ]);
      }
      for (const [t] of Sminus){
        const N = nodes(at(t));
        segs.push([ N.baseL, N.baseR ]);
      }
      return;
    }

    // ≠90°: Alternierung; invert spiegelt Richtung pro Panel
    stations.forEach(([s0,s1], i) => {
      const P0 = nodes(at(s0)), P1 = nodes(at(s1));
      const flip = ((i % 2) !== 0);
      const dir = inv ? !flip : flip;
      segs.push( dir ? [ P0.baseL, P1.baseR ] : [ P0.baseR, P1.baseL ] );
    });
  })();

  return {
    segments: segs,
    metadata: { typ:'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename },
  };
}

export function traversenstrecke_linien_4punkt(strecke){
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

  // --- Diagonalen pro Ebene: A -------------------------------------------
  (function drawA(){
    const ang = Number(spec.A_winkel ?? 45) * Math.PI/180;
    const gap = Number(spec.A_abstand ?? 0);
    const inv = !!spec.A_invert;

    // Gurtabstand in der A-Ebene
    const deltaA = 2 * ((Aaxis==='up') ? half_up : half_side);
    const tanA = Math.tan(ang);
    const run = isNinety(ang) ? 0 : (Math.abs(tanA) < EPS ? Infinity : (deltaA / tanA));

    // A-EBENE: 90°
    if (isNinety(ang)){
      const base = computePanelStations(L, 0, gap);      // [t,t]-Paare (rein quer)
      const n = base.length || 1;
      const offsetLen = inv ? (gap > EPS ? gap/2 : (L/(n+1))/2) : 0;

      const plusStations  = base;                         // Face @ B=+
      const minusStations = shiftStations90(base, offsetLen, L); // Face @ B=-

      // Face @ B = +
      for (const [t] of plusStations){
        const N = nodes(at(t));
        const [P, Q] = getFaceNodes(N, 'A', Aaxis, Baxis, +1); // A-Ebene, B=+ Face
        segs.push([P, Q]);  // reine Querlinie im A-Face
      }
      // Face @ B = -
      for (const [t] of minusStations){
        const N = nodes(at(t));
        const [P, Q] = getFaceNodes(N, 'A', Aaxis, Baxis, -1); // A-Ebene, B=- Face
        segs.push([P, Q]);
      }
      return;
    }

    // allgemeiner Fall (≠90°): wie gehabt, aber invert zwischen den Faces
    const stations = computePanelStations(L, isFinite(run) ? run : L+1, gap);
    stations.forEach(([s0, s1], i) => {
      const N0 = nodes(at(s0)), N1 = nodes(at(s1));
      const alt = (i % 2) === 0;

      // B = + Face der A-Ebene
      {
        const [P0, Q0] = getFaceNodes(N0, 'A', Aaxis, Baxis, +1);
        const [P1, Q1] = getFaceNodes(N1, 'A', Aaxis, Baxis, +1);
        const flipPlus = /* dein alt/fold wie gehabt */ alt;
        segs.push(flipPlus ? [P0, Q1] : [Q0, P1]);
      }
      // B = - Face der A-Ebene (invert spiegelt hier zwischen den Faces)
      {
        const [P0, Q0] = getFaceNodes(N0, 'A', Aaxis, Baxis, -1);
        const [P1, Q1] = getFaceNodes(N1, 'A', Aaxis, Baxis, -1);
        const flipMinus = inv ? !alt : alt;
        segs.push(flipMinus ? [P0, Q1] : [Q0, P1]);
      }
    });
  })();

  // --- Diagonalen pro Ebene: B -------------------------------------------
  (function drawB(){
    const ang = Number(spec.B_winkel ?? 45) * Math.PI/180;
    const gap = Number(spec.B_abstand ?? 0);
    const inv = !!spec.B_invert;

    const deltaB = 2 * ((Baxis==='up') ? half_up : half_side);
    const tanB = Math.tan(ang);
    const run = isNinety(ang) ? 0 : (Math.abs(tanB) < EPS ? Infinity : (deltaB / tanB));

    // B-EBENE: 90°
    if (isNinety(ang)){
      const base = computePanelStations(L, 0, gap);
      const n = base.length || 1;
      const offsetLen = inv ? (gap > EPS ? gap/2 : (L/(n+1))/2) : 0;

      const plusStations  = base;                         // Face @ A=+
      const minusStations = shiftStations90(base, offsetLen, L); // Face @ A=-

      // Face @ A = +
      for (const [t] of plusStations){
        const N = nodes(at(t));
        const [P, Q] = getFaceNodes(N, 'B', Aaxis, Baxis, +1); // B-Ebene, A=+ Face
        segs.push([P, Q]);
      }
      // Face @ A = -
      for (const [t] of minusStations){
        const N = nodes(at(t));
        const [P, Q] = getFaceNodes(N, 'B', Aaxis, Baxis, -1); // B-Ebene, A=- Face
        segs.push([P, Q]);
      }
      return;
    }

    const stations = computePanelStations(L, isFinite(run) ? run : L+1, gap);
    stations.forEach(([s0, s1], i) => {
      const N0 = nodes(at(s0)), N1 = nodes(at(s1));
      const alt = (i % 2) === 0;

      // A = + Face der B-Ebene
      {
        const [P0, Q0] = getFaceNodes(N0, 'B', Aaxis, Baxis, +1);
        const [P1, Q1] = getFaceNodes(N1, 'B', Aaxis, Baxis, +1);
        const flipPlus = alt;
        segs.push(flipPlus ? [P0, Q1] : [Q0, P1]);
      }
      // A = - Face der B-Ebene (invert spiegelt hier)
      {
        const [P0, Q0] = getFaceNodes(N0, 'B', Aaxis, Baxis, -1);
        const [P1, Q1] = getFaceNodes(N1, 'B', Aaxis, Baxis, -1);
        const flipMinus = inv ? !alt : alt;
        segs.push(flipMinus ? [P0, Q1] : [Q0, P1]);
      }
    });
  })();

  return {
    segments: segs,
    metadata: { typ:'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename },
  };
}

export function traversenstrecke_linien(strecke){
  const a0 = strecke.start ?? [0,0,0];
  const b0 = strecke.ende  ?? [0,0,0];

  // lokales KS robust
  const tangent = vNorm(vSub(b0,a0));
  let upBase = vNorm(strecke.orientierung ?? [0,0,1]);
  let side = vCross(tangent, upBase);
  if (vLen(side) < 1e-6) { upBase = Math.abs(tangent[2]) < 0.9 ? [0,0,1] : [1,0,0]; side = vCross(tangent, upBase); }
  side = vNorm(side);
  const up = vNorm(vCross(side, tangent));
  const L = vLen(vSub(b0,a0));
  const basis = { tangent, up, side, L };

  const spec = window?.TorCatalog?.getTraverse?.(strecke.traverse_name_intern);
  if (!spec) {
    console.warn("Traverse nicht im Katalog:", strecke.traverse_name_intern);
    return { segments: [], metadata: { typ:'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename } };
  }

  if (Number(spec.anzahl_gurtrohre) === 3) {
    return traversenstrecke_linien_3punkt(strecke, basis, spec);
  }

  // Fallback auf deine vorhandene 4-Punkt-Implementierung:
  return traversenstrecke_linien_4punkt(strecke, basis, spec); // <- benenne deine existierende Logik so um
}