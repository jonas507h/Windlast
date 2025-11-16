// modal/norminfo.js
// Statischer Inhalt für Norm-Infos im Footer

export const NORMINFO = {
  EN_13814_2005: {
    title: "EN 13814:2005 – Fahrgeschäfte und Anlagen für Jahrmärkte",
    body: `
      <p>
        Diese Norm regelt Sicherheit, Auslegung und Prüfung von Fahrgeschäften
        und ähnlichen Anlagen.
      </p>
      <ul>
        <li>Ausgabejahr: 2005</li>
        <li>Geltungsbereich: Fliegende Bauten / Fahrgeschäfte</li>
        <li>Hinweis: In einigen Ländern inzwischen durch EN 13814:2019 ersetzt,
            bei Windlast 2 aktuell als Referenznorm 2005 hinterlegt.</li>
      </ul>
    `
  },
  EN_17879_2024: {
    title: "EN 17879:2024 – Temporäre Bauten / Konstruktionen",
    body: `
      <p>
        Norm für temporäre Konstruktionen im Veranstaltungsbereich, z.B. Bühnen,
        Traversenkonstruktionen, Sonderbauten.
      </p>
      <ul>
        <li>Ausgabejahr: 2024</li>
        <li>Anwendungsbereich: Temporäre Bauwerke im Eventbereich</li>
        <li>Hinweis: In Verbindung mit nationalen Anhängen / Richtlinien zu verwenden.</li>
      </ul>
    `
  },
  EN_1991_1_4_2010: {
    title: "EN 1991-1-4:2010 – Eurocode 1, Windlasten",
    body: `
      <p>
        Eurocode 1, Teil 1-4: Allgemeine Einwirkungen – Windlasten.
      </p>
      <ul>
        <li>Ausgabejahr: 2010</li>
        <li>Inhalt: Ermittlung charakteristischer Windlasten auf Bauwerke</li>
        <li>Hinweis: Nationale Anhänge (NA) sind zwingend zu berücksichtigen.</li>
      </ul>
    `
  }
};

/**
 * Liefert Titel + Body-HTML für ein Norm-Info-Modal.
 * Fällt bei Unbekanntem Key auf eine einfache Default-Nachricht zurück.
 */
export function getNorminfo(normKey) {
  const info = NORMINFO[normKey];
  if (info) return info;
  return {
    title: `Norminfo – ${normKey}`,
    body: `
      <p>Für diese Norm ist noch kein ausführlicher Info-Text hinterlegt.</p>
      <p>Bitte später ergänzen.</p>
    `
  };
}
