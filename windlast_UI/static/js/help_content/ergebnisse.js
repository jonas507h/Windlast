// static/js/help_content/ergebnisse.js

export const ERGEBNISSE_HELP_PAGES = [
  {
    id: "ergebnisse:allgemein",
    title: "Ergebnisse",
    body: `
      <p>
        Die Rechenergebnisse werden im unteren Bereich der Seite in einer Tabelle dargestellt. Jede Spalte repräsentiert eine berechnete Norm.
        Die Tabelle wird aktualisiert durch einen Klick auf den &bdquo;Berechnen&ldquo;-Button. Eine automatische Aktualisierung bei jeder Eingabeänderung erfolgt nicht.
      </p>
      <p>
        <b>Die angezeigten Werte sind Ergebnis einer Überschlagberechnung und ersetzen keine statischen Nachweise durch einen qualifizierten Statiker.</b>
      </p>
      <p>
        Die Berechnung erfolgt blockweise. Für jede Norm werden die [[ergebnisse:sicherheit|Sicherheitswerte]] und der [[ergebnisse:ballast|erforderliche Ballast]] berechnet.
        In den oberen Zeilen werden die Ergebnisse der Hauptberechnung – also ohne Berücksichtigung möglicher Schutzmaßnahmen – dargestellt.
        Da die Traversenkonstruktionen meist nur temporär aufgestellt werden und bestimmte Schutzmaßnahmen getroffen werden können, dürfen die Staudrücke oft abgemindert werden.
        Wenn die Konstruktion in der Hauptberechnung nicht standsicher ist, werden automatisch weitere Berechnungen mit Berücksichtigung möglicher Schutzmaßnahmen durchgeführt.
        Die Ergebnisse dieser Berechnungen werden in den unteren Blöcken dargestellt. Details zu den einzelnen Normen findet ihr hier:
      </p>
      <ul>
        <li>[[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]]</li>
        <li>[[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]]</li>
        <li>[[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]]</li>
      </ul>
      <p>
        In den Titelzellen erscheint nach einer Berechnung rechts eine farblich hinterlegte Zahl. Diese Zahl gibt die Anzahl der [[meldungen:allgemein|Meldungen]]
        für die jeweilige Berechnung an. Ein Klick darauf öffnet das Meldungs-Fenster mit den ausführlichen Texten. Ein Klick auf den Norm-Titel öffnet die zugehörige
        [[norm:allgemein|Hilfe-Seite]].
      </p>
      <p>
        In den vier Zellen darunter werden die Ergebnisse angezeigt. [[ergebnisse:sicherheit|Sicherheitswerte]] werden immer aufgerundet
        und der [[ergebnisse:ballast|erforderliche Ballast]] wird immer abgerundet. &bdquo;--&ldquo; erscheint, wenn keine gültigen Ergebnisse vorliegen
        (z. B. bei Fehlern in der Berechnung oder wenn noch nichts berechnet wurde). ∞ erscheint, wenn die Sicherheit rechnerisch unendlich groß ist
        (näheres dazu [[ergebnisse:unendliche_sicherheit|hier]]). Ein Klick auf eine Zelle öffnet das [[zwischenergebnis:allgemein|Zwischenergebnis-Fenster]],
        wo alle Zwischenergebnisse der Berechnung detailliert dargestellt aufgelistet sind.
      </p>
      <p>
        <b>Die Software berechnet nur die Standsicherheit der Konstruktion. Bauteile und Verbindungen werden nicht geprüft.</b>
      </p>
    `
  },

  {
    id: "ergebnisse:sicherheit",
    title: "Sicherheitswerte",
    pfad: ["ergebnisse:allgemein"],
    body: `
      <p>
        Im Rahmen des Standsicherheitsnachweises nach [[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] oder [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]]
        sind jeweils Kippsicherheit, Gleitsicherheit und Abhebesicherheit zu prüfen.
        Im Grundsatz muss dafür die Summe der stabilisierenden Kräfte multipliziert mit den jeweiligen Teilsicherheitsbeiwerten größer sein als die Summe der
        destabilisierenden Kräfte, ebenfalls multipliziert mit den jeweiligen Teilsicherheitsbeiwerten. Diese Bedingung ist bei einem Sicherheitswert von 1,00 genau erfüllt.
        Da die Teilsicherheitsbeiwerte für destabilisierende Kräfte größer sind als für stabilisierende Kräfte, ist auch bei einem Sicherheitswert von 1,00 ein Puffer vorhanden.
      </p>
      <p>
        <b>Die Software berechnet nur die Standsicherheit der Konstruktion. Bauteile und Verbindungen werden nicht geprüft.</b>
      </p>
      <p>
        Die Sicherheitswerte werden auf zwei Nachkommastellen abgerundet. Es werden verschiedene Windrichtungen berechnet und der jeweils niedrigste Wert angezeigt.
      </p>
      <help-include page="ergebnisse:unendliche_sicherheit" auto-level="true"></help-include>
    `
  },

  {
    id: "ergebnisse:ballast",
    title: "Erforderlicher Ballast",
    shortTitle: "Ballast",
    pfad: ["ergebnisse:allgemein"],
    body: `
      <p>
        Sind nicht alle [[ergebnisse:sicherheit|Sicherheitswerte]] ≥ 1,00, so wird automatisch der erforderliche Ballast berechnet, mit dem alle Sicherheitswerte ≥ 1,00 sind.
        <b>Der erforderliche Ballast ist eine rechnerische Größe und hat seinen Schwerpunkt im Mittelpunkt der Grundfläche.</b> Bei symmetrischen Konstruktionen kann der Ballast
        also gleichmäßig auf die Bodenplatten verteilt werden, bei asymmetrischen Konstruktionen muss die Verteilung entsprechend angepasst werden.
      </p>
      <p>
        <b>Achtung:</b> Der Ballast ist nur ein Überschlagswert. In der Praxis sind unter anderem folgende Aspekte unbeding zu beachten:
      </p>
      <ul>
        <li>Ballast hat Volumen, benötigt also Platz und bietet Windangriffsflächen, die nicht mitgerechnet wurden.</li>
        <li>Der Ballast muss mit der Konstruktion verbunden werden und die Verbindung sowie die Konstruktion muss die auftretenden Kräfte aufnehmen können. <b>Diese Software
        prüft keine Bauteile.</b></li>
      </ul>
      <p>
        Der erforderliche Ballast wird nach folgendem Schema abgerundet:
      </p>
      <ul>
        <li>&lt; 1000 kg: auf 10 kg</li>
        <li>1000 - 9999 kg: auf 0,1 t</li>
        <li>≥ 10000 kg: auf 3 signifikante Stellen in t</li>
      </ul>
    `
  },

  {
    id: "ergebnisse:unendliche_sicherheit",
    title: "Unendliche Sicherheit",
    pfad: ["ergebnisse:allgemein", "ergebnisse:sicherheit"],
    body: `
      <p>
        Es kann (insbesondere bei der Abhebesicherheit) vorkommen, dass der berechnete Sicherheitswert unendlich groß ist.
        Dies ist der Fall, wenn in der Berechnung keine destabilisierenden Kräfte auftreten. Bei der Abhebesicherheit sind destabilisierende Kräfte ausschließlich Kräfte,
        die nach oben wirken. Solche Kräfte treten rechnerisch z.B. bei Dachflächen auf, allerdings nicht bei Traversen.
        Bei unseren Traversenkonstruktionen kann die Abhebesicherheit also bei der Betrachtung vernachlässigt werden, da keine Abhebekraft vorhanden ist.
      </p>
      <p>
        Ob ein solcher Fall vorliegt, wird in der Software immer rechnerisch geprüft. Es werden keine Sicherheitswerte pauschal als unendlich angenommen.
      </p>
    `
  }
];