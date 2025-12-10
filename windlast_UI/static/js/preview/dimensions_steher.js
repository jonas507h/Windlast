// dimensions_steher.js — erzeugt Maß-Spezifikationen für ein Steher

// kleine Vektorhilfen
const v={add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s], len:(a)=>Math.hypot(a[0],a[1],a[2]), norm:(a)=>{const L=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/L,a[1]/L,a[2]/L];}, cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]] };

function findEl(bauelemente, id){ return bauelemente.find(e=>e.element_id_intern===id); }
const fmtDE = (x) => x.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const trav_eff_offset = 0.2; // Versatz der Maßlinie von der Konstruktion in m
let trav_real_offset = trav_eff_offset;
let rohr_eff_offset = 0.2;
let rohr_offset = rohr_eff_offset;
const rh_eff_offset = 0.2;
let rh_real_offset = rh_eff_offset;
let rohr_offset_to_front = 0.0;
let h_flaeche_eff_offset = 0.2;
let h_flaeche_real_offset = h_flaeche_eff_offset;

export function computeDimensionsSteher(konstruktion){
  const specs=[];
  const H = konstruktion.hoehe_m;
  const R_L = konstruktion.rohr_laenge_m;
  const R_H = konstruktion.rohr_hoehe_m;
  const H_F = konstruktion.hoehe_flaeche_m;
  const traverse_name_intern = konstruktion.traverse_name_intern;
  const rohr_name_intern = konstruktion.rohr_name_intern;
  const els = konstruktion.bauelemente||[];

  const travSpec = window?.Catalog?.getTraverse?.(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;

  let label_hoehe;
  let label_rohr_laenge;
  let label_rohr_hoehe;
  let label_hoehe_flaeche;

  const hoehe_input  = parseFloat(document.getElementById('hoehe_m')?.value);
  if (isFinite(hoehe_input) && hoehe_input > 0) {
    label_hoehe = `Höhe: ${fmtDE(hoehe_input)} m`;
  } else {
    label_hoehe = `Höhe`;
  }
  const rohr_laenge_input  = parseFloat(document.getElementById('rohr_laenge_m')?.value);
  if (isFinite(rohr_laenge_input) && rohr_laenge_input > 0) {
    label_rohr_laenge = `Länge Rohr: ${fmtDE(rohr_laenge_input)} m`;
  } else {
    label_rohr_laenge = `Länge Rohr`;
  }
  const rohr_hoehe_input  = parseFloat(document.getElementById('rohr_hoehe_m')?.value);
  if (isFinite(rohr_hoehe_input) && rohr_hoehe_input > 0) {
    label_rohr_hoehe = `Höhe Rohr: ${fmtDE(rohr_hoehe_input)} m`;
  } else {
    label_rohr_hoehe = `Höhe Rohr`;
  }
  const hoehe_flaeche_input = parseFloat(document.getElementById('hoehe_flaeche_m')?.value);
  if (isFinite(hoehe_flaeche_input)) {
    label_hoehe_flaeche = `Höhe Fläche: ${fmtDE(hoehe_flaeche_input)} m`;
  } else {
    label_hoehe_flaeche = `Höhe Fläche`;
  }

  trav_real_offset = trav_eff_offset * 2 + (Number(travSpec.B_hoehe ?? travSpec.A_hoehe ?? travSpec.hoehe) / 2) + (R_L / 2);
  rh_real_offset = rh_eff_offset + R_L / 2;
  rohr_offset = rohr_eff_offset + H - R_H;
  h_flaeche_real_offset = h_flaeche_eff_offset + R_L / 2;

  if (is3punkt) {
    rohr_offset_to_front = -1 * (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3);
  } else {
    rohr_offset_to_front = -1 * (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 2);
  }
  const trav = findEl(els,'Traverse_Steher');
  const rohr = findEl(els,'Rohr_Steher');

  if (trav && trav.start && trav.ende){
    const [a1,a2,a3] = trav.start;
    const [b1,b2,b3] = trav.ende;
    const a = [a1,a2 + rohr_offset_to_front ,a3];
    const b = [b1,b2 + rohr_offset_to_front ,b3];
    specs.push({
      kind:'linear', param_key:'breite_m', label: label_hoehe,
      anchors:{ a, b, dir:[1,0,0], offset: trav_real_offset, textSize:0.28 }
    });
  }

  if (rohr && rohr.start && rohr.ende){
    const a = rohr.start; const b = rohr.ende;
    // Linke Stütze steht bei x≈0 → quer nach -X raus bemaßen
    specs.push({
      kind:'linear', param_key:'hoehe_m', label: label_rohr_laenge,
      anchors:{ a, b, dir:[0,0,1], offset: rohr_offset, textSize:0.28 }
    });
  }

  if (trav && rohr){
    const a = [0,rohr_offset_to_front,0]; const b = [0,rohr_offset_to_front,R_H];

    specs.push({
      kind:'linear', param_key:'hoehe_m', label: label_rohr_hoehe,
      anchors:{ a, b, dir:[-1,0,0], offset: rh_real_offset, textSize:0.28 }
    });
  }

  if (H_F != null && isFinite(H_F)) {
    const a = [0,rohr_offset_to_front,R_H]; const b = [0,rohr_offset_to_front, R_H - H_F];
    specs.push({
      kind:'linear', param_key:'hoehe_flaeche_m', label: label_hoehe_flaeche,
      anchors:{ a, b, dir:[1,0,0], offset: h_flaeche_real_offset, textSize:0.28 }
    });
  }

  return specs;
}
