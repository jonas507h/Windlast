// modal/norminfo.js
// Zentrale Norminfos – Hauptberechnung + eigene Texte für Alternativen

export const NORMINFO = {
  EN_13814_2005: {
    title: "DIN EN 13814:2005-06 – Fliegende Bauten und Anlagen für Veranstaltungsplätze und Vergnügungsparks – Sicherheit",
    body: `
      <p>
        Diese Norm regelt unter anderem die Windlastberechnung für fliegende Bauten. Dabei gibt sie Staudrücke und ein Verfahren zum Standsicherheitsnachweis vor, verweist zur Berechnung der Windkräfte jedoch auf die DIN EN 1991-1-4.
        Sie ist in Deutschland baurechtlich eingeführt für die Berechnung von fliegenden Bauten. Neuere Versionen der Norm sind veröffentlicht, aber noch nicht baurechtlich eingeführt.
        Staudrücke werden für Konstruktionen mit einer Höhe bis zu 50m vereinfacht in einer Tabelle vorgegeben. Daher ist die Norm nur unter bestimmten Voraussetzungen anwendbar:
      </p>
      <ul>
        <li>Referenzwindgeschwindigkeit höchstens 28 m/s (Achtung bei Windzone 4 und in Küstengebieten)</li>
        <li>Ab einer Windgeschwindigkeit von 25 m/s in 10 m Höhe muss die Anlage geschützt und angemessen verstärkt werden</li>
      </ul>
      <p>
        Für komplexere Bauwerke, höhere Windgeschwindigkeiten oder exponierte Standorte ist die Anwendung der DIN EN 13814:2005-06 nicht vorgesehen. Hier sind gesonderte Nachweise nach DIN EN 1991-1-4 erforderlich.
      </p>
      <p>
        <b>Diese Software liefert einen solchen Nachweis auch bei der Berechnung nach DIN EN 1991-1-4 nicht. Wendet euch hier an einen Statiker.</b>
      </p>
      <p>
        Es besteht die Möglichkeit, die angenommenen Staudrücke abzumindern, wenn bestimmte Schutzmaßnahmen möglich sind. Bei der vorliegenden Berechung wurden diese Abminderungen nicht berücksichtigt.
        Bei nicht gewährleisteter Standsicherheit werden die Abminderungen automatisch in einer zweiten Berechnung berücksichtigt. Details hierzu findet im entsprechenden Abschnitt der Tabelle.
      </p>
    `,
    alt: {
      "IN_BETRIEB": {
        title: "DIN EN 13814:2005-06 – Berücksichtigung von möglichen Schutzmaßnahmen",
        body: `
          <p>
            Bei der Berechnung nach DIN EN 13814:2005-06 können Abminderungen der Staudrücke berücksichtigt werden, wenn bestimmte Schutzmaßnahmen möglich sind. Bei der Berechnung &bdquo;mit Schutzmaßnahmen&ldquo; wurden diese Abminderungen berücksichtigt.
            Sollen die hier aufgelisteten Werte verwendet werden, müssen ab einer Windgeschwindigkeit von 15 m/s Schutzmaßnahmen getroffen werden.
            In unseren Bereich sind zum Beispiel folgende Schutzmaßnahmen möglich:
          </p>
          <ul>
            <li>Abnehmen von Planen oder anderen großen Windangriffsflächen</li>
            <li>Evakuierung der Konstruktion und der umliegenden Bereiche</li>
          </ul>
          <p>
            Die Schutzmaßnahmen müssen vorher definiert werden und wir müssen sicherstellen, dass diese Maßnahmen auch tatsächlich umgesetzt werden.
            <b>Andernfalls dürfen die abgeminderten Staudrücke nicht verwendet werden.</b>
          </p>
          <p>
            Wird als Schutzmaßnahme die Konstruktion verändert (z.&nbsp;B. Abnehmen von Planen), muss für die Konstruktion in diesem Zustand ebenfalls ein Standsicherheitsnachweis geführt werden.
            <b>Dieser Nachweis wird von dieser Software nicht automatisch geführt.</b>
          </p>
        `
      },
    }
  },

  EN_17879_2024: {
    title: "DIN EN 17879:2024-08 – Event-Strukturen – Sicherheit",
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
