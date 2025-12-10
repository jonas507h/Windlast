// static/js/help_content/tisch.js

export const TISCH_HELP_PAGES = [
  {
    id: "tisch:allgemein",
    title: "Traversentisch",
    pfad: ["app:konstruktionen"],
    body: `
      <p>
        Ist die Konstruktion &bdquo;Tisch&ldquo; ausgewählt, kann ein einfacher Traversentisch mit vier Füßen berechnet werden.
        Berechnet wird nur die reine Traversenkonstruktion. <b>Angebaute Technik (z. B. Lautsprecher, Scheinwerfer o. Ä.), Deko, Planen usw. können aktuell nicht berechnet werden.</b>
      </p>
      <p>
        Im [[app:vorschau|Vorschaufenster]] links werden die aktuellen Eingaben grafisch dargestellt. Rechts können folgende Eingaben gemacht werden:
      </p>

      <help-include page="tisch:traverse" auto-level="true"></help-include>
      <help-include page="tisch:bodenplatte" auto-level="true"></help-include>
      <help-include page="tisch:gummimatte" auto-level="true"></help-include>
      <help-include page="tisch:untergrund" auto-level="true"></help-include>
      <help-include page="tisch:hoehe" auto-level="true"></help-include>
      <help-include page="tisch:breite" auto-level="true"></help-include>
      <help-include page="tisch:tiefe" auto-level="true"></help-include>
      <help-include page="tisch:hoehe_flaeche" auto-level="true"></help-include>
    `
  },

  {
    id: "tisch:traverse",
    title: "Traverse (Pflichtfeld)",
    shortTitle: "Traverse",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Traversen die entsprechende Traverse aus. Die Auswahl beeinflusst alle in der Konstruktion verwendeten Traversen.
        Bei der Berechnung werden sowohl die Eigengewichte als auch die Windangriffsflächen der Traversen berücksichtigt.
      </p>
    `
  },

  {
    id: "tisch:bodenplatte",
    title: "Bodenplatte (Pflichtfeld)",
    shortTitle: "Bodenplatte",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Bodenplatten die entsprechende Bodenplatte aus. Die Auswahl beeinflusst alle in der Konstruktion verwendeten Bodenplatten.
        Bei der Berechnung werden Größe und Geometrie, Gewicht und Material der Bodenplatten berücksichtigt.
      </p>
    `
  },

  {
    id: "tisch:gummimatte",
    title: "Gummimatte (Pflichtfeld)",
    shortTitle: "Gummimatte",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Wählt hier aus, ob ihr Gummimatten unter den Bodenplatten verwendet. Gummimatten erhöhen in der Regel den Reibwert zwischen Bodenplatte und Untergrund
        und können sich positiv auf die Gleitsicherheit der Konstruktion auswirken.
      </p>
      <p>
        <b>Achtung:</b> Da in den zugrunde gelegten Normen (DIN EN 13814:2005-06 und DIN EN 17879:2024-08) nur Reibwerte für Gummi in Kombination mit Holz, Stahl oder Beton angegeben sind,
        führt eine andere Auswahl im [[tisch:untergrund|Untergrund-Feld]] zu einem Fehler in der Berechnung.
      </p>
    `
  },

  {
    id: "tisch:untergrund",
    title: "Untergrund (Pflichtfeld)",
    shortTitle: "Untergrund",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Wählt hier den Untergrund aus, auf dem die Konstruktion steht. Der Untergrund beeinflusst den Reibwert zwischen Bodenplatte und Untergrund. Dieser wird anhand der
        DIN EN 13814:2005-06 bzw. DIN EN 17879:2024-08 automatisch bestimmt.
      </p>
      <p>
        <b>Achtung:</b> Bei Verwendung von Gummimatten unter den Bodenplatten (siehe [[tisch:gummimatte|Gummimatte-Feld]]) sind nur die Untergründe Holz, Stahl oder Beton zulässig.
        Ansonsten führt dies zu einem Fehler in der Berechnung.
      </p>
    `
  },

  {
    id: "tisch:hoehe",
    title: "Höhe (Pflichtfeld)",
    shortTitle: "Höhe",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Gebt hier die Höhe des Tisches ein. Die Höhe ist definiert als Abstand zwischen dem Boden und der Oberkante der Quertraversen.
      </p>
    `
  },

  {
    id: "tisch:breite",
    title: "Breite (Pflichtfeld)",
    shortTitle: "Breite",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Gebt hier die Breite des Tisches ein. Die Breite ist definiert von Außenkante zu Außenkante der Traversencorner in den oberen Ecken.
      </p>
    `
  },

  {
    id: "tisch:tiefe",
    title: "Tiefe (Pflichtfeld)",
    shortTitle: "Tiefe",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Gebt hier die Tiefe des Tisches ein. Die Tiefe ist definiert von Außenkante zu Außenkante der Traversencorner in den oberen Ecken.
      </p>
    `
  },

  {
    id: "tisch:hoehe_flaeche",
    title: "Höhe Fläche (optional)",
    shortTitle: "Höhe Fläche",
    pfad: ["app:konstruktionen", "tisch:allgemein"],
    body: `
      <p>
        Wenn ihr eine Fläche (z. B. Plane oder Banner) am Tisch befestigen möchtet, könnt ihr hier die Höhe dieser Fläche eingeben.
        Bei der Berechnung wird nur die Windangriffsfläche aber nicht das Eigengewicht der Fläche berücksichtigt.
        Wenn ihr hier etwas eingebt, wird diese Fläche und eine Traverse an der Unterkante der Fläche automatisch erstellt.
        Die Fläche kann nur an einer Seite des Tisches befestigt werden.
      </p>
      <p>
        <b>Achtung:</b> Der eingegebene Wert muss niedriger als die Höhe des Tisches sein.<br>
        <b>Achtung:</b> Durch das Spannen von Planen oder Bannern können zusätzliche Kräfte auf die Konstruktion wirken, die in der Berechnung nicht berücksichtigt werden.
      </p>
      <p>
        Wenn ihr keine Fläche befestigen möchtet, lasst das Feld einfach leer.
      </p>
    `
  },
];