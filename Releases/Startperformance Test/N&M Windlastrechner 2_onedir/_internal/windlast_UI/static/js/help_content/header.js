// static/js/help_content/header.js

export const HEADER_HELP_PAGES = [
  {
    id: "header:aufstelldauer",
    title: "Aufstelldauer (optional)",
    shortTitle: "Aufstelldauer",
    body: `
      <p>
        Hier kann die geplante Aufstelldauer der Konstruktion angegeben werden. Die Aufstelldauer hat bei der Berechnung nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4]]
        Einfluss auf eine Mögliche Abminderung der Staudrücke. Kürzere Aufstelldauern führen zu höheren Abminderungen.
      </p>
      <p>
        <b>Diese Abminderung ist aber für fliegende Bauten bzw. allgemein Bauten, die jederzeit errichtet und demontiert werden können, explizit nicht zulässig.</b>
      </p>
    `
  },

  {
    id: "header:windzone",
    title: "Windzone (Pflichtfeld)",
    shortTitle: "Windzone",
    body: `
      <p>
        Hier wird die Windzone des Aufstellortes der Konstruktion ausgewählt. Die Windzone hat bei der Berechnung nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4]]
        Einfluss auf die verwendeten Staudrücke. Eine Karte mit den Windzonen in Deutschland ist im nationalen Anhand der DIN EN 1991-1-4 abgedruckt oder unten angehängt.
        Beim [[ext:https://www.dibt.de/de/wir-bieten/technische-baubestimmungen|Deutschen Institut für Bautechnik]] ist außerdem eine Excel-Liste mit der
        [[ext:https://www.dibt.de/fileadmin/dibt-website/Dokumente/Referat/P5/Technische_Bestimmungen/Windzonen_nach_Verwaltungsgrenzen.xlsx|Zuordnung der Windzonen nach Verwaltungsgrenzen der Länder]]
        zu finden.
      </p>
      <p>
        Mit &bdquo;Küste&ldquo; meint die Norm einen 5km breiten Streifen entlang der Küste.
      </p>
      <help-img
        path="/static/media/Windzonenkarte.png"
        link="https://de.wikipedia.org/wiki/Windlast#/media/Datei:Windzonenkarte.png"
        date="2025-12-23"
        alt="Windzonenkarte Deutschland"
        source-label="Wikipedia"
        width="600px"
      ></help-img>
    `
  }
];