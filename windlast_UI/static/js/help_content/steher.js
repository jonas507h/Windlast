// static/js/help_content/steher.js

export const STEHER_HELP_PAGES = [
  {
    id: "steher:allgemein",
    title: "Traversensteher mit Querpipe",
    shortTitle: "Traversensteher",
    pfad: ["app:konstruktionen"],
    body: `
      <p>
        Ist die Konstruktion &bdquo;Steher&ldquo; ausgewählt, kann ein Traversensteher mit Querpipe berechnet werden.
        Berechnet wird nur die reine Traversenkonstruktion inkl. Pipe. <b>Angebaute Technik (z. B. Lautsprecher, Scheinwerfer o. Ä.), Deko, Planen usw. können aktuell nicht berechnet werden.</b>
      </p>
      <p>
        Im [[app:vorschau|Vorschaufenster]] links werden die aktuellen Eingaben grafisch dargestellt. Rechts können folgende Eingaben gemacht werden:
      </p>

      <help-include page="steher:traverse" auto-level="true"></help-include>
      <help-include page="steher:rohr" auto-level="true"></help-include>
      <help-include page="steher:bodenplatte" auto-level="true"></help-include>
      <help-include page="steher:gummimatte" auto-level="true"></help-include>
      <help-include page="steher:untergrund" auto-level="true"></help-include>
      <help-include page="steher:hoehe" auto-level="true"></help-include>
      <help-include page="steher:laenge_rohr" auto-level="true"></help-include>
      <help-include page="steher:hoehe_rohr" auto-level="true"></help-include>
      <help-include page="steher:hoehe_flaeche" auto-level="true"></help-include>
    `
  },

  {
    id: "steher:traverse",
    title: "Traverse (Pflichtfeld)",
    shortTitle: "Traverse",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Traversen die entsprechende Traverse aus. Die Auswahl beeinflusst die senkrechte Traverse.
        Bei der Berechnung werden sowohl das Eigengewicht als auch die Windangriffsflächen der Traverse berücksichtigt.
      </p>
    `
  },

  {
    id: "steher:rohr",
    title: "Rohr (Pflichtfeld)",
    shortTitle: "Rohr",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Rohren das entsprechende Rohr aus. Die Auswahl beeinflusst das Querrohr.
        Bei der Berechnung werden sowohl das Eigengewicht als auch die Windangriffsflächen des Rohrs berücksichtigt.
      </p>
    `
  },

  {
    id: "steher:bodenplatte",
    title: "Bodenplatte (Pflichtfeld)",
    shortTitle: "Bodenplatte",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Wählt hier aus unseren Pool-Bodenplatten die entsprechende Bodenplatte aus.
        Bei der Berechnung werden Größe und Geometrie, Gewicht und Material der Bodenplatten berücksichtigt.
      </p>
    `
  },

  {
    id: "steher:gummimatte",
    title: "Gummimatte (Pflichtfeld)",
    shortTitle: "Gummimatte",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Wählt hier aus, ob ihr Gummimatten unter der Bodenplatte verwendet. Gummimatten erhöhen in der Regel den Reibwert zwischen Bodenplatte und Untergrund
        und können sich positiv auf die Gleitsicherheit der Konstruktion auswirken.
      </p>
      <p>
        <b>Achtung:</b> Da in den zugrunde gelegten Normen (DIN EN 13814:2005-06 und DIN EN 17879:2024-08) nur Reibwerte für Gummi in Kombination mit Holz, Stahl oder Beton angegeben sind,
        führt eine andere Auswahl im [[steher:untergrund|Untergrund-Feld]] zu einem Fehler in der Berechnung.
      </p>
    `
  },

  {
    id: "steher:untergrund",
    title: "Untergrund (Pflichtfeld)",
    shortTitle: "Untergrund",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Wählt hier den Untergrund aus, auf dem die Konstruktion steht. Der Untergrund beeinflusst den Reibwert zwischen Bodenplatte und Untergrund. Dieser wird anhand der
        DIN EN 13814:2005-06 bzw. DIN EN 17879:2024-08 automatisch bestimmt.
      </p>
      <p>
        <b>Achtung:</b> Bei Verwendung von Gummimatten unter den Bodenplatten (siehe [[steher:gummimatte|Gummimatte-Feld]]) sind nur die Untergründe Holz, Stahl oder Beton zulässig.
        Ansonsten führt dies zu einem Fehler in der Berechnung.
      </p>
    `
  },

  {
    id: "steher:hoehe",
    title: "Höhe (Pflichtfeld)",
    shortTitle: "Höhe",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Gebt hier die Höhe des Stehers ein. Die Höhe ist definiert als Abstand zwischen dem Boden und der Oberkante der Traverse.
      </p>
    `
  },

  {
    id: "steher:laenge_rohr",
    title: "Länge Rohr (Pflichtfeld)",
    shortTitle: "Länge Rohr",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Gebt hier die Länge des Querrohrs ein.
      </p>
    `
  },

  {
    id: "steher:hoehe_rohr",
    title: "Höhe Rohr (Pflichtfeld)",
    shortTitle: "Höhe Rohr",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Gebt hier die Höhe des Querrohrs über dem Boden ein. Referenz ist die Mittelachse des Rohrs.
      </p>
      <p>
        <b>Achtung:</b> Die Höhe des Rohrs muss kleiner als die Gesamthöhe des Stehers sein.
      </p>
    `
  },

  {
    id: "steher:hoehe_flaeche",
    title: "Höhe Fläche (optional)",
    shortTitle: "Höhe Fläche",
    pfad: ["app:konstruktionen", "steher:allgemein"],
    body: `
      <p>
        Wenn ihr eine Fläche (z. B. Plane oder Banner) am Steher befestigen möchtet, könnt ihr hier die Höhe dieser Fläche eingeben.
        Bei der Berechnung wird nur die Windangriffsfläche aber nicht das Eigengewicht der Fläche berücksichtigt.
        Wenn ihr hier etwas eingebt, wird diese Fläche und ein Rohr an der Unterkante der Fläche automatisch erstellt.
      </p>
      <p>
        <b>Achtung:</b> Der eingegebene Wert muss niedriger als die Höhe des oberen Rohrs sein.<br>
        <b>Achtung:</b> Durch das Spannen von Planen oder Bannern können zusätzliche Kräfte auf die Konstruktion wirken, die in der Berechnung nicht berücksichtigt werden.
      </p>
      <p>
        Wenn ihr keine Fläche befestigen möchtet, lasst das Feld einfach leer.
      </p> 
    `
  },
];