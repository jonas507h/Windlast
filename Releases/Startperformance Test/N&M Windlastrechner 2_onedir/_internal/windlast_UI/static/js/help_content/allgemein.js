// static/js/help_content/allgemein.js

export const GENERAL_HELP_PAGES = [
  {
    id: "app:start",
    title: "Hilfe – Übersicht",
    shortTitle: "Übersicht",
    body: `
      <p>Willkommen in der Hilfe des Windlastrechners.</p>

      <h4>Wichtige Links</h4>
      <ul>
        <li>[[norm:allgemein|Normen]]</li>
        <li>[[app:bedienung|Bedienung des Programms]]</li>
        <li>[[app:konstruktionen|Konstruktionen]]</li>
        <li>[[ergebnisse:allgemein|Ergebnisse]]</li>
      </ul>

      <h4>Fehlermeldungen & FAQs</h4>
      <ul>
        <li>[[meldungen:haeufige_meldungen|Häufige Meldungen]]</li>
      </ul>
      <p>
        Fragen oder Feedback gerne an [[contact:jonas.schmid|Jonas Schmid]] oder das [[contact:tg-rigging|TG-Rigging]].<br>
        [[app:changelog|Changelog]]
      </p>
    `
  },
  //FAQ für später
  //<li>[[app:faq|FAQ]]</li>

  {
    id: "app:bedienung",
    title: "Bedienung des Windlastrechners",
    shortTitle: "Bedienung",
    body: `
      <p>
        In der Kopfzeile werden allgemeine Daten wie die [[header:aufstelldauer|Aufstelldauer]] und die [[header:windzone|Windzone]] eingegeben.
        Außerdem kann hier zwischen dunklem und hellem Design gewechselt und das hilfe Menü aufgerufen werden.
      </p>
      <p>
        In der Mitte wird die zu berechnende [[app:konstruktionen|Konstruktion]] ausgewählt und die entsprechenden Eingaben gemacht.
        Links wird die Konstruktion im [[app:vorschau|Vorschaufenster]] grafisch dargestellt. Rechts befinden sich die Eingabefelder für die Konstruktion und
        der Button zur Berechnung der Windlasten.
      </p>
      <p>
        Unten werden die [[ergebnisse:allgemein|Ergebnisse]] der Berechnung angezeigt. Hier können auch die Fenster für die [[meldungen:allgemein|Meldungen]]
        und die [[zwischenergebnis:allgemein|Zwischenergebnisse]] geöffnet werden.
      </p>
      <p>
        Überall im Programm sind kleine Fragezeichen-Buttons zu finden. Ein Klick darauf öffnet die zugehörige Hilfe-Seite.
      </p>
      <p>
        Das Programm rechnet parallel nach drei verschiedenen [[norm:allgemein|Normen]] mit verschiedenen Einsatzgebieten. Informiert euch vor der Nutzung,
        welche Norm für euren Anwendungsfall die richtige ist.
      </p>
    `
  },

  {
    id: "app:faq",
    title: "FAQ – Häufige Fragen",
    shortTitle: "FAQ",
    body: `
      <p>TODO: FAQ</p>
    `
  },

  {
    id: "app:vorschau",
    title: "Vorschaufenster",
    body: `
      <p>
        Links neben den Eingabefeldern befindet sich ein Vorschaufenster, das die aktuellen Eingaben grafisch darstellt. Es aktualisiert sich automatisch bei jeder Änderung der Eingaben.
        Visualisiert werden die Geometrie aller Bauteile (wobei Rohre als Linien dargestellt werden), deren Lage und Ausrichtung im Raum, die realen Abmessungen sowie die rechts eingegebenen Maße.<br>
        Bodenplatten werden gelb markiert, wenn unter ihnen Gummimatten verwendet werden.
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
        Die Vorschau spiegelt 1:1 die geometrischen Ausgangsdaten der Berechnung wieder. Was in der Vorschau nicht dargestellt wird, wird auch nicht berechnet.
      </p>
    `
  },

  {
    id: "app:konstruktionen",
    title: "Konstruktionen",
    body: `
      <p>
        Der Windlasterechner unterstützt verschiedene, einfache Konstruktionstypen. Bei allen Konstruktionen können auch größere Windangriffsflächen
        (z.B. für Banner oder Planen) berücksichtigt werden. Aktuell werden folgende Konstruktionen unterstützt:
      </p>
      <ul>
        <li>[[tor:allgemein|Traversentor]]</li>
        <li>[[steher:allgemein|Traversensteher mit Querpipe]]</li>
        <li>[[tisch:allgemein|Traversentisch]]</li>
      </ul>
      <p>
        Auf der linken Seite zeigt das [[app:vorschau|Vorschaufenster]] die Konstruktion und rechts können die entsprechenden Eingaben gemacht werden.
      </p>
    `
  },

  {
    id: "app:changelog",
    title: "Changelog",
    shortTitle: "Changelog",
    body: `
      <div id="help-changelog-content">
        <p>Lade Changelog …</p>
      </div>
    `
  }
];