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
        Einfluss auf die verwendeten Staudrücke. Eine Karte mit den Windzonen in Deutschland ist im nationalen Anhand der DIN EN 1991-1-4 abgedruckt oder online zu finden.
        Die [[ext:https://www.bauministerkonferenz.de|Bauministerkonferenz]] stellt außerdem eine Excel-Liste mit der
        [[ext:https://www.is-argebau.de/IndexSearch.aspx?method=get&File=bya892ba82y1b9bbba8a4a8yb9bb92b8y9ya8ayyb9y884b992a2a0a1aba4a1494b88yb8388514gsjsurtpizrrzhlllyojo|Zuordnung der Windzonen nach Verwaltungsgrenzen der Länder]]
        zur Verfügung.
      </p>
      <p>
        Mit &bdquo;Küste&ldquo; meint die Norm einen 5km breiten Streifen entlang der Küste.
      </p>
    `
  }
];