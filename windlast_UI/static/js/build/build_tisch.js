// build_tor.js — UI-seitiger Builder für ein Traversen-Tor

// Vektor-Hilfen
const vec = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
};

/**
 * Validiert die UI-Inputs für ein Tisch.
 * Wirft bei Fehlern eine aussagekräftige Exception.
 */
export function validateTischInputs({
  breite_m, hoehe_m, tiefe_m, traverse_name_intern, bodenplatte_name_intern,
}, catalog) {
  if (!catalog || typeof catalog.getTraverse !== 'function' || typeof catalog.getBodenplatte !== 'function') {
    throw new Error('catalog mit getTraverse/getBodenplatte erforderlich.');
  }

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  const T = Number(tiefe_m);
  if (!isFinite(B) || !isFinite(H) || !isFinite(T)) throw new Error('breite_m, hoehe_m und tiefe_m müssen Zahlen sein.');
  if (B <= 0 || H <= 0 || T <= 0) throw new Error('Breite, Höhe und Tiefe müssen > 0 sein.');
  if (!traverse_name_intern) throw new Error('traverse_name_intern fehlt.');
  if (!bodenplatte_name_intern) throw new Error('bodenplatte_name_intern fehlt.');

  const travSpec = catalog.getTraverse(traverse_name_intern);
  if (!travSpec) throw new Error(`Traverse ${traverse_name_intern} nicht im Katalog gefunden.`);

  const t_a = travSpec.A_hoehe ?? travSpec.hoehe;
  if (!isFinite(t_a) || t_a <= 0) {
    throw new Error(`Traverse im Katalog ohne gültige Höhe (A_hoehe/B_hoehe).`);
  }
  const t_b = travSpec.B_hoehe ?? travSpec.hoehe;
  if (!isFinite(t_b) || t_b <= 0) {
    throw new Error(`Traverse im Katalog ohne gültige Höhe (A_hoehe/B_hoehe).`);
  }

  if (H <= t_a || H <= t_b) {
    throw new Error(`hoehe_m (${H}) muss größer als Traversenhöhe (${t_a}/${t_b}) sein.`);
  }
}

/**
 * Baut die KONSTRUKTIONS-Datenstruktur für ein Tisch.
 *
 * @param {Object} inputs
 * @param {number} inputs.breite_m
 * @param {number} inputs.hoehe_m
 * @param {number} inputs.tiefe_m
 * @param {string} inputs.traverse_name_intern
 * @param {string} inputs.bodenplatte_name_intern
 * @param {boolean} [inputs.gummimatte=true]
 * @param {string} [inputs.name='Tor']
 * @param {Object} catalog – siehe oben
 * @returns {Object} konstruktion
 */
