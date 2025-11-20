// static/js/help_content/tor.js

export const TOR_HELP_PAGES = [
  {
    id: "tor:allgemein",
    title: "Traversentor",
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
      <help-include page="tor:höhe" auto-level="true"></help-include>
      <help-include page="tor:breite" auto-level="true"></help-include>
    `
  },

  {
    id: "tor:traverse",
    title: "Traverse (Pflichtfeld)",
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
    body: `
      <p>
        Wählt hier aus unseren Pool-Bodenplatten die entsprechende Bodenplatte aus. Die Auswahl beeinflusst alle in der Konstruktion verwendeten Bodenplatten.
        Bei der Berechnung werden Größe und Geometrie, Gewicht und Material der Bodenplatten berücksichtigt.
      </p>
    `
  },

  {
    id: "tor:gummimatte",
    title: "Gummimatte (Pflichtfeld)",
    body: `
      <p>
        Wählt hier aus, ob ihr Gummimatten unter den Bodenplatten verwendet. Gummimatten erhöhen in der Regel den Reibwert zwischen Bodenplatte und Untergrund
        und können sich positiv auf die Gleitsicherheit der Konstruktion auswirken.
      </p>
      <p>
        <b>Achtung:</b> Da in den zugrunde gelegten Normen (DIN EN 13814:2005-06 und DIN EN 17879:2024-08) nur Reibwerte für Gummi in Kombination mit Holz, Stahl oder Beton angegeben sind, führt eine andere Auswahl im [[tor:untergrund|Untergrund-Feld]]
        zu einem Fehler in der Berechnung.
      </p>
    `
  },

  {
    id: "tor:untergrund",
    title: "Untergrund (Pflichtfeld)",
    body: `
      <p>
        Wählt hier den Untergrund aus, auf dem die Konstruktion steht. Der Untergrund beeinflusst den Reibwert zwischen Bodenplatte und Untergrund. Dieser wird anhand der
        DIN EN 13814:2005-06 bzw. DIN EN 17879:2024-08 automatisch bestimmt.
      </p>
      <p>
        <b>Achtung:</b> Bei Verwendung von Gummimatten unter den Bodenplatten (siehe [[tor:gummimatte|Gummimatte-Feld]]) sind nur die Untergründe Holz, Stahl oder Beton zulässig.
        Ansonsten führt dies zu einem Fehler in der Berechnung.
      </p>
    `
  },

  {
    id: "tor:höhe",
    title: "Höhe (Pflichtfeld)",
    body: `
      <p>
        Gebt hier die Höhe des Tors ein. Die Höhe ist definiert als Abstand zwischen dem Boden und der Oberkante der Quertraverse.
      </p>
    `
  },

  {
    id: "tor:breite",
    title: "Breite (Pflichtfeld)",
    body: `
      <p>
        Gebt hier die Breite des Tors ein. Die Breite ist definiert von Außenkante zu Außenkante der Traversencorner in den oberen Ecken.
      </p>
    `
  }
];