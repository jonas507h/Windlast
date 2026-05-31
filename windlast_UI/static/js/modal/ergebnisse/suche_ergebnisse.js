import { FILTER_GROUPS } from "./filter_ergebnisse.js";
import { resolveResource } from "../../resources/resources.js";

export function searchFilterSuggestions(query) {
  const q = normalizeSearch(query);
  if (!q) return [];

  const branchSearchHit = {
    kind: "branch_search",
    groupLabel: "Ast durchsuchen",
    label: query,
    query,
  };

  const filterHits = [];

  for (const group of FILTER_GROUPS) {
    for (const filter of group.filters || []) {
      const label = filter.label || filter.name || "";

      if (!normalizeSearch(label).includes(q)) continue;

      filterHits.push({
        kind: "filter",
        groupName: group.name,
        groupLabel: group.label || group.name,
        name: filter.name,
        label: filter.label || filter.name,
        fn: filter.fn,
      });
    }
  }

  return [branchSearchHit, ...filterHits];
}

export function searchInBranch(rootNode, currentPath = [], query = "") {
  const q = normalizeSearch(query);
  if (!q) return [];

  const startNode = getNodeAtPath(rootNode, currentPath);
  if (!startNode) return [];

  const hits = [];

  walkNode(startNode, currentPath, hits, q);

  return hits;
}

function walkNode(node, path, hits, q) {
  for (const ergebnis of node.ergebnisse || []) {
    if (matchesErgebnis(ergebnis, q)) {
      hits.push({
        kind: "ergebnis",
        path,
        breadcrumb: makeBreadcrumbLabel(path),
        item: ergebnis,
      });
    }
  }

  for (const message of node.messages || []) {
    if (matchesMessage(message, q)) {
      hits.push({
        kind: "message",
        path,
        breadcrumb: makeBreadcrumbLabel(path),
        item: message,
      });
    }
  }

  for (const ebene of node.ebenen || []) {
    for (const gruppe of ebene.gruppen || []) {
      walkNode(
        gruppe,
        [
          ...path,
          {
            ebene: ebene.name,
            ebeneLabel: ebene.label,
            gruppe: gruppe.name,
            gruppeLabel: gruppe.label,
          },
        ],
        hits,
        q
      );
    }
  }
}

function getNodeAtPath(rootNode, path = []) {
  let node = rootNode;

  for (const step of path) {
    const ebene = (node.ebenen || []).find((e) => e.name === step.ebene);
    if (!ebene) return null;

    const gruppe = (ebene.gruppen || []).find((g) => String(g.name) === String(step.gruppe));
    if (!gruppe) return null;

    node = gruppe;
  }

  return node;
}

function matchesErgebnis(ergebnis, q) {
  return [
    ergebnis.name,
    resolveResource(ergebnis.label, ergebnis.label),
    resolveResource(ergebnis.formelzeichen, ergebnis.formelzeichen),
    resolveResource(ergebnis.formel, ergebnis.formel),
    ergebnis.einheit,
    ergebnis.wert,
  ].some((value) => normalizeSearch(value).includes(q));
}

function matchesMessage(message, q) {
  return [
    message.severity,
    resolveResource(message.text, message.text),
    message.code,
  ].some((value) => normalizeSearch(value).includes(q));
}

function makeBreadcrumbLabel(path) {
  if (!path?.length) return "Root";

  return path
    .map((step) => {
      const ebene = step.ebeneLabel || step.ebene;
      const gruppe = step.gruppeLabel || step.gruppe;
      return `${ebene} = ${gruppe}`;
    })
    .join(" / ");
}

export function normalizeSearch(value) {
  if (Array.isArray(value)) return normalizeSearch(value.join(" "));

  if (value && typeof value === "object") {
    return normalizeSearch(JSON.stringify(value));
  }

  return String(value ?? "")
    .trim()
    .toLowerCase();
}