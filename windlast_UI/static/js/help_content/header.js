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
      <p>Hier wird die Windzone des Aufstellortes der Konstruktion ausgewählt. Die Windzone hat bei der Berechnung nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4]]
      Einfluss auf die verwendeten Staudrücke. Eine Karte mit den Windzonen in Deutschland ist im nationalen Anhand der DIN EN 1991-1-4 abgedruckt oder online zu finden.
      Im deutschen Binnenland sind meist nur Windzone 1 und 2 relevant, in Norddeutschland – insbesondere in Küstennähe – sind Windzone 3 oder 4 möglich.</p>
    `
  }
];