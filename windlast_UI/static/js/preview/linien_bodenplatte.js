// linien_bodenplatte.js — erzeugt Linien für eine Bodenplatte (V0: reines Viereck in XZ)

// Hinweis: Der "Katalog" ist hier absichtlich lokal gekapselt und minimal.
// Später ersetzen wir das durch einen echten API-gestützten Katalog.
function localCatalogGetBodenplatte(nameIntern) {
  return { kantenlaenge: 1.0, anzeige_name: nameIntern };
}

export function bodenplatte_linien(plate) {
  const spec = localCatalogGetBodenplatte(plate.name_intern);
  const k = Number.isFinite(spec.kantenlaenge) ? Number(spec.kantenlaenge) : 1.0;
  const h = k / 2;
  const cx = plate.mittelpunkt?.[0] ?? 0;
  const cy = plate.mittelpunkt?.[1] ?? 0; // bleibt 0 in V0
  const cz = plate.mittelpunkt?.[2] ?? 0;

  // Viereck in XZ-Ebene (y = cy)
  const p1 = [cx - h, cy, cz - h];
  const p2 = [cx + h, cy, cz - h];
  const p3 = [cx + h, cy, cz + h];
  const p4 = [cx - h, cy, cz + h];

  return {
    segments: [ [p1,p2], [p2,p3], [p3,p4], [p4,p1] ],
    metadata: { typ: 'BODENPLATTE', id: plate.element_id_intern, anzeigename: plate.anzeigename },
  };
}
