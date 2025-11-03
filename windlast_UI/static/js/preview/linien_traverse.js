export function traversenstrecke_linien(strecke) {
  const a = strecke.start ?? [0,0,0];
  const b = strecke.ende ?? [0,0,0];
  return {
    segments: [ [a,b] ],
    metadata: { typ: 'TRAVERSE', id: strecke.element_id_intern, anzeigename: strecke.anzeigename },
  };
}
