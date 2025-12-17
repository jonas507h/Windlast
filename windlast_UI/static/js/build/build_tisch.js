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
  breite_m, hoehe_m, tiefe_m, hoehe_flaeche_m, anzahl_steher_breite, anzahl_steher_tiefe, traverse_name_intern, bodenplatte_name_intern, untergrund,
}, catalog) {
  if (!catalog || typeof catalog.getTraverse !== 'function' || typeof catalog.getBodenplatte !== 'function') {
    throw new Error('catalog mit getTraverse/getBodenplatte erforderlich.');
  }

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  const T = Number(tiefe_m);
  let H_F = hoehe_flaeche_m;
  const A_SB = Number(anzahl_steher_breite);
  const A_ST = Number(anzahl_steher_tiefe);

  if (!isFinite(A_SB) || A_SB < 2 || !Number.isInteger(A_SB)) {
    throw new Error('anzahl_steher_breite muss eine ganze Zahl ≥ 2 sein.');
  }
  if (!isFinite(A_ST) || A_ST < 2 || !Number.isInteger(A_ST)) {
    throw new Error('anzahl_steher_tiefe muss eine ganze Zahl ≥ 2 sein.');
  }

  if (H_F === "" || H_F === null || H_F === undefined) {
    H_F = null;
  } else {
    H_F = Number(H_F);
    if (!isFinite(H_F) || H_F <= 0) {
      throw new Error('hoehe_flaeche_m muss leer oder eine Zahl > 0 sein.');
    }
  }
  if (!isFinite(B) || !isFinite(H) || !isFinite(T)) throw new Error('breite_m, hoehe_m und tiefe_m müssen Zahlen sein.');
  if (B <= 0 || H <= 0 || T <= 0) throw new Error('Breite, Höhe und Tiefe müssen > 0 sein.');
  if (H_F !== null && H_F > H) throw new Error('hoehe_flaeche_m darf nicht größer als hoehe_m sein.');
  if (!traverse_name_intern) throw new Error('traverse_name_intern fehlt.');
  if (!bodenplatte_name_intern) throw new Error('bodenplatte_name_intern fehlt.');
  if (!untergrund) throw new Error('untergrund fehlt.');

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
 * @param {number|null} inputs.hoehe_flaeche_m
 * @param {number} inputs.anzahl_steher_breite
 * @param {number} inputs.anzahl_steher_tiefe
 * @param {string} inputs.traverse_name_intern
 * @param {string} inputs.bodenplatte_name_intern
 * @param {boolean} [inputs.gummimatte=true]
 * @param {string} inputs.untergrund
 * @param {string} [inputs.name='Tisch']
 * @param {Object} catalog – siehe oben
 * @returns {Object} konstruktion
 */
export function buildTisch(inputs, catalog) {
  const {
    breite_m, hoehe_m, tiefe_m, hoehe_flaeche_m, anzahl_steher_breite, anzahl_steher_tiefe, traverse_name_intern, bodenplatte_name_intern,
    gummimatte = true,
    untergrund,
    name = 'Tisch',
  } = inputs;

  validateTischInputs({ breite_m, hoehe_m, tiefe_m, hoehe_flaeche_m, anzahl_steher_breite, anzahl_steher_tiefe, traverse_name_intern, bodenplatte_name_intern, untergrund }, catalog);

  const B = Number(breite_m);
  const H = Number(hoehe_m);
  const T = Number(tiefe_m);
  let H_F = null;
  const A_SB = Number(anzahl_steher_breite);
  const A_ST = Number(anzahl_steher_tiefe);
  if (hoehe_flaeche_m !== "" && hoehe_flaeche_m !== null && hoehe_flaeche_m !== undefined) {
    H_F = Number(hoehe_flaeche_m);
  }
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

  // Positionen der Steher (Raster)
  const dx = (B - 2 * t_b) / (A_SB - 1);
  const dy = (T - 2 * t_a) / (A_ST - 1);

  const midY = Math.floor(A_ST / 2); // mittlere Reihe zählt zur vorderen Hälfte

  const traversen = [];
  const bodenplatten = [];

  // --- Vertikale Steher (Traversenstrecken) + Bodenplatten ---
  let steherCount = 0;
  let plateCount = 0;

  for (let j = 0; j < A_ST; j++) {
    const y = t_a + j * dy;

    // vordere Hälfte -> nach hinten (+y), hintere Hälfte -> nach vorne (-y)
    const orientY = (j <= midY) ? [0, 1, 0] : [0, -1, 0];

    for (let i = 0; i < A_SB; i++) {
      const x = t_b + i * dx;

      steherCount++;
      traversen.push({
        typ: 'Traversenstrecke',
        traverse_name_intern,
        start: [x, y, 0],
        ende:  [x, y, H],
        orientierung: orientY,
        objekttyp: 'TRAVERSE',
        element_id_intern: `Steher_${steherCount}`,
        anzeigename: travAnzeige,
      });

      plateCount++;
      bodenplatten.push({
        typ: 'Bodenplatte',
        name_intern: bodenplatte_name_intern,
        mittelpunkt: [x, y, 0],
        orientierung: [0, 0, 1],
        drehung: orientY,
        untergrund,
        gummimatte: gummimatte ? 'GUMMI' : null,
        objekttyp: 'BODENPLATTE',
        element_id_intern: `Bodenplatte_${plateCount}`,
        anzeigename: plateAnzeige,
      });
    }
  }

  // --- Top-Traversen: A_ST Stück in y-Richtung (über Breite B), A_SB Stück in x-Richtung (über Tiefe T)
  const topTraversen = [];

  // quer über B, an mehreren y-Positionen (Nutze t_b wie im alten Code für "oben vorne/hinten")
  const dyTop = (T - 2 * t_b) / (A_ST - 1);
  for (let j = 0; j < A_ST; j++) {
    const yTop = t_b + j * dyTop;
    topTraversen.push({
      typ: 'Traversenstrecke',
      traverse_name_intern,
      start: [0, yTop, H - t_a],
      ende:  [B, yTop, H - t_a],
      orientierung: [0, 0, -1],
      objekttyp: 'TRAVERSE',
      element_id_intern: `Top_B_${j + 1}`,
      anzeigename: travAnzeige,
    });
  }

  // quer über T, an mehreren x-Positionen
  const dxTop = (B - 2 * t_b) / (A_SB - 1);
  for (let i = 0; i < A_SB; i++) {
    const xTop = t_b + i * dxTop;
    topTraversen.push({
      typ: 'Traversenstrecke',
      traverse_name_intern,
      start: [xTop, 0, H - t_a],
      ende:  [xTop, T, H - t_a],
      orientierung: [0, 0, -1],
      objekttyp: 'TRAVERSE',
      element_id_intern: `Top_T_${i + 1}`,
      anzeigename: travAnzeige,
    });
  }

  // Basis-Bauelemente
  const bauelemente = [ ...traversen, ...bodenplatten, ...topTraversen ];

  // --- Wenn Unterkante definiert, dann Fläche und untere Truss ---
  if (H_F !== null) {
    const trav_bottom_front = {
      typ: 'Traversenstrecke',
      traverse_name_intern,
      start: [ 0, t_b, H - H_F + t_a ],
      ende:  [ B, t_b, H - H_F + t_a ],
      orientierung: [ 0, 0, 1],
      objekttyp: 'TRAVERSE',
      element_id_intern: 'Strecke_Unten_Vorne',
      anzeigename: travAnzeige,
    };

    const flaeche = {
      typ: 'senkrechteFlaeche',
      eckpunkte: [
        [ 0, 0, H - H_F ],
        [ 0, 0, H ],
        [ B, 0, H ],
        [ B, 0, H - H_F ],
      ],
      objekttyp: 'SENKRECHTE_FLAECHE',
      element_id_intern: 'Flaeche_Vorne',
      anzeigename: 'Fläche',
      flaechenlast: null,
      gesamtgewicht: null,
    }
    bauelemente.push(trav_bottom_front, flaeche);
  }

  // Gesamtobjekt (flach, gut serialisierbar)
  const konstruktion = {
    version: 1,
    typ: 'Tisch',
    name,
    breite_m: B,
    hoehe_m: H,
    tiefe_m: T,
    hoehe_flaeche_m: H_F,
    traverse_name_intern: traverse_name_intern,
    bauelemente: bauelemente,
  };

  return konstruktion;
}
