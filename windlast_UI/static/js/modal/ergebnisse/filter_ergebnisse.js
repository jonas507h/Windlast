export const FILTER_GROUPS = [
  {
    name: "label_filter",
    label: "Namens-Filter",
    filters: [
      {
        name: "kippsicherheiten",
        label: "Kippsicherheiten",
        fn: filterLabel("Kippsicherheit S_kipp"),
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
        name: "messages",
        label: "Messages",
        fn: filterType("message"),
      },
    ],
  },
];

export function filterLabel(exaktesLabel) {
  return {
    matchErgebnis: (ergebnis) => {
      const label = ergebnis?.label ?? ergebnis?.name ?? "";
      return String(label).trim() === String(exaktesLabel).trim();
    },
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