export function listEbenen(node) {
  return Array.isArray(node?.ebenen) ? node.ebenen : [];
}

export function listGruppen(ebene) {
  return Array.isArray(ebene?.gruppen) ? ebene.gruppen : [];
}

export function listErgebnisse(gruppeOrRoot) {
  return Array.isArray(gruppeOrRoot?.ergebnisse) ? gruppeOrRoot.ergebnisse : [];
}

export function listMessages(gruppeOrRoot) {
  return Array.isArray(gruppeOrRoot?.messages) ? gruppeOrRoot.messages : [];
}

export function findEbene(node, name) {
  return listEbenen(node).find(e => e?.name === name) || null;
}

export function findGruppe(node, ebeneName, gruppeName) {
  const ebene = findEbene(node, ebeneName);
  return listGruppen(ebene).find(g => String(g?.name) === String(gruppeName)) || null;
}

export function getScenarioRoot(tree, normKey, szenario) {
  const normMap = {
    EN_13814_2005: "DIN_EN_13814_2005_06",
    EN_17879_2024: "DIN_EN_17879_2024_08",
    EN_1991_1_4_2010: "DIN_EN_1991_1_4_2010_12",
  };

  const treeNorm = normMap[normKey] || normKey;
  const normGroup = findGruppe(tree, "norm", treeNorm);
  if (!normGroup) return null;

  if (!szenario) {
    const defaults = {
      EN_13814_2005: "AUSSER_BETRIEB",
      EN_17879_2024: "AUSSER_BETRIEB",
      EN_1991_1_4_2010: "STANDARD",
    };
    szenario = defaults[normKey] || null;
  }

  return szenario ? findGruppe(normGroup, "szenario", szenario) : normGroup;
}

export function makePathLabel(path) {
  if (!path?.length) return "Root";
  return path.map(p => `${p.ebeneLabel || p.ebene} = ${p.gruppeLabel || p.gruppe}`).join(" / ");
}