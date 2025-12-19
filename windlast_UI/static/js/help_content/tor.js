// static/js/help_content/tor.js

export const TOR_HELP_PAGES = [
  {
    id: "tor:allgemein",
    title: "Traversentor",
    pfad: ["app:konstruktionen"],
    body: `
      <p>
        Ist die Konstruktion &bdquo;Tor&ldquo; ausgewählt, kann ein Traversentor bestehend aus zwei Stehern und einer Quertraverse berechnet werden.
        Die Konstruktion steht auf zwei Bodenplatten.
        Berechnet wird nur die reine Traversenkonstruktion. <b>Angebaute Technik (z. B. Lautsprecher, Scheinwerfer o. Ä.), Deko, Planen usw. können aktuell nicht berechnet werden.</b>
      </p>
      <p>
        Im [[app:vorschau|Vorschaufenster]] links werden die aktuellen Eingaben grafisch dargestellt. Rechts können folgende Eingaben gemacht werden:
      </p>

      <help-include page="tor:traverse" auto-level="true"></help-include>
      <help-include page="tor:traversen-orientierung" auto-level="true"></help-include>
      <help-include page="tor:bodenplatte" auto-level="true"></help-include>
      <help-include page="tor:gummimatte" auto-level="true"></help-include>
      <help-include page="tor:untergrund" auto-level="true"></help-include>
      <help-include page="tor:hoehe" auto-level="true"></help-include>
      <help-include page="tor:breite" auto-level="true"></help-include>
      <help-include page="tor:hoehe_flaeche" auto-level="true"></help-include>
      <help-include page="tor:anzahl_steher" auto-level="true"></help-include>
    `
  },

  {
    id: "tor:traverse",
    title: "Traverse (Pflichtfeld)",
    shortTitle: "Traverse",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Traversen die entsprechende Traverse aus. Die Auswahl beeinflusst alle in der Konstruktion verwendeten Traversen.
        Bei der Berechnung werden sowohl die Eigengewichte als auch die Windangriffsflächen der Traversen berücksichtigt.
      </p>
    `
  },

  {
    id: "tor:traversen-orientierung",
    title: "Traversen-Orientierung (Pflichtfeld)",
    shortTitle: "Traversen-Orientierung",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Dreht alle Traversen in 90°-Schritten um ihre Längsachse. Je nach Ausrichtung der Traverse ändert sich die Windangriffsfläche und damit die Windlasten auf die Konstruktion.
        Bei Traversen mit quadratischem Querschnitt (z.B. Prolyte H30V, Prolyte H40V) hat die Orientierung keinen Einfluss auf die Windlasten.
        Bodenplatten werden entsprechend mitgedreht, sodass bei dreieckigen Bodenplatten die Ecken immer richtig ausgerichtet sind.
      </p>
      <p>
        Die Angaben wie &bdquo;Spitze nach oben&ldquo; beziehen sich auf Quertraverse. Das [[app:vorschau|Vorschaufenster]] links zeigt auch die aktuelle Orientierung an,
        sodass hier die Eingaben überprüft werden können.
      </p>
    `
  },

  {
    id: "tor:bodenplatte",
    title: "Bodenplatte (Pflichtfeld)",
    shortTitle: "Bodenplatte",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Bodenplatten die entsprechende Bodenplatte aus. Die Auswahl beeinflusst alle in der Konstruktion verwendeten Bodenplatten.
        Bei der Berechnung werden Größe und Geometrie, Gewicht und Material der Bodenplatten berücksichtigt. Eine blau markierte Bodenplatte im
        [[app:vorschau|Vorschaufenster]] zeigt an, dass unter der Bodenplatte eine Gummimatte verwendet wird.<br>
        Da das Material der Bodenplatte Einfluss auf den Reibwert hat und nicht für alle Materialpaarungen Reibwerte in den zugrunde gelegten Normen
        ([[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] und [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]]) angegeben sind, kann die Auswahl der Bodenplatte Einfluss
        auf die Auswahlmöglichkeiten im [[tor:gummimatte|Gummimatte-Feld]] und im [[tor:untergrund|Untergrund-Feld]] haben.
      </p>
    `
  },

  {
    id: "tor:gummimatte",
    title: "Gummimatte (Pflichtfeld)",
    shortTitle: "Gummimatte",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Wählt hier aus, ob ihr Gummimatten unter den Bodenplatten verwendet. Gummimatten erhöhen in der Regel den Reibwert zwischen Bodenplatte und Untergrund
        und können sich positiv auf die Gleitsicherheit der Konstruktion auswirken. Im [[app:vorschau|Vorschaufenster]] werden Bodenplatten mit untergelegten
        Gummimatten blau markiert.<br>
        Da die Gummimatte Einfluss auf den Reibwert hat und nicht für alle Materialpaarungen Reibwerte in den zugrunde gelegten Normen
        ([[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] und [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]]) angegeben sind, können die Auswahlmöglichkeiten in diesem Feld
        je nach ausgewählter [[tor:bodenplatte|Bodenplatte]] eingeschränkt sein oder automatisch geändert werden. Die Auswahl der Gummimatte kann auch Einfluss auf
        auf die Auswahlmöglichkeiten im [[tor:untergrund|Untergrund-Feld]] haben.
      </p>
    `
  },

  {
    id: "tor:untergrund",
    title: "Untergrund (Pflichtfeld)",
    shortTitle: "Untergrund",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Wählt hier den Untergrund aus, auf dem die Konstruktion steht. Der Untergrund beeinflusst den Reibwert zwischen Bodenplatte und Untergrund. Dieser wird anhand der
        [[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] bzw. [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]] automatisch bestimmt.<br>
        Da der Reibwert nicht für alle Materialpaarungen in den zugrunde gelegten Normen angegeben ist, können die Auswahlmöglichkeiten in diesem Feld
        je nach ausgewählter [[tor:bodenplatte|Bodenplatte]] und [[tor:gummimatte|Gummimatte]] eingeschränkt sein oder automatisch geändert werden.
      </p>
    `
  },

  {
    id: "tor:hoehe",
    title: "Höhe (Pflichtfeld)",
    shortTitle: "Höhe",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Gebt hier die Höhe des Tors ein. Die Höhe ist definiert als Abstand zwischen dem Boden und der Oberkante der Quertraverse.
      </p>
    `
  },

  {
    id: "tor:breite",
    title: "Breite (Pflichtfeld)",
    shortTitle: "Breite",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Gebt hier die Breite des Tors ein. Die Breite ist definiert von Außenkante zu Außenkante der Traversencorner in den oberen Ecken.
      </p>
    `
  },

  {
    id: "tor:hoehe_flaeche",
    title: "Höhe Fläche (optional)",
    shortTitle: "Höhe Fläche",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Wenn ihr eine Fläche (z. B. Plane oder Banner) am Tor befestigen möchtet, könnt ihr hier dieser Fläche eingeben.
        Bei der Berechnung wird nur die Windangriffsfläche aber nicht das Eigengewicht der Fläche berücksichtigt.
        Wenn ihr hier etwas eingebt, wird diese Fläche und eine Traverse an der Unterkante der Fläche automatisch erstellt.
      </p>
      <p>
        <b>Achtung:</b> Der eingegebene Wert muss niedriger als die Höhe des Tors sein.<br>
        <b>Achtung:</b> Durch das Spannen von Planen oder Bannern können zusätzliche Kräfte auf die Konstruktion wirken, die in der Berechnung nicht berücksichtigt werden.
      </p>
      <p>
        Wenn ihr keine Fläche befestigen möchtet, lasst das Feld einfach leer.
      </p>
    `
  },

  {
    id: "tor:anzahl_steher",
    title: "Anzahl Steher (Pflichtfeld)",
    shortTitle: "Anzahl Steher",
    pfad: ["app:konstruktionen", "tor:allgemein"],
    body: `
      <p>
        Gebt hier die Anzahl der Steher des Tors an. Mindestens zwei Steher sind erforderlich. 
        Wird die Anzahl der Steher erhöht, werden diese gleichmäßig auf die Breite des Tors verteilt.
      </p>
    `
  }
];