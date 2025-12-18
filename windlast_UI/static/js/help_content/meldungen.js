// static/js/help_content/meldungen.js

export const MELDUNGEN_HELP_PAGES = [
  {
    id: "meldungen:allgemein",
    title: "Meldungen",
    stand: "18.12.2025",
    body: `
      <p>
        Im Meldungs-Fenster werden alle Infos, Hinweise, Warnungen und Fehlermeldungen aus der Berechnung angezeigt. Nachdem eine Berechnung durchgeführt wurde, erscheint in der Ergebnis-Tabelle rechts neben dem Titel der Norm eine farblich hinterlegte Zahl.
        Diese gibt die Anzahl der vorliegenden Meldungen an. Ein Klick auf diese Zahl öffnet das zugehörige Meldungs-Fenster.
      </p>
      <p>
        Meldungen werden auch bei fast jeder fehlerfreien Berechnung erzeugt, sie sind also kein Grund zur Sorge. <b>Unbedingt zu beachten sind jedoch Warnungen (gelb) oder Fehler (rot).</b>
      </p>
      <p>Meldungen sind in vier Kategorien eingeteilt:</p>
      <ul>
        <li><b>Fehler (rot):</b> Rechenkritische Probleme. Die Berechnung konnte aufgrund des Fehlers nicht durchgeführt werden.</li>
        <li><b>Warnungen (gelb):</b> Die Berechnung konnte durchgeführt werden, das Ergebnis steht aber gegebenenfalls in Konflikt mit den zugrunde gelegten Normen.</li>
        <li><b>Hinweise (blau):</b> Hinweise auf Besonderheiten in der Berechnung oder Abweichungen von den Normen, die jedoch keine kritischen Auswirkungen haben.</li>
        <li><b>Informationen (grau):</b> Allgemeine Informationen zur Berechnung oder zum Programmablauf.</li>
      </ul>

      <help-include page="meldungen:haeufige_meldungen" auto-level="true"></help-include>
    `
  },

  {
    id: "meldungen:haeufige_meldungen",
    title: "Häufige Meldungen",
    pfad: ["meldungen:allgemein"],
    stand: "18.12.2025",
    body: `
      <h4>Fehler</h4>
        <faq question="Gesamthöhe ...m überschreitet die höchste definierte Obergrenze ...m ">
          Die Konstruktion kann nicht berechnet werden, weil sie zu hoch ist. Die Staudrücke nach den vereinfachten Verfahren sind nur bis zu einer bestimmten Höhe anwendbar
          ([[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] bis 50m, [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]] bis 30m,
          [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]] bis 25m).
        </faq>
      <h4>Warnungen</h4>
        <faq question="Abminderungen der Windlasten nach DIN EN 1991-1-4:2010-12/NA sind bei Bauten, die jederzeit errichtet und demontiert werden können (z.B. fliegende Bauten), nicht zulässig.">
          Im nationalen Anhang der [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]] ist festgelegt, dass bei kurzen Aufstelldauern eine Abminderung des Staudrucks möglich ist.
          Fliegende Bauten bzw. allgemein Bauten, die jederzeit errichtet und demontiert werden können, sind von dieser Regelung jedoch explizit ausgenommen
          (siehe [[norm:DIN_EN_1991_1_4_2010:abminderungen|DIN EN 1991-1-4:2010-12 – Abminderung von Staudrücken]]).
          Die Software wendet die Abminderung dennoch an. Soll dies nicht geschehen, könnt ihr das Feld [[header:aufstelldauer|Aufstelldauer]] einfach leer lassen.
        </faq>
        <faq question="Die Windgeschwindigkeiten in Windzone '4 ...' überschreiten die für die Anwendung der DIN EN 13814:2005-06 zulässigen Werte.">
          Die Staudrücke nach [[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] sind nur bis zu einer Referenzwindgeschwindigkeit von 28 m/s zulässig. Für Windzone 4 gibt der nationale Anhang
          der [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]] jedoch eine höhere Basiswindgeschwindigkeit vor.
          Die Berechnung wird trotzdem durchgeführt. Ihr solltet jedosch prüfen, ob die Ergebnisse für eure Anwendung noch geeignet sind.
        </faq>
        <faq question="Die verwendete Aufstelldauer zwischen 3 Tagen und 3 Monaten führt zu einer Abminderung des Staudrucks, die nur für den Zeitraum von Mai bis August zulässig ist.">
          Die hier benutzte [[norm:DIN_EN_1991_1_4_2010:abminderungen|Abminderung der Staudrücke]] gemäß dem nationalen Anhang der
          [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]] ist nur in einem Aufstellzeitraum zwischen Mai und August zulässig.
          Wenn das bei euch nicht der Fall ist, könnt ihr einfach eine Aufstelldauer zwischen 3 und 12 Monaten angeben.
        </faq>
      <h4>Hinweise</h4>
        <faq question="Für Paarung ...–... wurde auf DIN EN ... zurückgegriffen.">
          Nicht alle drei Normen enthalten Reibwerte für alle Materialpaarungen.
          In diesem Fall wird auf eine andere Norm zurückgegriffen, die einen Reibwert für die gewählte Paarung enthält.
        </faq>
      <h4>Informationen</h4>
        <faq question="Maßgebend ist die Paarung ...–... mit μ=...">
          Gibt den Reibwert μ an, der für der Berechnung verwendet wurde und von welcher Materialpaarung dieser stammt.
          Ausschlaggebend ist immer der niedrigste Reibwert über alle Bodenplatten und Materialpaarungen.
        </faq>
    `
  }
];