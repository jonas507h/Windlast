// build_tor.js — UI-seitiger Builder für ein Traversen-Tor

// Vektor-Hilfen
const vec = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
};

export const ORIENTIERUNG = Object.freeze({ up: 'up', side: 'side', down: 'down' });

const ORIENT_MAP = {
  [ORIENTIERUNG.up]:   { links: [-1, 0,  0], oben: [0, 0,  1], rechts: [ 1, 0,  0], unten: [0, 0, -1] },
  [ORIENTIERUNG.side]: { links: [ 0, 1,  0], oben: [0, 1,  0], rechts: [ 0, 1,  0], unten: [0, 1,  0] },
  [ORIENTIERUNG.down]: { links: [ 1, 0,  0], oben: [0, 0, -1], rechts: [-1, 0,  0], unten: [0, 0,  1] },
};

/**
 * Validiert die UI-Inputs für ein Tor.
 * Wirft bei Fehlern eine aussagekräftige Exception.
 */
export function validateTorInputs({
  breite_m, hoehe_m, hoehe_flaeche_m: hoehe_flaeche_m, anzahl_steher,traverse_name_intern, bodenplatte_name_intern, untergrund, orientierung = ORIENTIERUNG.up,
}, catalog) {
  if (!catalog || typeof catalog.getTraverse !== 'function' || typeof catalog.getBodenplatte !== 'function') {
    throw new Error('catalog mit getTraverse/getBodenplatte erforderlich.');
  }

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  let H_F = hoehe_flaeche_m;
  const A_S = Number(anzahl_steher);

  if (!isFinite(A_S) || A_S < 2 || !Number.isInteger(A_S)) {
    throw new Error('anzahl_steher muss eine ganze Zahl ≥ 2 sein.');
  }

  if (H_F === "" || H_F === null || H_F === undefined) {
    H_F = null;
  } else {
    H_F = Number(H_F);
    if (!isFinite(H_F) || H_F <= 0) {
      throw new Error('hoehe_flaeche_m muss leer oder eine Zahl > 0 sein.');
    }
  }
  if (!isFinite(B) || !isFinite(H)) throw new Error('breite_m und hoehe_m müssen Zahlen sein.');
  if (B <= 0 || H <= 0) throw new Error('Breite und Höhe müssen > 0 sein.');
  if (H_F !== null && H_F > H) throw new Error('hoehe_flaeche_m darf nicht größer als hoehe_m sein.');
  if (!traverse_name_intern) throw new Error('traverse_name_intern fehlt.');
  if (!bodenplatte_name_intern) throw new Error('bodenplatte_name_intern fehlt.');
  if (!untergrund) throw new Error('untergrund fehlt.');
  if (!ORIENT_MAP[orientierung]) throw new Error(`Unbekannte orientierung: ${orientierung}`);

  const travSpec = catalog.getTraverse(traverse_name_intern);
  if (!travSpec) throw new Error(`Traverse ${traverse_name_intern} nicht im Katalog gefunden.`);

  // Orientierungsgerechte Höhe prüfen
  const t = (() => {
    switch (orientierung) {
      case ORIENTIERUNG.side:
        return Number(travSpec.B_hoehe ?? travSpec.A_hoehe ?? travSpec.hoehe);
      case ORIENTIERUNG.up:
      case ORIENTIERUNG.down:
      default:
        return Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe);
    }
  })();

  if (!isFinite(t) || t <= 0) {
    throw new Error(`Traverse im Katalog ohne gültige Höhe (A_hoehe/B_hoehe).`);
  }

  if (H <= t) {
    throw new Error(`hoehe_m (${H}) muss größer als Traversenhöhe (${t}) sein.`);
  }
}

/**
 * Baut die KONSTRUKTIONS-Datenstruktur für ein Tor.
 * NUR Datenaufbau – keine Three.js Meshes, keine Physik.
 *
 * @param {Object} inputs
 * @param {number} inputs.breite_m
 * @param {number} inputs.hoehe_m
 * @param {number|null} inputs.hoehe_flaeche_m
 * @param {number} inputs.anzahl_steher
 * @param {string} inputs.traverse_name_intern
 * @param {string} inputs.bodenplatte_name_intern
 * @param {boolean} [inputs.gummimatte=true]
 * @param {string} inputs.untergrund
 * @param {'up'|'side'|'down'} [inputs.orientierung='up']
 * @param {string} [inputs.name='Tor']
 * @param {Object} catalog – siehe oben
 * @returns {Object} konstruktion
 */
