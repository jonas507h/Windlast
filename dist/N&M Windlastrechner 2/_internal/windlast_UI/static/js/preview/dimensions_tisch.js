// dimensions_tisch.js — erzeugt Maß-Spezifikationen für ein Tisch (Breite/Höhe vorerst)

// kleine Vektorhilfen
const v={add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s], len:(a)=>Math.hypot(a[0],a[1],a[2]), norm:(a)=>{const L=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/L,a[1]/L,a[2]/L];}, cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]] };

function findEl(bauelemente, id){ return bauelemente.find(e=>e.element_id_intern===id); }
const fmtDE = (x) => x.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const eff_offset = 0.2; // Versatz der Maßlinie von der Konstruktion in m
let real_offset_a = eff_offset;
let real_offset_b = eff_offset;
let bp_offset = eff_offset;

export function computeDimensionsTisch(konstruktion){
  const specs=[];
  const B = konstruktion.breite_m;
  const H = konstruktion.hoehe_m;
  const T = konstruktion.tiefe_m;
  const H_F = konstruktion.hoehe_flaeche_m;
  const traverse_name_intern = konstruktion.traverse_name_intern;
  const bodenplatte_name_intern = konstruktion.bodenplatte_name_intern;
  const els = konstruktion.bauelemente||[];

  const travSpec = window?.Catalog?.getTraverse?.(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;
  const bpSpec = window?.Catalog?.getBodenplatte?.(bodenplatte_name_intern);
 
  let label_breite;
  let label_hoehe;
  let label_tiefe;
  let label_hoehe_flaeche;

  const breite_input = parseFloat(document.getElementById('breite_m')?.value);
  if (isFinite(breite_input) && breite_input > 0) {
    label_breite = `Breite: ${fmtDE(breite_input)} m`;
  } else {
    label_breite = `Breite`;
  }
  const hoehe_input  = parseFloat(document.getElementById('hoehe_m')?.value);
  if (isFinite(hoehe_input) && hoehe_input > 0) {
    label_hoehe = `Höhe: ${fmtDE(hoehe_input)} m`;
  } else {
    label_hoehe = `Höhe`;
  }
  const tiefe_input  = parseFloat(document.getElementById('tiefe_m')?.value);
  if (isFinite(tiefe_input) && tiefe_input > 0) {
    label_tiefe = `Tiefe: ${fmtDE(tiefe_input)} m`;
  } else {
    label_tiefe = `Tiefe`;
  }
  const hoehe_flaeche_input = parseFloat(document.getElementById('hoehe_flaeche_m')?.value);
  if (isFinite(hoehe_flaeche_input)) {
    label_hoehe_flaeche = `Höhe Fläche: ${fmtDE(hoehe_flaeche_input)} m`;
  } else {
    label_hoehe_flaeche = `Höhe Fläche`;
  }

  if (is3punkt) {
    real_offset_a = eff_offset + (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3);
    real_offset_b = eff_offset + (Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2);
  } else {
    real_offset_a = eff_offset + (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 2);
    real_offset_b = eff_offset + (Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2);
  }
  bp_offset = eff_offset + (Number(bpSpec.breite ?? bpSpec.tiefe ?? bpSpec.kantenlaenge) / 2);

  if (B != null && isFinite(B)) {
    // Breite entlang der oberen Traverse, Maßlinie leicht darüber (Z-up: +Z)
    const a = [0,0,H]; const b = [B,0,H];
    specs.push({
      kind:'linear', param_key:'breite_m', label: label_breite,
      anchors:{ a, b, dir:[0,0,1], offset: eff_offset, textSize:0.28 }
    });
  }

  if (H != null && isFinite(H)) {
    // Höhe entlang der linken Stütze, Maßlinie leicht links daneben
    const a = [0,0,0]; const b = [0,0,H];
    // Linke Stütze steht bei x≈0 → quer nach -X raus bemaßen
    specs.push({
      kind:'linear', param_key:'hoehe_m', label: label_hoehe,
      anchors:{ a, b, dir:[-1,0,0], offset: bp_offset, textSize:0.28 }
    });
  }

  if (T != null && isFinite(T)) {
    // Tiefe entlang der oberen linken Traverse, Maßlinie leicht links daneben
    const a = [0,0,H]; const b = [0,T,H];
    specs.push({
      kind:'linear', param_key:'tiefe_m', label: label_tiefe,
      anchors:{ a, b, dir:[0,0,1], offset: eff_offset, textSize:0.28 }
    });
  }

  if (H_F != null && isFinite(H_F)) {
    const a = [B,0,H]; const b = [B,0,H - H_F];
    specs.push({
      kind:'linear', param_key:'hoehe_flaeche_m', label: label_hoehe_flaeche,
      anchors:{ a, b, dir:[1,0,0], offset: real_offset_b, textSize:0.28 }
    });
  }

  return specs;
}







