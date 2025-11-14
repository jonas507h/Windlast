// dimensions_steher.js — erzeugt Maß-Spezifikationen für ein Steher

// kleine Vektorhilfen
const v={add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s], len:(a)=>Math.hypot(a[0],a[1],a[2]), norm:(a)=>{const L=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/L,a[1]/L,a[2]/L];}, cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]] };

function findEl(bauelemente, id){ return bauelemente.find(e=>e.element_id_intern===id); }
const fmtDE = (x) => x.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const trav_eff_offset = 0.2; // Versatz der Maßlinie von der Konstruktion in m
let trav_real_offset = trav_eff_offset;
const rohr_offset = 0.1;
const rh_eff_offset = 0.2;
let rh_real_offset = rh_eff_offset;
let rohr_offset_to_front = 0.0;

export function computeDimensionsSteher(konstruktion){
  const specs=[];
  const H = konstruktion.hoehe_m;
  const R_L = konstruktion.rohr_laenge_m;
  const R_H = konstruktion.rohr_hoehe_m;
  const traverse_name_intern = konstruktion.traverse_name_intern;
  const rohr_name_intern = konstruktion.rohr_name_intern;
  const els = konstruktion.bauelemente||[];

  const travSpec = window?.Catalog?.getTraverse?.(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;

  trav_real_offset = trav_eff_offset + (Number(travSpec.B_hoehe ?? travSpec.A_hoehe ?? travSpec.hoehe) / 2);
  rh_real_offset = rh_eff_offset + R_L / 2;

  if (is3punkt) {
    rohr_offset_to_front = -1 * (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3);
  } else {
    rohr_offset_to_front = -1 * (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 2);
  }
  const trav = findEl(els,'Traverse_Steher');
  const rohr = findEl(els,'Rohr_Steher');

  if (trav && trav.start && trav.ende){
    const a = trav.start; const b = trav.ende;
    specs.push({
      kind:'linear', param_key:'breite_m', label: `Höhe: ${fmtDE(H)} m`,
      anchors:{ a, b, dir:[1,0,0], offset: trav_real_offset, textSize:0.28 }
    });
  }

  if (rohr && rohr.start && rohr.ende){
    const a = rohr.start; const b = rohr.ende;
    // Linke Stütze steht bei x≈0 → quer nach -X raus bemaßen
    specs.push({
      kind:'linear', param_key:'hoehe_m', label:`Länge Rohr: ${fmtDE(R_L)} m`,
      anchors:{ a, b, dir:[0,0,1], offset: rohr_offset, textSize:0.28 }
    });
  }

  if (trav && rohr){
    const a = [0,rohr_offset_to_front,0]; const b = [0,rohr_offset_to_front,R_H];

    specs.push({
      kind:'linear', param_key:'hoehe_m', label:`Höhe Rohr: ${fmtDE(R_H)} m`,
      anchors:{ a, b, dir:[-1,0,0], offset: rh_real_offset, textSize:0.28 }
    });
  }
  return specs;
}
