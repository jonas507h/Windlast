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
        [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010 – Eurocode 1: Einwirkungen auf Tragwerke – Teil 1-4: Windlasten]]
      </p>
      <ul>
        <li>Baurechtlich eingeführt</li>
        <li>Liefert Staudrücke und Vefahren zur Berechnung von Windkräften auf Bauteile und Bauwerkskomponenten aller Art</li>
        <li>Greift beim Standsicherheitsnachweis auf die Vefahren nach DIN EN 13814 bzw. DIN EN 17879 zurück</li>
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
    title: "DIN EN 1991-1-4:2010-12 – Eurocode 1: Einwirkungen auf Tragwerke – Teil 1-4: Windlasten",
    shortTitle: "DIN EN 1991-1-4:2010-12",
    stand: "10.12.2025",
    pfad: ["norm:allgemein"],
    body: `
      <p>
        Diese Norm regelt die Windlastberechnung für Bauwerke aller Art. Neben verfahren zur Berechnung der Staudrücke auf Bauwerke enthält sie auch Verfahren zur Ermittlung von Windkräften auf Bauteile und Bauwerkskomponenten.
        Bei der Anwendung der Norm in Deutschland ist der nationale Anhang zu beachten. Baurechtlich eingeführt ist sowohl die Norm als auch der nationale Anhang in der Fassung von Dezember 2010 (DIN EN 1991-1-4/NA:2010-12).
        Die aktuelle Fassung des nationalen Anhangs von August 2024 ist noch nicht baurechtlich eingeführt. Für die in dieser Software unterstützten Berechnungen sind jedoch keine Unterschiede zwischen den Fassungen relevant.
      </p>
      <p>
        Diese Software nutzt für die Staudruckermittlung nicht das vollständige Verfahren der Norm, sondern bedient sich an den im nationalen Anhang angegebenen vereinfachten Geschwindigkeitsdrücken.
        Daher ist die Bauwerkshöhe auf 25m begrenzt und <b>an exponierten Standorten oder für komplexe Bauwerke sind gesonderte Nachweise erforderlich.</b>
        Im Gegensatz zu den anderen Normen ist für die Staudruckermittlung hier eine Angabe der [[header:windzone|Windzone]] erforderlich.
      </p>
      <p>
        Staudrücke nach DIN EN 1991-1-4 sind im Vergleich zu den anderen Normen in der Regel deutlich höher, da hier keine Abminderungen aufgrund von kurzen Aufstelldauern oder möglichen Schutzmaßnahmen berücksichtigt werden.
        Daher sind die Ergebnisse der Berechnung nach DIN EN 1991-1-4 konservativer als bei den anderen Normen.
        Der nationale Anhang beschreibt zwar die Möglichkeit, für kurze Aufstelldauern und mit möglichen Sicherungsmaßnahmen die Staudrücke abzumindern, jedoch dürfen diese Abminderungen für unsere Einsatzzwecke nicht ohne Weiteres angewendet werden.
        Diese Software kann diese Abminderungen aber berücksichtigen. Sobald ihr eine [[header:aufstelldauer|Aufstelldauer]] eingebt, werden die Abminderungen automatisch auch in der Hauptberechnung berücksichtigt.
        <b>Bevor ihr eine Aufstelldauer eingebt oder Sicherungsmaßnahmen bei der DIN EN 1991-1-4 berücksichtigt, lest euch unbedingt den [[norm:DIN_EN_1991_1_4_2010:abminderungen|entsprechenden Abschnitt]] dazu durch.</b>
      </p>
      <p>
        Bei der Windkraftermittlung kommen in dieser Software drei verschiedene Verfahren zur Anwendung, je nach Art des Bauteils:
      </p>
      <ul>
        <li>Für Flächen (z.&nbsp;B. Planen, Banner) wird das Verfahren für freistehende Wände oder Anzeigetafeln verwendet (vgl. DIN EN 1991-1-4:2010-12, Abschnitt 7.4).</li>
        <li>Für Rohre/Pipes wird das Verfahren für Kreiszylinder verwendet (vgl. DIN EN 1991-1-4:2010-12, Abschnitt 7.9).</li>
        <li>Für Traversen wird das Verfahren für Fachwerke verwendet (vgl. DIN EN 1991-1-4:2010-12, Abschnitt 7.11).</li>
      </ul>
      <p>
        Da die DIN EN 1991-1-4 keine Vorgaben für einen Standsicherheitsnachweis macht, werden die in den [[norm:allgemein|anderen Normen]] beschriebenen Verfahren verwendet.
      </p>
    `
  },
  {
    id: "norm:DIN_EN_1991_1_4_2010:abminderungen",
    title: "DIN EN 1991-1-4:2010-12 – Abminderung von Staudrücken",
    shortTitle: "Abminderung von Staudrücken",
    stand: "10.12.2025",
    pfad: ["norm:allgemein", "norm:DIN_EN_1991_1_4_2010"],
    body: `
      <p>
        Der nationale Anhang zur DIN EN 1991-1-4 beschreibt die Möglichkeit, bei kurzen Aufstelldauern bis zu 24 Monaten Staudrücke abzumindern (vgl. DIN EN 1991-1-4/NA:2010-12, Abschnitt NA.B.5).
        <b>In unseren Anwendungsfällen ist diese Abminderung meist jedeoch nicht zulässig:</b>
      </p>
      <p>
        <i>&bdquo;Bei Bauten, die jederzeit errichtet und demontiert werden können, z.B. fliegende Bauten und Gerüste, darf diese Abminderung nicht angewendet werden, es sei denn dies wird in Fachnormen anders geregelt&ldquo;</i>
      </p>
      <p>
        Dennoch kann diese Software die Abminderungen berücksichtigen. Sobald ihr eine [[header:aufstelldauer|Aufstelldauer]] eingebt, werden die Abminderungen automatisch auch in der Hauptberechnung berücksichtigt.
        Auch bei den Berechnungen mit Sicherungsmaßnahmen sind bereits diese Abminderungen berücksichtigt. Wenn ihr also auf der sicheren Seite sein wollt, lasst das Feld für die Aufstelldauer einfach leer.
      </p>
      <p>
        Die Abminderungen sind zum einen von der Aufstelldauer und zum andern von möglichen Sicherungsmaßnahmen abhängig. Bei der Aufstelldauer wird unterschieden zwischen Dauern bis zu 3 Tagen, bis zu 3 Monaten von Mai bis August,
        bis zu 12 Monaten und bis zu 24 Monaten.
        Bei den Sicherungsmaßnahmen wird unterschieden zwischen [[norm:DIN_EN_1991_1_4_2010:SCHUETZEND|schützenden]] und [[norm:DIN_EN_1991_1_4_2010:VERSTAERKEND|verstärkenden]] Maßnahmen. Schützende Maßnahmen sind zum Beispiel das Abnehmen von Planen oder die Evakuierung der Konstruktion und der umliegenden Bereiche.
        Verstärkende Maßnahmen sind zum Beispiel das Anbringen von zusätzlichen Abspannungen.
      </p>
    `
  },
  {
    id: "norm:DIN_EN_1991_1_4_2010:SCHUETZEND",
    normKey: "EN_1991_1_4_2010:SCHUETZEND",
    title: "DIN EN 1991-1-4:2010-12 – Berücksichtigung schützender Sicherungsmaßnahmen",
    shortTitle: "Schützende Sicherungsmaßnahmen",
    stand: "10.12.2025",
    pfad: ["norm:allgemein", "norm:DIN_EN_1991_1_4_2010"],
    body: `
      <p>
        Bei der Berechnung nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]] können Abminderungen der Staudrücke berücksichtigt werden, wenn bestimmte Sicherungsmaßnahmen möglich sind.
        Bei der Berechnung &bdquo;mit schützenden Sicherungsmaßnahmen&ldquo; wurden diese Abminderungen berücksichtigt. <b>Diese Abminderungen sind in unserem Bereich meist nicht zulässig.</b> Mehr dazu im entsprechenden Abschnitt unten.<br>
        Sollen die hier aufgelisteten Werte verwendet werden, muss die Wetterlage ausreichend genau beobachtet werden und vor Aufkommen eines Sturms die Sicherungsmaßnahmen umgesetzt sein.
        In unseren Bereich sind zum Beispiel folgende schützende Sicherungsmaßnahmen möglich:
      </p>
      <ul>
        <li>Abnehmen von Planen oder anderen großen Windangriffsflächen</li>
        <li>Evakuierung der Konstruktion und der umliegenden Bereiche</li>
      </ul>
      <p>
        Die Sicherungsmaßnahmen müssen vorher definiert werden und wir müssen sicherstellen, dass diese Maßnahmen auch tatsächlich umgesetzt werden.
        <b>Andernfalls dürfen die abgeminderten Staudrücke nicht verwendet werden.</b>
      </p>
      <p>
        Wird als Sicherungsmaßnahme die Konstruktion verändert (z.&nbsp;B. Abnehmen von Planen), muss für die Konstruktion in diesem Zustand ebenfalls ein Standsicherheitsnachweis geführt werden.
        <b>Dieser Nachweis wird von dieser Software nicht automatisch geführt.</b>
      </p>
      <help-include page="norm:DIN_EN_1991_1_4_2010:abminderungen" auto-level="true"></help-include>
    `
  },
  {
    id: "norm:DIN_EN_1991_1_4_2010:VERSTAERKEND",
    normKey: "EN_1991_1_4_2010:VERSTAERKEND",
    title: "DIN EN 1991-1-4:2010-12 – Berücksichtigung verstärkender Sicherungsmaßnahmen",
    shortTitle: "Verstärkende Sicherungsmaßnahmen",
    stand: "10.12.2025",
    pfad: ["norm:allgemein", "norm:DIN_EN_1991_1_4_2010"],
    body: `
      <p>
        Bei der Berechnung nach [[norm:DIN_EN_1991_1_4_2010|DIN EN 1991-1-4:2010-12]] können Abminderungen der Staudrücke berücksichtigt werden, wenn bestimmte Sicherungsmaßnahmen möglich sind.
        Bei der Berechnung &bdquo;mit verstärkenden Sicherungsmaßnahmen&ldquo; wurden diese Abminderungen berücksichtigt. <b>Diese Abminderungen sind in unserem Bereich meist nicht zulässig.</b> Mehr dazu im entsprechenden Abschnitt unten.<br>
        Sollen die hier aufgelisteten Werte verwendet werden, muss die Wetterlage ausreichend genau beobachtet werden und vor Aufkommen eines Sturms die Sicherungsmaßnahmen umgesetzt sein.
        In unseren Bereich ist als verstärkende Sicherungsmaßnahme zum Beispiel das Anbringen von zusätzlichen Abspannungen möglich.
      </p>
      <p>
        Die Sicherungsmaßnahmen müssen vorher definiert werden und wir müssen sicherstellen, dass diese Maßnahmen auch tatsächlich umgesetzt werden.
        <b>Andernfalls dürfen die abgeminderten Staudrücke nicht verwendet werden.</b>
      </p>
      <p>
        Wird als Sicherungsmaßnahme die Konstruktion verändert (z.&nbsp;B. Abnehmen von Planen), muss für die Konstruktion in diesem Zustand ebenfalls ein Standsicherheitsnachweis geführt werden.
        <b>Dieser Nachweis wird von dieser Software nicht automatisch geführt.</b>
      </p>
      <help-include page="norm:DIN_EN_1991_1_4_2010:abminderungen" auto-level="true"></help-include>
    `
  },
];
