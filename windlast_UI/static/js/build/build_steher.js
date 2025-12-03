// build_steher.js — UI-seitiger Builder für ein Traversen-Tor

// Vektor-Hilfen
const vec = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
};

/**
 * Validiert die UI-Inputs für ein Steher.
 * Wirft bei Fehlern eine aussagekräftige Exception.
 */
export function validateSteherInputs({
  hoehe_m, rohr_laenge_m, rohr_hoehe_m, unterkante_flaeche_m, traverse_name_intern, bodenplatte_name_intern, rohr_name_intern, untergrund,
}, catalog) {
  if (!catalog || typeof catalog.getTraverse !== 'function' || typeof catalog.getBodenplatte !== 'function' || typeof catalog.getRohr !== 'function') {
    throw new Error('catalog mit getTraverse/getBodenplatte/getRohr erforderlich.');
  }

  const H = Number(hoehe_m);
  const R_L = Number(rohr_laenge_m);
  const R_H = Number(rohr_hoehe_m);
  let U = unterkante_flaeche_m;

  if (U === "" || U === null || U === undefined) {
    U = null;
  } else {
    U = Number(U);
    if (!isFinite(U) || U < 0) {
      throw new Error('unterkante_flaeche_m muss leer oder eine Zahl ≥ 0 sein.');
    }
  }
  if (!isFinite(H) || !isFinite(R_L) || !isFinite(R_H)) throw new Error('hoehe_m, rohr_laenge_m und rohr_hoehe_m müssen Zahlen sein.');
  if (H <= 0 || R_L <= 0 || R_H <= 0) throw new Error('Hoehe, Rohrlänge und Rohrhöhe müssen > 0 sein.');
  if (!traverse_name_intern) throw new Error('traverse_name_intern fehlt.');
  if (!bodenplatte_name_intern) throw new Error('bodenplatte_name_intern fehlt.');
  if (!rohr_name_intern) throw new Error('rohr_name_intern fehlt.');
  if (!untergrund) throw new Error('untergrund fehlt.');

  const travSpec = catalog.getTraverse(traverse_name_intern);
  if (!travSpec) throw new Error(`Traverse ${traverse_name_intern} nicht im Katalog gefunden.`);
  const plateSpec = catalog.getBodenplatte(bodenplatte_name_intern);
  if (!plateSpec) throw new Error(`Bodenplatte ${bodenplatte_name_intern} nicht im Katalog gefunden.`);
  const rohrSpec = catalog.getRohr(rohr_name_intern);
  if (!rohrSpec) throw new Error(`Rohr ${rohr_name_intern} nicht im Katalog gefunden.`);

  const t = Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe);

  if (!isFinite(t) || t <= 0) {
    throw new Error(`Traverse im Katalog ohne gültige Höhe (A_hoehe/B_hoehe).`);
  }
}

/**
 * Baut die KONSTRUKTIONS-Datenstruktur für ein Tor.
 * NUR Datenaufbau – keine Three.js Meshes, keine Physik.
 *
 * @param {Object} inputs
 * @param {number} inputs.hoehe_m
 * @param {number} inputs.rohr_laenge_m
 * @param {number} inputs.rohr_hoehe_m
 * @param {number|null} inputs.unterkante_flaeche_m
 * @param {string} inputs.traverse_name_intern
 * @param {string} inputs.bodenplatte_name_intern
 * @param {boolean} [inputs.gummimatte=true]
 * @param {string} inputs.rohr_name_intern
 * @param {string} inputs.untergrund
 * @param {string} [inputs.name='Steher']
 * @param {Object} catalog – siehe oben
 * @returns {Object} konstruktion
 */
