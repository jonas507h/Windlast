// modal/norminfo.js
// Zentrale Norminfos – Hauptberechnung + eigene Texte für Alternativen

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
    `,
    alt: {
      // Beispiel – Keys an deine data-szenario-Werte anpassen
      "IN_BETRIEB": {
        title: "EN 13814:2005 – Alternative „Wind 0°“",
        body: `
          <p>
            Diese Alternative bildet ein spezielles Nachweisszenario ab
            (z.&nbsp;B. Windrichtung 0°, besondere Aufstellung, etc.).
          </p>
        `
      },
    }
  },

  EN_17879_2024: {
    title: "EN 17879:2024 – Temporäre Bauten / Konstruktionen",
    body: `
      <p>
        Norm für temporäre Konstruktionen im Veranstaltungsbereich,
        z.&nbsp;B. Bühnen, Traversenkonstruktionen, Sonderbauten.
      </p>
      <ul>
        <li>Ausgabejahr: 2024</li>
        <li>Anwendungsbereich: Temporäre Bauwerke im Eventbereich</li>
        <li>Hinweis: In Verbindung mit nationalen Anhängen / Richtlinien zu verwenden.</li>
      </ul>
    `,
    alt: {
      // Beispiel-Platzhalter
      "IN_BETRIEB": {
        title: "EN 17879:2024 – Alternative „Standard-Szenario“",
        body: `
          <p>
            Alternative Nachweiskonfiguration auf Basis von EN 17879:2024,
            z.&nbsp;B. andere Nutzung oder Randbedingungen.
          </p>
        `
      }
    }
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
    `,
    alt: {
      // Beispiel-Platzhalter
      // "NA_DE": {
      //   title: "EN 1991-1-4:2010 – Alternative „NA DE“",
      //   body: `
      //     <p>
      //       Nachweis auf Basis des deutschen Nationalen Anhangs.
      //     </p>
      //   `
      // }
    }
  }
};

/**
 * Liefert Title + Body für Haupt- oder Alternativspalte.
 * - normKey: z.B. "EN_1991_1_4_2010"
 * - szenario: z.B. "wind_0" oder null
 */
export function getNorminfo(normKey, szenario = null) {
  const entry = NORMINFO[normKey];

  // Fallback, falls die Norm noch nicht hinterlegt ist
  if (!entry) {
    if (szenario) {
      return {
        title: `Norminfo – ${normKey} (Alternative ${szenario})`,
        body: `
          <p>Für diese Kombination aus Norm und Alternative ist noch kein Text hinterlegt.</p>
          <p>Bitte in <code>modal/norminfo.js</code> ergänzen.</p>
        `
      };
    }
    return {
      title: `Norminfo – ${normKey}`,
      body: `
        <p>Für diese Norm ist noch kein Info-Text hinterlegt.</p>
        <p>Bitte in <code>modal/norminfo.js</code> ergänzen.</p>
      `
    };
  }

  // Alternative mit eigenem Text?
  if (szenario && entry.alt && entry.alt[szenario]) {
    return entry.alt[szenario];
  }

  // Sonst: Haupttext
  return {
    title: entry.title,
    body: entry.body
  };
}
