// linien_bodenplatte.js — 3- und 4-Eck Bodenplatten in beliebiger Raumlage (voll 3D)

/**
 * Erwartete plate-Felder (analog build_tor):
 * - name_intern
 * - mittelpunkt: [x,y,z]
 * - orientierung: Normalenvektor (senkrecht auf Plattenfläche)
 * - drehung: Richtungsvektor in Plattenebene (Tiefe läuft parallel hierzu)
 * - anzeigename, element_id_intern
 *
 * Katalog (window.TorCatalog.getBodenplatte) sollte liefern:
 * - breite, tiefe (Meter)
 * - anzahl_ecken (3 | 4)
 * Fallback: plate.breite / plate.tiefe falls im Objekt vorhanden.
 */

// ---------- kleine Vektor-Utilities ----------
const EPS = 1e-9;
function vAdd(a,b){ return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function vSub(a,b){ return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function vMul(a,s){ return [a[0]*s, a[1]*s, a[2]*s]; }
function vDot(a,b){ return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
function vLen(a){ return Math.sqrt(vDot(a,a)); }
function vNorm(a){ const L=vLen(a); return L>EPS ? vMul(a,1/L) : [0,0,0]; }
function vCross(a,b){ return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }

/** robust: projiziere v in Ebene mit Normal n */
function projectToPlane(v, n){
  const nn = vNorm(n);
  return vSub(v, vMul(nn, vDot(v, nn)));
}

/** Hole Bodenplatten-Spezifikation aus globalem Katalog (wie bei Traversen) */
function getPlateSpec(name_intern, plate){
  const cat = window?.TorCatalog?.getBodenplatte?.(name_intern);
  return {
    breite: Number(cat?.breite ?? plate?.breite ?? 1.0),
    tiefe:  Number(cat?.tiefe  ?? plate?.tiefe  ?? 1.0),
    anzahl_ecken: Number(cat?.anzahl_ecken ?? 4)
  };
}

export function bodenplatte_linien(plate){
  // --- Katalog lesen ------------------------------------------------------
  const spec = getPlateSpec(plate?.name_intern, plate);
  const breite = Math.max(0, Number(spec.breite));
  const tiefe  = Math.max(0, Number(spec.tiefe));
  const nEcken = (spec.anzahl_ecken === 3) ? 3 : 4; // clamp auf 3|4

  // --- Zentrum & lokale Achsen -------------------------------------------
  const C = [
    plate?.mittelpunkt?.[0] ?? 0,
    plate?.mittelpunkt?.[1] ?? 0,
    plate?.mittelpunkt?.[2] ?? 0,
  ];

  // Normalenrichtung der Platte (senkrecht auf Fläche)
  let n = plate?.orientierung ?? [0,0,1];
  n = vNorm(n);
  if (vLen(n) < EPS) n = [0,0,1]; // Fallback

  // "Drehung" der Platte → Richtung der Tiefe (in der Ebene)
  let r = plate?.drehung ?? [1,0,0];
  // in Plattenebene projizieren
  r = projectToPlane(r, n);
  if (vLen(r) < EPS){
    // Fallback: wähle eine beliebige Richtung in der Ebene
    const helper = Math.abs(n[2]) < 0.9 ? [0,0,1] : [0,1,0];
    r = projectToPlane(helper, n);
  }
  const u = vNorm(r);               // u = Tiefe (parallel zur Drehung)
  const v = vNorm(vCross(n, u));    // v = Breite (senkrecht zur Drehung, in Ebene)

  // --- Punkte erzeugen ----------------------------------------------------
  const segments = [];

  if (nEcken === 4){
    // Rechteck: Breite entlang v, Tiefe entlang u; Mittelpunkt = C
    const hu = vMul(u, tiefe/2);
    const hv = vMul(v, breite/2);

    const p1 = vAdd(vSub(C, hu), vSub(C, vSub(C, hv)) ); // C - hu - hv → (C - hu) - hv
    // oben sauberer:
    const A = vSub(C, hu);          // Mitte - Tiefe/2
    const B = vAdd(C, hu);          // Mitte + Tiefe/2
    const pA = vSub(A, hv);
    const pB = vAdd(A, hv);
    const pC = vAdd(B, hv);
    const pD = vSub(B, hv);

    segments.push([pA, pB], [pB, pC], [pC, pD], [pD, pA]);
  } else {
    // Gleichschenkliges Dreieck:
    // - Breite = Grundseite (±breite/2 entlang v)
    // - Tiefe  = Höhe (entlang u)
    // - C ist Flächenschwerpunkt → Basiszentrum = C - tiefe/3 * u, Spitze = C + 2/3 * tiefe * u
    const baseCenter = vSub(C, vMul(u, tiefe/3));
    const apex       = vAdd(C, vMul(u, 2*tiefe/3));
    const halfB      = vMul(v, breite/2);

    const baseL = vSub(baseCenter, halfB);
    const baseR = vAdd(baseCenter, halfB);

    // Umfang
    segments.push(
      [baseL, baseR],
      [baseR, apex],
      [apex,  baseL],
    );
  }

  return {
    segments,
    metadata: {
      typ: 'BODENPLATTE',
      id: plate?.element_id_intern,
      anzeigename: plate?.anzeigename ?? plate?.name_intern ?? 'Bodenplatte'
    }
  };
}