// dimensions_tisch.js — erzeugt Maß-Spezifikationen für ein Tisch (Breite/Höhe vorerst)

// kleine Vektorhilfen
const v={add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s], len:(a)=>Math.hypot(a[0],a[1],a[2]), norm:(a)=>{const L=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/L,a[1]/L,a[2]/L];}, cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]] };

function findEl(bauelemente, id){ return bauelemente.find(e=>e.element_id_intern===id); }
const fmtDE = (x) => x.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const eff_offset = 0.2; // Versatz der Maßlinie von der Konstruktion in m
let real_offset_a = eff_offset;
let real_offset_b = eff_offset;

export function computeDimensionsTisch(konstruktion){
  const specs=[];
  const B = konstruktion.breite_m;
  const H = konstruktion.hoehe_m;
  const T = konstruktion.tiefe_m;
  const traverse_name_intern = konstruktion.traverse_name_intern;
  const els = konstruktion.bauelemente||[];


  const travSpec = window?.TorCatalog?.getTraverse?.(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;

  if (is3punkt) {
    real_offset_a = eff_offset + (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3);
    real_offset_b = eff_offset + (Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2);
  } else {
    real_offset_a = eff_offset + (Number(travSpec.A_hoehe ?? travSpec.hoehe) / 2);
    real_offset_b = eff_offset + (Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2);
  }

  const breite = findEl(els,'Strecke_Oben_Vorne');
  const hoehe = findEl(els,'Strecke_Vorne_Links');
  const tiefe = findEl(els,'Strecke_Oben_Links');

  if (breite && breite.start && breite.ende){
    // Breite entlang der oberen Traverse, Maßlinie leicht darüber (Z-up: +Z)
    const a = breite.start; const b = breite.ende;
    specs.push({
      kind:'linear', param_key:'breite_m', label: `Breite: ${fmtDE(B)} m`,
      anchors:{ a, b, dir:[0,0,1], offset: real_offset_a, textSize:0.28 }
    });
  }

  if (hoehe && hoehe.start && hoehe.ende){
    // Höhe entlang der linken Stütze, Maßlinie leicht links daneben
    const a = hoehe.start; const b = hoehe.ende;
    // Linke Stütze steht bei x≈0 → quer nach -X raus bemaßen
    specs.push({
      kind:'linear', param_key:'hoehe_m', label:`Höhe: ${fmtDE(H)} m`,
      anchors:{ a, b, dir:[-1,0,0], offset: real_offset_a, textSize:0.28 }
    });
  }

  if (tiefe && tiefe.start && tiefe.ende){
    // Tiefe entlang der oberen linken Traverse, Maßlinie leicht links daneben
    const a = tiefe.start; const b = tiefe.ende;
    specs.push({
      kind:'linear', param_key:'tiefe_m', label:`Tiefe: ${fmtDE(T)} m`,
      anchors:{ a, b, dir:[0,0,1], offset: real_offset_a, textSize:0.28 }
    });
  }

  return specs;
}







