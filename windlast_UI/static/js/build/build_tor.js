// build_tor.js — UI-seitiger Builder für ein Traversen-Tor

// Vektor-Hilfen
const vec = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
};

export const ORIENTIERUNG = Object.freeze({ up: 'up', side: 'side', down: 'down' });

const ORIENT_MAP = {
  [ORIENTIERUNG.up]:   { links: [-1, 0,  0], oben: [0, 0,  1], rechts: [ 1, 0,  0] },
  [ORIENTIERUNG.side]: { links: [ 0, 1,  0], oben: [0, 1,  0], rechts: [ 0, 1,  0] },
  [ORIENTIERUNG.down]: { links: [ 1, 0,  0], oben: [0, 0, -1], rechts: [-1, 0,  0] },
};

// Platzhalter-Katalog, bis wir den echten aus der API ziehen
export const placeholderCatalog = {
  getTraverse: (nameIntern) => ({ hoehe: 0.3, anzeige_name: nameIntern }),
  getBodenplatte: (nameIntern) => ({ kantenlaenge: 1.0, anzeige_name: nameIntern }),
};

/**
 * Validiert die UI-Inputs für ein Tor.
 * Wirft bei Fehlern eine aussagekräftige Exception.
 */
export function validateTorInputs({
  breite_m, hoehe_m, traverse_name_intern, bodenplatte_name_intern, orientierung = ORIENTIERUNG.up,
}, catalog) {
  if (!catalog || typeof catalog.getTraverse !== 'function' || typeof catalog.getBodenplatte !== 'function') {
    throw new Error('catalog mit getTraverse/getBodenplatte erforderlich.');
  }
  const B = Number(breite_m);
  const H = Number(hoehe_m);
  if (!isFinite(B) || !isFinite(H)) throw new Error('breite_m und hoehe_m müssen Zahlen sein.');
  if (B <= 0 || H <= 0) throw new Error('Breite und Höhe müssen > 0 sein.');
  if (!traverse_name_intern) throw new Error('traverse_name_intern fehlt.');
  if (!bodenplatte_name_intern) throw new Error('bodenplatte_name_intern fehlt.');
  if (!ORIENT_MAP[orientierung]) throw new Error(`Unbekannte orientierung: ${orientierung}`);

  const travSpec = catalog.getTraverse(traverse_name_intern);
  if (!travSpec || !isFinite(travSpec.hoehe)) throw new Error('Traverse im Katalog ohne gültige "hoehe".');
  if (H <= travSpec.hoehe) throw new Error('hoehe_m muss größer als Traversenhöhe sein.');
}

/**
 * Baut die KONSTRUKTIONS-Datenstruktur für ein Tor.
 * NUR Datenaufbau – keine Three.js Meshes, keine Physik.
 *
 * @param {Object} inputs
 * @param {number} inputs.breite_m
 * @param {number} inputs.hoehe_m
 * @param {string} inputs.traverse_name_intern
 * @param {string} inputs.bodenplatte_name_intern
 * @param {boolean} [inputs.gummimatte=true]
 * @param {'up'|'side'|'down'} [inputs.orientierung='up']
 * @param {string} [inputs.name='Tor']
 * @param {Object} catalog – siehe oben
 * @returns {Object} konstruktion
 */
export function buildTor(inputs, catalog = placeholderCatalog) {
  const {
    breite_m, hoehe_m, traverse_name_intern, bodenplatte_name_intern,
    gummimatte = true,
    orientierung = ORIENTIERUNG.up,
    name = 'Tor',
  } = inputs;

  validateTorInputs({ breite_m, hoehe_m, traverse_name_intern, bodenplatte_name_intern, orientierung }, catalog);

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  const travSpec = catalog.getTraverse(traverse_name_intern);
  const t = Number(travSpec.hoehe); // Traversenhöhe (Profilmaß)
  const travAnzeige = travSpec.anzeige_name || traverse_name_intern;

  const plateSpec = catalog.getBodenplatte(bodenplatte_name_intern) || {};
  const plateAnzeige = plateSpec.anzeige_name || bodenplatte_name_intern;

  const vecs = ORIENT_MAP[orientierung];

  // --- Traversenstrecken (links/oben/rechts) – identisch zu CORE-Logik ---
  const trav_left = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ t / 2, 0, 0 ],
    ende:  [ t / 2, 0, H ],
    orientierung: vecs.links,
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Links',
    anzeigename: travAnzeige,
  };

  const trav_top = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ 0, 0, H - t / 2 ],
    ende:  [ B, 0, H - t / 2 ],
    orientierung: vecs.oben,
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Oben',
    anzeigename: travAnzeige,
  };

  const trav_right = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ B - t / 2, 0, 0 ],
    ende:  [ B - t / 2, 0, H ],
    orientierung: vecs.rechts,
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Rechts',
    anzeigename: travAnzeige,
  };

  // --- Bodenplatten (links/rechts) – Orientierung/Drehung wie im CORE ---
  const plate_left = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [0, 0, 0],
    orientierung: [0, 0, 1],
    drehung: vecs.links,
    form: 'RECHTECK',
    material: 'STAHL',
    untergrund: 'BETON',
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Links',
    anzeigename: plateAnzeige,
  };

  const plate_right = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [B, 0, 0],
    orientierung: [0, 0, 1],
    drehung: vecs.rechts,
    form: 'RECHTECK',
    material: 'STAHL',
    untergrund: 'BETON',
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Rechts',
    anzeigename: plateAnzeige,
  };

  // Gesamtobjekt (flach, gut serialisierbar)
  const konstruktion = {
    version: 1,
    typ: 'Tor',
    name,
    breite_m: B,
    hoehe_m: H,
    traversen_orientierung: orientierung,
    bauelemente: [ trav_left, trav_top, trav_right, plate_left, plate_right ],
  };

  return konstruktion;
}
