// static/js/help_content/norminfo.js

export const NORM_HELP_PAGES = [
  {
    id: "norm:allgemein",
    title: "Normen",
    body: `
      <p>
       Die Software unterstützt die Berechnung nach folgenden Normen:
      </p>
      <p>
        [[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06 – Fliegende Bauten und Anlagen für Veranstaltungsplätze und Vergnügungsparks – Sicherheit]]
      </p>
      <ul>
        <li>Baurechtlich eingeführt für fliegende Bauten</li>
        <li>Liefert Staudrücke und Verfahren für Standsicherheitsnachweis</li>
        <li>Greift bei der Windkraftberechnung auf DIN EN 1991-1-4 zurück</li>
      </ul>
      <p>
        [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08 – Event-Strukturen – Sicherheit]]
      </p>
      <ul>
        <li>Nicht baurechtlich eingeführt</li>
        <li>Liefert Staudrücke und Verfahren für Standsicherheitsnachweis</li>
        <li>Greift bei der Windkraftberechnung auf DIN EN 1991-1-4 zurück</li>
      </ul>
      <p>
        [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010 – Eurocode 1, Windlasten]]
      </p>
      <ul>
        <li>TODO</li>
      </ul>
    `
  },
  {
    id: "norm:DIN_EN_13814_2005",
    normKey: "EN_13814_2005",
    title: "DIN EN 13814:2005-06 – Fliegende Bauten und Anlagen für Veranstaltungsplätze und Vergnügungsparks – Sicherheit",
    shortTitle: "DIN EN 13814:2005-06",
    stand: "19.11.2025",
    pfad: ["norm:allgemein"],
    body: `
      <p>
        Diese Norm regelt unter anderem die Windlastberechnung für fliegende Bauten. Dabei gibt sie Staudrücke und ein Verfahren zum Standsicherheitsnachweis vor, verweist zur Berechnung der Windkräfte jedoch auf die DIN EN 1991-1-4.
        Sie ist in Deutschland baurechtlich eingeführt für die Berechnung von fliegenden Bauten. Neuere Versionen der Norm sind veröffentlicht, aber noch nicht baurechtlich eingeführt.
        Staudrücke werden für Konstruktionen mit einer Höhe bis zu 50m vereinfacht in einer Tabelle vorgegeben. Daher ist die Norm nur unter bestimmten Voraussetzungen anwendbar:
      </p>
      <ul>
        <li>Referenzwindgeschwindigkeit höchstens 28 m/s (Achtung bei Windzone 4 und in Küstengebieten)</li>
        <li>Ab einer Windgeschwindigkeit von 25 m/s in 10 m Höhe muss die Anlage geschützt und angemessen verstärkt werden</li>
      </ul>
      <p>
        Für komplexere Bauwerke, höhere Windgeschwindigkeiten oder exponierte Standorte ist die Anwendung der DIN EN 13814:2005-06 nicht vorgesehen. Hier sind gesonderte Nachweise nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4]] erforderlich.
      </p>
      <p>
        <b>Diese Software liefert einen solchen Nachweis auch bei der Berechnung nach DIN EN 1991-1-4 nicht. Wendet euch hier an einen Statiker.</b>
      </p>
      <p>
        Es besteht die Möglichkeit, die angenommenen Staudrücke abzumindern, wenn bestimmte Schutzmaßnahmen möglich sind. Bei der Hauptberechnung werden diese Abminderungen nicht berücksichtigt.
        Bei nicht gewährleisteter Standsicherheit werden die Abminderungen automatisch in einer zweiten Berechnung berücksichtigt. Details hierzu findet ihr [[norm:DIN_EN_13814_2005:IN_BETRIEB|hier]].
      </p>
    `
  },
  {
    id: "norm:DIN_EN_13814_2005:IN_BETRIEB",
    normKey: "EN_13814_2005",
    szenario: "IN_BETRIEB",
    title: "DIN EN 13814:2005-06 – Berücksichtigung von möglichen Schutzmaßnahmen",
    shortTitle: "Schutzmaßnahmen",
    stand: "19.11.2025",
    pfad: ["norm:allgemein","norm:DIN_EN_13814_2005"],
    body: `
      <p>
        Bei der Berechnung nach [[norm:DIN_EN_13814_2005|DIN EN 13814:2005-06]] können Abminderungen der Staudrücke berücksichtigt werden, wenn bestimmte Schutzmaßnahmen möglich sind. Bei der Berechnung &bdquo;mit Schutzmaßnahmen&ldquo; wurden diese Abminderungen berücksichtigt.
        Sollen die hier aufgelisteten Werte verwendet werden, müssen ab einer Windgeschwindigkeit von 15 m/s Schutzmaßnahmen getroffen werden.
        In unseren Bereich sind zum Beispiel folgende Schutzmaßnahmen möglich:
      </p>
      <ul>
        <li>Abnehmen von Planen oder anderen großen Windangriffsflächen</li>
        <li>Evakuierung der Konstruktion und der umliegenden Bereiche</li>
      </ul>
      <p>
        Die Schutzmaßnahmen müssen vorher definiert werden und wir müssen sicherstellen, dass diese Maßnahmen auch tatsächlich umgesetzt werden.
        <b>Andernfalls dürfen die abgeminderten Staudrücke nicht verwendet werden.</b>
      </p>
      <p>
        Wird als Schutzmaßnahme die Konstruktion verändert (z.&nbsp;B. Abnehmen von Planen), muss für die Konstruktion in diesem Zustand ebenfalls ein Standsicherheitsnachweis geführt werden.
        <b>Dieser Nachweis wird von dieser Software nicht automatisch geführt.</b>
      </p>
    `
  },
  {
    id: "norm:DIN_EN_17879_2024",
    normKey: "EN_17879_2024",
    szenario: "IN_BETRIEB",
    title: "DIN EN 17879:2024-08 – Event-Strukturen – Sicherheit",
    shortTitle: "DIN EN 17879:2024-08",
    stand: "19.11.2025",
    pfad: ["norm:allgemein"],
    body: `
      <p>
        Diese Norm regelt unter anderem die Windlastberechnung für Event-Strukturen, unabhängig von der baurechtlichen Einordnung der Strukturen.
        Dabei gibt sie Staudrücke und ein Verfahren zum Standsicherheitsnachweis vor, verweist zur Berechnung der Windkräfte jedoch auf die DIN EN 1991-1-4.
        Sie ist in Deutschland allerdings <b>nicht baurechtlich eingeführt.</b>
        Staudrücke werden entweder nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4]] unter Berücksichtigung eines Wahrscheinlichkeitsfaktors von 0,85 oder vereinfacht mithilfe einer Tabelle ermittelt.
        Diese Software verwendet die tabellarische Methode, weshalb die Maximalhöhe der Konstruktionen auf 30m begrenzt ist.
      </p>
      <p>
        Für komplexere Bauwerke oder exponierte Standorte sind gesonderte Nachweise nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4]] erforderlich.
      </p>
      <p>
        <b>Diese Software liefert einen solchen Nachweis auch bei der Berechnung nach DIN EN 1991-1-4 nicht. Wendet euch hier an einen Statiker.</b>
      </p>
      <p>
        Es besteht die Möglichkeit, die angenommenen Staudrücke abzumindern, wenn bestimmte Schutzmaßnahmen möglich sind. Bei der Hauptberechnung werden diese Abminderungen nicht berücksichtigt.
        Bei nicht gewährleisteter Standsicherheit werden die Abminderungen automatisch in einer zweiten Berechnung berücksichtigt. Details hierzu findet ihr [[norm:DIN_EN_17879_2024:IN_BETRIEB|hier]].
      </p>
    `
  },
  {
    id: "norm:DIN_EN_17879_2024:IN_BETRIEB",
    normKey: "EN_17879_2024",
    szenario: "IN_BETRIEB",
    title: "DIN EN 17879:2024-08 – Berücksichtigung von möglichen Schutzmaßnahmen",
    shortTitle: "Schutzmaßnahmen",
    stand: "19.11.2025",
    pfad: ["norm:allgemein","norm:DIN_EN_17879_2024"],
    body: `
      <p>
        Bei der Berechnung nach [[norm:DIN_EN_17879_2024|DIN EN 17879:2024-08]] können Abminderungen der Staudrücke berücksichtigt werden, wenn bestimmte Schutzmaßnahmen möglich sind. Bei der Berechnung &bdquo;mit Schutzmaßnahmen&ldquo; wurden diese Abminderungen berücksichtigt.
        Sollen die hier aufgelisteten Werte verwendet werden, müssen vor Überschreiten der Windgeschwindigkeit von 20 m/s gemessen in 10m Höhe Schutzmaßnahmen getroffen werden.
        In unseren Bereich sind zum Beispiel folgende Schutzmaßnahmen möglich:
      </p>
      <ul>
        <li>Abnehmen von Planen oder anderen großen Windangriffsflächen</li>
        <li>Evakuierung der Konstruktion und der umliegenden Bereiche</li>
      </ul>
      <p>
        Die Schutzmaßnahmen müssen vorher definiert werden und wir müssen sicherstellen, dass diese Maßnahmen auch tatsächlich umgesetzt werden.
        <b>Andernfalls dürfen die abgeminderten Staudrücke nicht verwendet werden.</b>
      </p>
      <p>
        Wird als Schutzmaßnahme die Konstruktion verändert (z.&nbsp;B. Abnehmen von Planen), muss für die Konstruktion in diesem Zustand ebenfalls ein Standsicherheitsnachweis geführt werden.
        <b>Dieser Nachweis wird von dieser Software nicht automatisch geführt.</b>
      </p>
    `
  },
  {
    id: "norm:DIN_EN_1991_1_4_2010",
    normKey: "EN_1991_1_4_2010",
    title: "DIN EN 1991-1-4:2010 – Eurocode 1, Windlasten",
    shortTitle: "DIN EN 1991-1-4:2010",
    pfad: ["norm:allgemein"],
    body: `
      <p>
        TODO: Beschreibung der Norm DIN EN 1991-1-4
      </p>
    `
  }
];
