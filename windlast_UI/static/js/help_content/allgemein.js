// static/js/help_content/allgemein.js
// Nur Content – keine Logik, keine Importe.

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
      <p>Hier beantworten wir die typischen Fragen.</p>
      <p>Für Details zu Normen siehe [[app:start]].</p>
    `
  }
];
