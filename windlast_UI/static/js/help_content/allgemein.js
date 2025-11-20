// static/js/help_content/allgemein.js

export const GENERAL_HELP_PAGES = [
  {
    id: "app:start",
    title: "Hilfe – Übersicht",
    body: `
      <p>Willkommen in der Hilfe des Windlastrechners.</p>

      <h4>Häufige Themen</h4>
      <ul>
        <li><a href="#help:norm:DIN_EN_13814_2005">DIN EN 13814:2005-06 – Fliegende Bauten</a></li>
        <li><a href="#help:norm:DIN_EN_17879_2024">DIN EN 17879:2024-08 – Event-Strukturen</a></li>
        <li><a href="#help:norm:DIN_EN_1991_1_4_2010">DIN EN 1991-1-4:2010-12 – Eurocode 1</a></li>
      </ul>

      <h4>Weitere Themen</h4>
      <ul>
        <li>[[app:bedienung|Bedienung des Programms]]</li>
        <li>[[app:faq|FAQ]]</li>
      </ul>
    `
  },

  {
    id: "app:bedienung",
    title: "Bedienung des Windlastrechners",
    body: `
      <p>
        Dieser Abschnitt erklärt die grundlegende Bedienung des Programms.
      </p>
      <p>
        Weitere Normen findest du z. B. unter [[norm:EN_13814_2005]].
      </p>
    `
  },

  {
    id: "app:faq",
    title: "FAQ – Häufige Fragen",
    body: `
      <p>Hier findest du häufige Fragen:</p>

      <faq question="Wie lese ich die Tabelle im Footer?">
        Die Spalten repräsentieren verschiedene Normen. Klicke auf die Spaltenüberschrift für Details.
      </faq>

      <faq question="Was bedeutet die rote Markierung?">
        Es bedeutet, dass die Sicherheit < 1.00 ist.<br>
        Details findest du unter [[norm:EN_1991_1_4_2010]].
      </faq>
    `
  },

  {
    id: "app:vorschau",
    title: "Vorschaufenster",
    body: `
      <p>
        Links neben den Eingabefeldern befindet sich ein Vorschaufenster, das die aktuellen Eingaben grafisch darstellt. Es aktualisiert sich automatisch bei jeder Änderung der Eingaben.
        Visualisiert werden die Geometrie aller Bauteile (wobei Rohre als Linien dargestellt werden), deren Lage und Ausrichtung im Raum, die realen Abmessungen sowie die rechts eingegebenen Maße.
      </p>
      <p>
      Die Vorschau ist dreidimensional und unterstützt die Interaktion mit der Maus:
      </p>
      <ul>
        <li><b>Mausrad:</b> Zoom</li>
        <li><b>Linke Maustaste + Ziehen:</b> Rotation</li>
        <li><b>Rechte Maustaste + Ziehen:</b> Verschiebung</li>
      </ul>
      <p>
        Die Vorschau spiegelt 1:1 die geometrischen Ausgangsdaten der Berechnung wieder. Entspricht die Vorschau nicht der Realität, entspricht auch die Berechnung nicht der Realität.
      </p>
    `
  },

  {
    id: "app:konstruktionen",
    title: "Konstruktionen",
    body: `
      <p>
        Der Windlasterechner unterstützt verschiedene, einfache Konstruktionstyten. Aktuell werden folgende Konstruktionen unterstützt:
      </p>
      <ul>
        <li>[[tor:allgemein|Traversentor]]</li>
        <li>[[steher:allgemein|Traversensteher mit Querpipe]]</li>
        <li>[[tisch:allgemein|Traversentisch]]</li>
      </ul>
    `
  }
];
