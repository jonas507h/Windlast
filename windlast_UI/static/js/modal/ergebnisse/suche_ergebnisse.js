import { FILTER_GROUPS } from "./filter_ergebnisse.js";

export function searchFilters(query) {
  const q = normalizeSearch(query);
  if (!q) return [];

  const results = [];

  for (const group of FILTER_GROUPS) {
    for (const filter of group.filters || []) {
      const label = filter.label || filter.name || "";

      if (!normalizeSearch(label).includes(q)) continue;

      results.push({
        groupName: group.name,
        groupLabel: group.label || group.name,
        name: filter.name,
        label: filter.label || filter.name,
        fn: filter.fn,
      });
    }
  }

  return results;
}

export function normalizeSearch(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}