export function buildTor(inputs, catalog) {
  const {
    breite_m, hoehe_m, hoehe_flaeche_m, anzahl_steher, traverse_name_intern, bodenplatte_name_intern,
    gummimatte = true,
    untergrund,
    orientierung = ORIENTIERUNG.up,
    name = 'Tor',
  } = inputs;

  validateTorInputs({ breite_m, hoehe_m, hoehe_flaeche_m, anzahl_steher, traverse_name_intern, bodenplatte_name_intern, untergrund, orientierung }, catalog);

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  let H_F = null;
  if (hoehe_flaeche_m !== "" && hoehe_flaeche_m !== null && hoehe_flaeche_m !== undefined) {
    H_F = Number(hoehe_flaeche_m);
  }
  const A_S = Number(anzahl_steher);
  const travSpec = catalog.getTraverse(traverse_name_intern);
  const is3punkt = Number(travSpec.anzahl_gurtrohre) === 3;

  // Orientierungsgerechte Traversenhöhe bestimmen
  let t_part;
  let flaeche_offset;
  switch (orientierung) {
    case ORIENTIERUNG.side:
      if (is3punkt) {
        t_part = Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2;
        flaeche_offset = -1 * Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3;
      } else {
        t_part = Number(travSpec.B_hoehe ?? travSpec.A_hoehe ?? travSpec.hoehe) / 2;
        flaeche_offset = -t_part;
      }
      break;
    case ORIENTIERUNG.up:
      if (is3punkt) {
        t_part = Number(travSpec.A_hoehe ?? travSpec.hoehe) * 2 / 3;
        flaeche_offset = -1 * Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2;
      } else {
        t_part = Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe) / 2;
        flaeche_offset = -t_part;
      }
      break;
    case ORIENTIERUNG.down:
      if (is3punkt) {
        t_part = Number(travSpec.A_hoehe ?? travSpec.hoehe) / 3;
        flaeche_offset = -1 * Number(travSpec.B_hoehe ?? travSpec.hoehe) / 2;
      } else {
        t_part = Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe) / 2;
        flaeche_offset = -t_part;
      }
      break;
    default:
      t_part = Number(travSpec.A_hoehe ?? travSpec.B_hoehe ?? travSpec.hoehe);
      flaeche_offset = -t_part;
      break;
  }

  // Fallback: Wenn nichts passt, Fehler werfen
  if (!isFinite(t_part) || t_part <= 0) {
    throw new Error(
      `Ungültige Traversenhöhe für ${traverse_name_intern} (Orientierung ${orientierung}).`
    );
  }
  const travAnzeige = travSpec.anzeige_name || traverse_name_intern;

  const plateSpec = catalog.getBodenplatte(bodenplatte_name_intern) || {};
  const plateAnzeige = plateSpec.anzeige_name || bodenplatte_name_intern;

  const vecs = ORIENT_MAP[orientierung];

  // --- obere Strecke ---
  const trav_top = {
    typ: 'Traversenstrecke',
    traverse_name_intern,
    start: [ 0, 0, H - t_part ],
    ende:  [ B, 0, H - t_part ],
    orientierung: vecs.oben,
    objekttyp: 'TRAVERSE',
    element_id_intern: 'Strecke_Oben',
    anzeigename: travAnzeige,
  };

  // -- Steher und Bodenplatten ---
  const x_abstand = (B - 2 * t_part) / (anzahl_steher - 1);

  // Mittelpunkt-Index
  const midIndex = Math.floor(anzahl_steher / 2);

  const traversen = [];
  const bodenplatten = [];

  for (let n = 0; n < anzahl_steher; n++) {
    const x = t_part + n * x_abstand;

    const sideVec = (n <= midIndex)
      ? vecs.links
      : vecs.rechts;

    traversen.push({
      typ: 'Traversenstrecke',
      traverse_name_intern,
      start: [x, 0, 0],
      ende:  [x, 0, H],
      orientierung: sideVec,
      objekttyp: 'TRAVERSE',
      element_id_intern: `Steher_${n + 1}`,
      anzeigename: travAnzeige,
    });

    bodenplatten.push({
      typ: 'Bodenplatte',
      name_intern: bodenplatte_name_intern,
      mittelpunkt: [x, 0, 0],
      orientierung: [0, 0, 1],
      drehung: sideVec,
      untergrund,
      gummimatte: gummimatte ? 'GUMMI' : null,
      objekttyp: 'BODENPLATTE',
      element_id_intern: `Bodenplatte_${n + 1}`,
      anzeigename: plateAnzeige,
    });
  }

  // Basis-Bauelemente
  const bauelemente = [trav_top, ...traversen, ...bodenplatten];

  // --- Wenn Unterkante definiert, dann Fläche und untere Truss ---
  if (H_F !== null) {
    const trav_bottom = {
      typ: 'Traversenstrecke',
      traverse_name_intern,
      start: [ 0, 0, H - H_F + t_part ],
      ende:  [ B, 0, H - H_F + t_part ],
      orientierung: vecs.unten,
      objekttyp: 'TRAVERSE',
      element_id_intern: 'Strecke_Unten',
      anzeigename: travAnzeige,
    };

    const flaeche = {
      typ: 'senkrechteFlaeche',
      eckpunkte: [
        [ 0, flaeche_offset, H - H_F ],
        [ 0, flaeche_offset, H ],
        [ B, flaeche_offset, H ],
        [ B, flaeche_offset, H - H_F ],
      ],
      objekttyp: 'SENKRECHTE_FLAECHE',
      element_id_intern: 'Flaeche',
      anzeigename: 'Fläche',
      flaechenlast: null,
      gesamtgewicht: null,
    }
    bauelemente.push(trav_bottom, flaeche);
  }

  // Gesamtobjekt (flach, gut serialisierbar)
  const konstruktion = {
    version: 1,
    typ: 'Tor',
    name,
    breite_m: B,
    hoehe_m: H,
    hoehe_flaeche_m: H_F,
    anzahl_steher: A_S,
    traverse_name_intern: traverse_name_intern,
    traversen_orientierung: orientierung,
    bodenplatte_name_intern: bodenplatte_name_intern,
    bauelemente: bauelemente,
  };

  return konstruktion;
}