export function buildTisch(inputs, catalog) {
  const {
    breite_m, hoehe_m, tiefe_m, traverse_name_intern, bodenplatte_name_intern,
    gummimatte = true,
    name = 'Tisch',
  } = inputs;

  validateTischInputs({ breite_m, hoehe_m, tiefe_m, traverse_name_intern, bodenplatte_name_intern }, catalog);

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  const T = Number(tiefe_m);
  const travSpec = catalog.getTraverse(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;

  // Orientierungsgerechte Traversenhöhe bestimmen
  let t_a;
  let t_b;
  if (is3punkt) {
    t_a = Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3;
    t_b = Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2;
  } else {
    t_a = Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe) / 2;
    t_b = Number(travSpec.B_hoehe ?? travSpec.A_hoehe ?? travSpec.hoehe) / 2;
  }

  // Fallback: Wenn nichts passt, Fehler werfen
  if (!isFinite(t_a) || t_a <= 0 || !isFinite(t_b) || t_b <= 0) {
    throw new Error(
      `Ungültige Traversenhöhe für ${traverse_name_intern}.`
    );
  }
  const travAnzeige = travSpec.anzeige_name || traverse_name_intern;

  const plateSpec = catalog.getBodenplatte(bodenplatte_name_intern) || {};
  const plateAnzeige = plateSpec.anzeige_name || bodenplatte_name_intern;

  // --- Traversenstrecken ---
  const trav_front_left = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ t_b, t_a, 0 ],
    ende:  [ t_b, t_a, H ],
    orientierung: [0, 1, 0],
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Vorne_Links',
    anzeigename: travAnzeige,
  };
  const trav_front_right = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ B - t_b, t_a, 0 ],
    ende:  [ B - t_b, t_a, H ],
    orientierung: [0, 1, 0],
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Vorne_Rechts',
    anzeigename: travAnzeige,
  };
  const trav_back_left = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ t_b, T - t_a, 0 ],
    ende:  [ t_b, T - t_a, H ],
    orientierung: [0, -1, 0],
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Hinten_Links',
    anzeigename: travAnzeige,
  };
  const trav_back_right = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ B - t_b, T - t_a, 0 ],
    ende:  [ B - t_b, T - t_a, H ],
    orientierung: [0, -1, 0],
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Hinten_Rechts',
    anzeigename: travAnzeige,
  };
  const trav_top_front = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ 0, t_b, H - t_a ],
    ende:  [ B, t_b, H - t_a ],
    orientierung: [0, 0, -1],
    objekttyp: 'TRAVERSE',  
    element_id_intern: 'Strecke_Oben_Vorne',
    anzeigename: travAnzeige,
  };
  const trav_top_back = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ 0, T - t_b, H - t_a ],
    ende:  [ B, T - t_b, H - t_a ],
    orientierung: [0, 0, -1],
    objekttyp: 'TRAVERSE',  
    element_id_intern: 'Strecke_Oben_Hinten',
    anzeigename: travAnzeige,
  };
  const trav_top_left = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ t_b, 0, H - t_a ],
    ende:  [ t_b, T, H - t_a ],
    orientierung: [0, 0, -1],
    objekttyp: 'TRAVERSE',  
    element_id_intern: 'Strecke_Oben_Links',
    anzeigename: travAnzeige,
  };
  const trav_top_right = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ B - t_b, 0, H - t_a ],
    ende:  [ B - t_b, T, H - t_a ],
    orientierung: [0, 0, -1],
    objekttyp: 'TRAVERSE',  
    element_id_intern: 'Strecke_Oben_Rechts',
    anzeigename: travAnzeige,
  };

  // --- Bodenplatten ---
  const plate_front_left = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [t_b, t_a, 0],
    orientierung: [0, 0, 1],
    drehung: [0, 1, 0],
    material: 'STAHL',
    untergrund: 'BETON',
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Vorne_Links',
    anzeigename: plateAnzeige,
  };
  const plate_front_right = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [B - t_b, t_a, 0],
    orientierung: [0, 0, 1],
    drehung: [0, 1, 0],
    material: 'STAHL',
    untergrund: 'BETON',
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Vorne_Rechts',
    anzeigename: plateAnzeige,
  };
  const plate_back_left = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [t_b, T - t_a, 0],
    orientierung: [0, 0, 1],
    drehung: [0, -1, 0],
    material: 'STAHL',
    untergrund: 'BETON',
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Hinten_Links',
    anzeigename: plateAnzeige,
  };
  const plate_back_right = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [B - t_b, T - t_a, 0],
    orientierung: [0, 0, 1],
    drehung: [0, -1, 0],
    material: 'STAHL',
    untergrund: 'BETON',
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Hinten_Rechts',
    anzeigename: plateAnzeige,
  };

  // Gesamtobjekt (flach, gut serialisierbar)
  const konstruktion = {
    version: 1,
    typ: 'Tisch',
    name,
    breite_m: B,
    hoehe_m: H,
    tiefe_m: T,
    traverse_name_intern: traverse_name_intern,
    bauelemente: [ trav_front_left, trav_front_right, trav_back_left, trav_back_right,
                   trav_top_front, trav_top_back, trav_top_left, trav_top_right,
                   plate_front_left, plate_front_right, plate_back_left, plate_back_right ],
  };

  return konstruktion;
}
