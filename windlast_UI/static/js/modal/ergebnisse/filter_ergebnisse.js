export const FILTER_GROUPS = [
  {
    name: "label_filter",
    label: "Namens-Filter",
    filters: [
      {
        name: "abminderungsfaktor_schlankheit",
        label: "Abminderungsfaktor Schlankheit",
        fn: filterLabelIn([
          "math.abminderungsfaktor_schlankheit.label",
          "math.abminderungsfaktor_schlankheit_rohr.label"
        ]),
      },
      {
        name: "bezugsflaeche",
        label: "Bezugsfläche",
        fn: filterLabelIn([
          "math.bezugsflaeche.label",
          "math.bezugsflaeche_anzeigetafel.label",
          "math.bezugsflaeche_rohr.label",
          "math.bezugsflaeche_traverse.label",
          "math.bezugsflaeche_wand.label"
        ]),
      },
      {
        name: "eingeschlossene_flaeche",
        label: "Eingeschlossene Fläche",
        fn: filterLabelIn([
          "math.eingeschlossene_flaeche.label",
          "math.eingeschlossene_flaeche_traverse.label"
        ]),
      },
      {
        name: "gewichtskraft",
        label: "Gewichtskraft",
        fn: filterLabelIn([
          "math.gewichtskraft_bodenplatte.label",
          "math.gewichtskraft_rohr.label",
          "math.gewichtskraft_traverse.label",
        ]),
      },
      {
        name: "grundkraftbeiwert",
        label: "Grundkraftbeiwert",
        fn: filterLabelIn(["math.grundkraftbeiwert.label"]),
      },
      {
        name: "kraftbeiwert",
        label: "Kraftbeiwert",
        fn: filterLabelIn([
          "math.kraftbeiwert.label",
          "math.kraftbeiwert_anzeigetafel.label",
          "math.kraftbeiwert_rohr.label",
          "math.kraftbeiwert_traverse.label"
        ]),
      },
      {
        name: "nettodruckbeiwert",
        label: "Nettodruckbeiwert",
        fn: filterLabelIn(["math.nettodruckbeiwert_wand.label"]),
      },
      {
        name: "reibwert",
        label: "Reibwert",
        fn: filterLabelIn([
          "math.reibwert.label",
          "math.reibwert_bodenplatte.label"
        ]),
      },
      {
        name: "reynoldszahl",
        label: "Reynoldszahl",
        fn: filterLabelIn([
          "math.reynoldszahl.label",
          "math.reynoldszahl_rohr.label",
          "math.reynoldszahl_traverse.label"
        ]),
      },
      {
        name: "schlankheit",
        label: "Schlankheit",
        fn: filterLabelIn([
          "math.schlankheit.label",
          "math.schlankheit_rohr.label",
          "math.schlankheit_traverse.label"
        ]),
      },
      {
        name: "sicherheitsbeiwert",
        label: "Sicherheitsbeiwert",
        fn: filterLabelIn(["math.sicherheitsbeiwert.label"]),
      },
      {
        name: "staudruck",
        label: "Staudruck",
        fn: filterLabelIn([
          "math.staudruck.label",
          "math.staudruck_anzeigetafel.label",
          "math.staudruck_obergrenze.label"
        ]),
      },
      {
        name: "stroemungsgeschwindigkeit",
        label: "Strömungsgeschwindigkeit",
        fn: filterLabelIn(["math.stroemungsgeschwindigkeit.label"]),
      },
      {
        name: "voelligkeitsgrad",
        label: "Vollständigkeitsgrad",
        fn: filterLabelIn(["math.voelligkeitsgrad.label"]),
      },
      {
        name: "windkraft",
        label: "Windkraft",
        fn: filterLabelIn([
          "math.windkraft.label",
          "math.windkraft_anzeigetafel.label",
          "math.windkraft_rohr.label",
          "math.windkraft_traverse.label",
          "math.windkraft_wand.label",
          "math.windkraft_vektor.label",
          "math.windkraft_vektor_anzeigetafel.label",
          "math.windkraft_vektor_rohr.label",
          "math.windkraft_vektor_traverse.label",
          "math.windkraft_vektor_wand.label"
        ]),
      },
      {
        name: "normalkraft",
        label: "Normalkraft",
        fn: filterLabelIn([
          "math.abhebe_normalkraft_down_lastfall.label",
          "math.abhebe_normalkraft_up_lastfall.label",
          "math.abhebe_normalkraft_down_element.label",
          "math.abhebe_normalkraft_up_element.label",
          "math.abhebe_normalkraft_down_richtung.label",
          "math.abhebe_normalkraft_up_richtung.label",
          "math.gleit_normalkraft_down_lastfall.label",
          "math.gleit_normalkraft_up_lastfall.label",
          "math.gleit_normalkraft_effektiv_lastfall.label",
          "math.gleit_normalkraft_down_element.label",
          "math.gleit_normalkraft_up_element.label",
          "math.gleit_normalkraft_down_richtung.label",
          "math.gleit_normalkraft_up_richtung.label",
          "math.gleit_normalkraft_effektiv_richtung.label",
        ]),
      },
      {
        name: "horizontalkraft",
        label: "Horizontalkraft",
        fn: filterLabelIn([
          "math.gleit_horizontalkraft_lastfall.label",
          "math.gleit_horizontalkraft_betrag_lastfall.label",
          "math.gleit_horizontalkraft_element.label",
          "math.gleit_horizontalkraft_richtung.label",
        ]),
      },
      {
        name: "reibkraft",
        label: "Reibkraft",
        fn: filterLabelIn(["math.gleit_reibkraft_richtung.label"]),
      },
      {
        name: "kippmoment",
        label: "Kippmoment",
        fn: filterLabelIn([
          "math.kipp_kippmoment_lastfall.label",
          "math.kipp_kippmoment_element.label",
          "math.kipp_kippmoment_achse.label"
        ]),
      },
      {
        name: "standmoment",
        label: "Standmoment",
        fn: filterLabelIn([
          "math.kipp_standmoment_lastfall.label",
          "math.kipp_standmoment_element.label",
          "math.kipp_standmoment_achse.label"
        ]),
      },
      {
        name: "abhebesicherheit",
        label: "Abhebesicherheit",
        fn: filterLabelIn([
          "math.abhebe_sicherheit_richtung.label",
          "math.abhebe_sicherheit.label"
        ]),
      },
      {
        name: "gleitsicherheit",
        label: "Gleitsicherheit",
        fn: filterLabelIn([
          "math.gleit_sicherheit_richtung.label",
          "math.gleit_sicherheit.label"
        ]),
      },
      {
        name: "kippsicherheit",
        label: "Kippsicherheit",
        fn: filterLabelIn([
          "math.kipp_sicherheit_achse.label",
          "math.kipp_sicherheit_richtung.label",
          "math.kipp_sicherheit.label"
        ]),
      },
      {
        name: "ballastkraft",
        label: "Ballastkraft",
        fn: filterLabelIn([
          "math.abhebe_ballast_richtung.label",
          "math.gleit_ballast_richtung.label",
          "math.kipp_ballast_achse.label",
          "math.kipp_ballast_richtung.label"
        ]),
      },
      {
        name: "ballast",
        label: "Ballast",
        fn: filterLabelIn([
          "math.abhebe_ballast.label",
          "math.gleit_ballast.label",
          "math.kipp_ballast.label",
          "math.gesamt_ballast.label"
        ]),
      },
    ],
  },
  {
    name: "type_filter",
    label: "Typ-Filter",
    filters: [
      {
        name: "ergebnisse",
        label: "Ergebnisse",
        fn: filterType("ergebnis"),
      },
      {
        name: "meldungen",
        label: "Meldungen",
        fn: filterType("message"),
      },
    ],
  },
];

