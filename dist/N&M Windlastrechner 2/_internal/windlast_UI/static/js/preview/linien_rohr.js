// linien_rohr.js

export function rohr_linien(strecke) {
  const a = strecke.start ?? [0, 0, 0];
  const b = strecke.ende  ?? [0, 0, 0];

  return {
    segments: [
      [a, b],
    ],
    metadata: {
      typ: 'ROHR',
      id: strecke.element_id_intern,
      anzeigename: strecke.anzeigename,
    },
  };
}