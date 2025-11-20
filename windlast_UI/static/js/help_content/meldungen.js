// static/js/help_content/meldungen.js

export const MELDUNGEN_HELP_PAGES = [
  {
    id: "meldungen:allgemein",
    title: "Meldungen",
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

      <p>Einige häufig auftretenden Meldungen sind [[meldungen:haeufige_meldungen|hier]] erklärt</p>
    `
  },

  {
    id: "meldungen:haeufige_meldungen",
    title: "Häufige Meldungen",
    body: `
      <h4>Fehler</h4>
      <h4>Warnungen</h4>
      <h4>Hinweise</h4>
      <h4>Informationen</h4>
      <faq question="Maßgebend ist die Paarung Stahl–Gummi mit μ=0.600.">
        Gibt den Reibwert μ an, der für der Berechnung verwendet wurde und von welcher Materialpaarung dieser stammt. Ausschlaggebend ist immer der niedrigste Reibwert über alle Bodenplatten und Materialpaarungen.
      </faq>
    `
  }
];