export function buildSteher(inputs, catalog) {
  const {
    hoehe_m, rohr_laenge_m, rohr_hoehe_m, unterkante_flaeche_m, traverse_name_intern, bodenplatte_name_intern, rohr_name_intern,
    gummimatte = true,
    untergrund,
    name = 'Steher',
  } = inputs;

  validateSteherInputs({hoehe_m, rohr_laenge_m, rohr_hoehe_m, unterkante_flaeche_m, traverse_name_intern, bodenplatte_name_intern, rohr_name_intern, untergrund }, catalog);
  const H = Number(hoehe_m);
  const R_L = Number(rohr_laenge_m);
  const R_H = Number(rohr_hoehe_m);
  let U = null;
  if (unterkante_flaeche_m !== "" && unterkante_flaeche_m !== null && unterkante_flaeche_m !== undefined) {
    U = Number(unterkante_flaeche_m);
  }
  const travSpec = catalog.getTraverse(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;

  let t_part;
  let flaeche_offset;
  if (is3punkt) {
        t_part = Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3;
        flaeche_offset = t_part;
      } else {
        t_part = Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe) / 2;
        flaeche_offset = t_part;
      }

  // Fallback: Wenn nichts passt, Fehler werfen
  if (!isFinite(t_part) || t_part <= 0) {
    throw new Error(
      `Ungültige Traversenhöhe für ${traverse_name_intern}.`
    );
  }
  const travAnzeige = travSpec.anzeige_name || traverse_name_intern;

  const plateSpec = catalog.getBodenplatte(bodenplatte_name_intern) || {};
  const plateAnzeige = plateSpec.anzeige_name || bodenplatte_name_intern;

  // --- Traversenstrecke ---
  const trav = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ 0, 0, 0 ],
    ende:  [ 0, 0, H ],
    orientierung: [0, 1, 0],
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Traverse_Steher',
    anzeigename: travAnzeige,
  };

  // --- Rohr ---
  const rohr = {
    typ: 'Rohr',
    rohr_name_intern,
    start: [ -R_L / 2, -t_part, R_H ],
    ende:  [ R_L / 2, -t_part, R_H ],
    objekttyp: 'ROHR',
    element_id_intern: 'Rohr_Steher',
    anzeigename: rohr_name_intern,
  };

  // --- Bodenplatte ---
  const plate = {
    typ: 'Bodenplatte',
    name_intern: bodenplatte_name_intern,
    mittelpunkt: [0, 0, 0],
    orientierung: [0, 0, 1],
    drehung: [0, 1, 0],
    untergrund: untergrund,
    gummimatte: gummimatte ? 'GUMMI' : null,
    objekttyp: 'BODENPLATTE',
    element_id_intern: 'Bodenplatte_Steher',
    anzeigename: plateAnzeige,
  };

  // Basis-Bauelemente
  const bauelemente = [ trav, rohr, plate ];

  // --- Wenn Unterkante definiert, dann Fläche und untere Pipe ---
  if (U !== null) {
    const rohr_bottom = {
    typ: 'Rohr',
    rohr_name_intern,
    start: [ -R_L / 2, -t_part, U ],
    ende:  [ R_L / 2, -t_part, U ],
    objekttyp: 'ROHR',
    element_id_intern: 'Rohr_unten',
    anzeigename: rohr_name_intern,
  };

    const flaeche = {
      typ: 'senkrechteFlaeche',
      eckpunkte: [
        [ -R_L / 2, flaeche_offset, U ],
        [ -R_L / 2, flaeche_offset, R_H ],
        [ R_L / 2, flaeche_offset, R_H ],
        [ R_L / 2, flaeche_offset, U ],
      ],
      objekttyp: 'SENKRECHTE_FLAECHE',
      element_id_intern: 'Flaeche',
      anzeigename: 'Fläche',
      flaechenlast: null,
      gesamtgewicht: null,
    }
    bauelemente.push(rohr_bottom, flaeche);
  }

  // Gesamtobjekt (flach, gut serialisierbar)
  const konstruktion = {
    version: 1,
    typ: 'Steher',
    name,
    hoehe_m: H,
    rohr_laenge_m: R_L,
    rohr_hoehe_m: R_H,
    unterkante_flaeche_m: U,
    traverse_name_intern: traverse_name_intern,
    bodenplatte_name_intern: bodenplatte_name_intern,
    rohr_name_intern: rohr_name_intern,
    bauelemente: bauelemente,
  };

  return konstruktion;
}