export function filterLabelIn(exakteCodes = []) {
  const codeSet = new Set(exakteCodes.map((v) => String(v).trim()));

  return {
    matchErgebnis: (ergebnis) => codeSet.has(String(ergebnis?.label ?? "").trim()),
    matchMessage: () => false,
  };
}

export function filterType(type) {
  return {
    matchErgebnis: () => type === "ergebnis",
    matchMessage: () => type === "message",
  };
}

export function applyErgebnisFilters(rootNode, activeFilters = []) {
  if (!activeFilters.length) return rootNode;

  const filtersByGroup = groupFilters(activeFilters);
  return filterTreeNode(rootNode, filtersByGroup);
}

function groupFilters(activeFilters) {
  const map = new Map();

  for (const filter of activeFilters) {
    if (!filter?.groupName || !filter.fn) continue;

    if (!map.has(filter.groupName)) {
      map.set(filter.groupName, []);
    }

    map.get(filter.groupName).push(filter);
  }

  return map;
}

function matchesErgebnisFilters(ergebnis, filtersByGroup) {
  if (!filtersByGroup.size) return true;

  for (const filters of filtersByGroup.values()) {
    const groupMatches = filters.some((filter) => {
      return filter.fn?.matchErgebnis?.(ergebnis) === true;
    });

    if (!groupMatches) return false;
  }

  return true;
}

function matchesMessageFilters(message, filtersByGroup) {
  if (!filtersByGroup.size) return true;

  for (const filters of filtersByGroup.values()) {
    const groupMatches = filters.some((filter) => {
      return filter.fn?.matchMessage?.(message) === true;
    });

    if (!groupMatches) return false;
  }

  return true;
}

function filterTreeNode(node, filtersByGroup) {
  if (!node) return null;

  const filteredEbenen = filterEbenen(node.ebenen || [], filtersByGroup);

  return {
    ...node,
    ebenen: filteredEbenen,
  };
}

function filterEbenen(ebenen, filtersByGroup) {
  return ebenen
    .map((ebene) => {
      const gruppen = filterGruppen(ebene.gruppen || [], filtersByGroup);

      if (!gruppen.length) return null;

      return {
        ...ebene,
        gruppen,
      };
    })
    .filter(Boolean);
}

function filterGruppen(gruppen, filtersByGroup) {
  return gruppen
    .map((gruppe) => {
      const ergebnisse = (gruppe.ergebnisse || [])
        .filter((ergebnis) => matchesErgebnisFilters(ergebnis, filtersByGroup));

      const messages = (gruppe.messages || [])
        .filter((message) => matchesMessageFilters(message, filtersByGroup));

      const ebenen = filterEbenen(gruppe.ebenen || [], filtersByGroup);

      if (!ergebnisse.length && !messages.length && !ebenen.length) {
        return null;
      }

      return {
        ...gruppe,
        ergebnisse,
        messages,
        ebenen,
      };
    })
    .filter(Boolean);
}