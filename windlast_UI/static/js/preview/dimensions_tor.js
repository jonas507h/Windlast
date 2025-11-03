// dimensions_tor.js — erzeugt Maß-Spezifikationen für ein Tor (Breite/Höhe vorerst)

// kleine Vektorhilfen
const v={add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s], len:(a)=>Math.hypot(a[0],a[1],a[2]), norm:(a)=>{const L=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/L,a[1]/L,a[2]/L];}, cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]] };

function findEl(bauelemente, id){ return bauelemente.find(e=>e.element_id_intern===id); }

export function computeDimensionsTor(konstruktion){
  const specs=[];
  const B = konstruktion.breite_m;
  const H = konstruktion.hoehe_m;
  const els = konstruktion.bauelemente||[];

  const top = findEl(els,'Strecke_Oben');
  const left = findEl(els,'Strecke_Links');

  if (top && top.start && top.ende){
    // Breite entlang der oberen Traverse, Maßlinie leicht darüber (Z-up: +Z)
    const a = top.start; const b = top.ende;
    specs.push({
      kind:'linear', param_key:'breite_m', label: `${B.toFixed(2)} m`,
      anchors:{ a, b, dir:[0,0,1], offset: 0.35, textSize:0.28 }
    });
  }

  if (left && left.start && left.ende){
    // Höhe entlang der linken Stütze, Maßlinie leicht links daneben
    const a = left.start; const b = left.ende;
    // Linke Stütze steht bei x≈0 → quer nach -X raus bemaßen
    specs.push({
      kind:'linear', param_key:'hoehe_m', label:`${H.toFixed(2)} m`,
      anchors:{ a, b, dir:[-1,0,0], offset: 0.35, textSize:0.28 }
    });
  }

  return specs;
}
