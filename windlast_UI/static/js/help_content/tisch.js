// static/js/help_content/tisch.js

export const TISCH_HELP_PAGES = [
  {
    id: "tisch:allgemein",
    title: "Traversentisch",
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
    `
  },

  {
    id: "tisch:traverse",
    title: "Traverse (Pflichtfeld)",
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
    body: `
      <p>
        Gebt hier die Höhe des Tisches ein. Die Höhe ist definiert als Abstand zwischen dem Boden und der Oberkante der Quertraversen.
      </p>
    `
  },

  {
    id: "tisch:breite",
    title: "Breite (Pflichtfeld)",
    body: `
      <p>
        Gebt hier die Breite des Tisches ein. Die Breite ist definiert von Außenkante zu Außenkante der Traversencorner in den oberen Ecken.
      </p>
    `
  },

  {
    id: "tisch:tiefe",
    title: "Tiefe (Pflichtfeld)",
    body: `
      <p>
        Gebt hier die Tiefe des Tisches ein. Die Tiefe ist definiert von Außenkante zu Außenkante der Traversencorner in den oberen Ecken.
      </p>
    `
  }
];