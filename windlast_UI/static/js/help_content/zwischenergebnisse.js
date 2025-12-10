// static/js/help_content/zwischenergebnisse.js

export const ZWISCHENERGEBNISSE_HELP_PAGES = [
  {
    id: "zwischenergebnis:allgemein",
    title: "Zwischenergebnisse",
    pfad: ["ergebnisse:allgemein"],
    body: `
      <p>
        In der Ergebnistabelle öffnet ein Klick auf ein Ergebnisfeld ein Fenster mit den zugehörigen Zwischenergebnissen. Hier werden alle Zwischenergebnisse
        aus der Berechnung angezeigt, die zu dem jeweiligen Endergebnis geführt haben. In dem Fenster sind grundsätzlich nur die Zwischenergebnisse der Berechnung einer Norm bei
        einem Szenario (z.B. mit oder ohne Schutzmaßnahmen) zu sehen. Diese werden automatisch gruppiert und können gefiltert werden.
      </p>
      <h3>Gruppierung</h3>
      <p>
        Die Gruppierung erfolgt automatisch nach folgendem Schema. Nicht immer sind alle Gruppierungen vorhanden, das hängt von der jeweiligen Berechnung ab.
      </p>
      <ul>
        <li><b>Windrichtung:</b> Die Software prüft die Standsicherheit der Konstruktion für 8 Windrichtungen. Alle Ergebnisse einer Windrichtung werden zusammengefasst.</li>
        <li><b>Element:</b> Die Ergebnisse werden nach den einzelnen Bauelementen (z.B. Traversenstrecke, Rohr, Bodenplatte) der Konstruktion gruppiert.</li>
        <li><b>Achse:</b> Die Kippsicherheit wird für jede Kippachse der Konstruktion überprüft und die Ergebnisse werden entsprechend gruppiert.</li>
        <li><b>Zone:</b> Senkrechte Flächen werden ggf. in verschiedene Zonen unterteilt. Die den einzelnen Zonen zugeordneten Ergebnisse werden dann zusammengefasst.</li>
        <li><b>Segment:</b> Bei hohen Konstruktionen müssen je nach Norm in unterschiedlichen Höhen unterschiedliche Staudrücke angesetzt werden. Die Software teilt die einzelnen
        Bauelemente entsprechend und berechnet die Ergebnisse für jeden Höhenbereich.</li>
      </ul>
      <h3>Filterung</h3>
      <p>
        Über die Filterfunktion können die angezeigten Zwischenergebnisse weiter eingeschränkt werden. Im oberen Bereich des Fensters findet ihr zwei Reihen mit Buttons.
        In der ersten Reihe könnt ihr nach den verschiedenen Nachweisen filtern. Die Filter werden vorausgewählt, je nachdem welches Ergebnisfeld ihr angeklickt habt.
      </p>
      <ul>
        <li><b>Alle:</b> Zeigt alle Zwischenergebnisse an.</li>
        <li><b>Kippen:</b> Zeigt nur die Zwischenergebnisse zur Kippsicherheit an.</li>
        <li><b>Gleiten:</b> Zeigt nur die Zwischenergebnisse zur Gleitsicherheit an.</li>
        <li><b>Abheben:</b> Zeigt nur die Zwischenergebnisse zur Abhebesicherheit an.</li>
        <li><b>Ballast:</b> Zeigt nur die Zwischenergebnisse zur Ballastberechnung an.</li>
        <li><b>Kräfte:</b> Zeigt nur die Zwischenergebnisse zu den wirkenden Kräften an.</li>
        <li><b>Basis:</b> Zeigt nur die Basis-Zwischenergebnisse an, die für alle Berechnungen relevant sind (z.B. Staudrücke).</li>
      </ul>
      <p>
        In der zweiten Reihe könnt ihr nach der Relevanz der Zwischenergebnisse filtern. Die Software arbeitet in vielen Fällen nach dem Prinzip &bdquo;ausprobieren und
        den ungünstigsten Wert finden&ldquo; (z.B. bei der Wahl der Kippachse oder der Windrichtung). Standardmäßig werden nur relevante Zwischenergebnisse angezeigt.
        Bei Bedarf könnt ihr aber auch alle Zwischenergebnisse einblenden. Die Zwischenergebnisse werden entsprechend dieser Kategorien auch farblich markiert.
      </p>
      <ul>
        <li><b>Relevant (grün)</b> sind alle Zwischenergebnisse, die direkt zum Endergebnis beigetragen haben.</li>
        <li><b>Entscheidungsrelevant (blau)</b> sind alle Zwischenergebnisse, die für die Entscheidungsfindung wichtig sind, aber nicht direkt zum Endergebnis beitragen.
        Beispielsweise werden die Kippsicherheiten der verschiedenen Windrichtungen verglichen. Die niedrigste Sicherheit &bdquo;gewinnt&ldquo; und wird relevant. Die anderen
        Werte sind dann entscheidungsrelevant.</li>
        <li><b>Irrelevant (grau)</b> sind alle Zwischenergebnisse, die nur zu einem entscheidungsrelevanten Wert beigetragen haben und damit keinen direkten Einfluss
        auf das Endergebnis hatten.
      </ul>
    `
  }
];