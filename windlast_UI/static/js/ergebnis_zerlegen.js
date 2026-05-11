(function (global) {
  const SEVS = ["error", "warn", "hint", "info"];

  const API_TO_TREE_NORM = {
    EN_13814_2005: "DIN_EN_13814_2005_06",
    EN_17879_2024: "DIN_EN_17879_2024_08",
    EN_1991_1_4_2010: "DIN_EN_1991_1_4_2010_12",
  };

  const TREE_TO_API_NORM = Object.fromEntries(
    Object.entries(API_TO_TREE_NORM).map(([api, tree]) => [tree, api])
  );

  const RESULT_BY_ROW_KEY = {
    kipp: "sicherheit_kipp",
    gleit: "sicherheit_gleit",
    abhebe: "sicherheit_abhebe",
    ballast: "ballast_max",
  };

  const DEFAULT_SCENARIO_BY_NORM = {
    EN_13814_2005: "AUSSER_BETRIEB",
    EN_17879_2024: "AUSSER_BETRIEB",
    EN_1991_1_4_2010: "STANDARD",
  };

  function normalizeSeverity(s) {
    if (!s) return null;
    s = String(s).toLowerCase();
    if (s === "warning") s = "warn";
    if (s === "information") s = "info";
    if (s === "hinweis") s = "hint";
    return SEVS.includes(s) ? s : null;
  }

  function createZeroCounts() {
    return { error: 0, warn: 0, hint: 0, info: 0 };
  }

  function normalizeValue(v) {
    if (v === undefined) return null;
    if (v === "Infinity") return "INF";
    if (v === "-Infinity") return "-INF";
    if (v === "NaN") return null;
    return v;
  }

  function groupLabel(gruppe) {
    return gruppe?.label || gruppe?.name || "";
  }

  function findEbene(container, ebeneName) {
    const ebenen = Array.isArray(container?.ebenen) ? container.ebenen : [];
    return ebenen.find((e) => e?.name === ebeneName) || null;
  }

  function findGruppe(container, ebeneName, gruppeName) {
    const ebene = findEbene(container, ebeneName);
    if (!ebene) return null;
    const gruppen = Array.isArray(ebene.gruppen) ? ebene.gruppen : [];
    return gruppen.find((g) => String(g?.name) === String(gruppeName)) || null;
  }

  function listGruppen(container, ebeneName) {
    const ebene = findEbene(container, ebeneName);
    return Array.isArray(ebene?.gruppen) ? ebene.gruppen : [];
  }

  function findResult(gruppe, resultName) {
    const ergebnisse = Array.isArray(gruppe?.ergebnisse) ? gruppe.ergebnisse : [];
    return ergebnisse.find((r) => r?.name === resultName) || null;
  }

  function makeMessageObject(message, context = {}) {
    if (!message) return null;
    const sev = normalizeSeverity(message.severity);
    return {
      severity: sev,
      text: message.text == null ? null : String(message.text),
      code: message.code == null ? null : String(message.code),
      context: { ...context, ...(message.meta || {}) },
      meta: message.meta || {},
    };
  }

  function collectMessagesRecursive(container, context = {}, out = []) {
    const ownMessages = Array.isArray(container?.messages) ? container.messages : [];
    for (const msg of ownMessages) {
      const m = makeMessageObject(msg, context);
      if (m) out.push(m);
    }

    const ebenen = Array.isArray(container?.ebenen) ? container.ebenen : [];
    for (const ebene of ebenen) {
      const gruppen = Array.isArray(ebene?.gruppen) ? ebene.gruppen : [];
      for (const gruppe of gruppen) {
        collectMessagesRecursive(
          gruppe,
          { ...context, [ebene.name]: gruppe.name },
          out
        );
      }
    }

    return out;
  }

  function collectDocsRecursive(container, context = {}, out = []) {
    const ergebnisse = Array.isArray(container?.ergebnisse) ? container.ergebnisse : [];
    for (const e of ergebnisse) {
      out.push({
        title: e.label || e.name,
        value: normalizeValue(e.wert),
        unit: e.einheit || null,
        formula: e.formel || null,
        symbols: e.formelzeichen || null,
        context: { ...context, ...(e.meta || {}) },
        raw: e,
      });
    }

    const ebenen = Array.isArray(container?.ebenen) ? container.ebenen : [];
    for (const ebene of ebenen) {
      const gruppen = Array.isArray(ebene?.gruppen) ? ebene.gruppen : [];
      for (const gruppe of gruppen) {
        collectDocsRecursive(
          gruppe,
          { ...context, [ebene.name]: gruppe.name },
          out
        );
      }
    }

    return out;
  }

  function addCountsFromMessages(countsMap, scenarioName, messages) {
    const c = (countsMap[scenarioName] ||= createZeroCounts());

    for (const m of messages || []) {
      const sev = normalizeSeverity(m?.severity);
      if (!sev) continue;
      c[sev] += 1;
    }
  }

  function extractNachweisValues(scenarioGroup) {
    const values = {
      kipp: null,
      gleit: null,
      abhebe: null,
      ballast: null,
    };

    const sicherheiten = {
      kipp: "KIPP",
      gleit: "GLEIT",
      abhebe: "ABHEBE",
    };

    for (const [rowKey, sicherheitName] of Object.entries(sicherheiten)) {
      const sicherheitGroup = findGruppe(
        scenarioGroup,
        "sicherheiten",
        sicherheitName
      );

      const resultName = RESULT_BY_ROW_KEY[rowKey];
      const result = findResult(sicherheitGroup, resultName);

      values[rowKey] = normalizeValue(result?.wert);
    }

    const ballastResult = findResult(scenarioGroup, "ballast_max");
    values.ballast = normalizeValue(ballastResult?.wert);

    return values;
  }

  function isMainScenario(apiNormKey, scenarioName, scenarioIndex) {
    const defaultScenario = DEFAULT_SCENARIO_BY_NORM[apiNormKey];
    if (defaultScenario) return scenarioName === defaultScenario;
    return scenarioIndex === 0;
  }

  const ResultsIndex = {
    build(payload) {
      const idx = Object.create(ResultsIndex._proto);

      idx.payload = payload || {};
      idx.tree = payload?.ergebnis || payload || {};

      idx.mainValues = {};
      idx.altValues = {};
      idx.altLabelsByNorm = {};

      idx.docsMainByNorm = {};
      idx.docsByAlt = {};
      idx.msgsMainByNorm = {};
      idx.msgsByAlt = {};

      idx.counts = {};

      const normGroups = listGruppen(idx.tree, "norm");

      for (const normGroup of normGroups) {
        const treeNormKey = String(normGroup?.name || "");
        const normKey = TREE_TO_API_NORM[treeNormKey] || treeNormKey;

        idx.mainValues[normKey] = { kipp: null, gleit: null, abhebe: null, ballast: null };
        idx.altValues[normKey] = {};
        idx.altLabelsByNorm[normKey] = {};

        idx.docsMainByNorm[normKey] = [];
        idx.docsByAlt[normKey] = {};
        idx.msgsMainByNorm[normKey] = [];
        idx.msgsByAlt[normKey] = {};

        idx.counts[normKey] = {};

        const scenarioGroups = listGruppen(normGroup, "szenario");

        scenarioGroups.forEach((scenarioGroup, scenarioIndex) => {
          const scenarioName = String(scenarioGroup?.name || "");
          const scenarioLabel = groupLabel(scenarioGroup) || scenarioName;

          const values = extractNachweisValues(scenarioGroup);
          const messages = collectMessagesRecursive(scenarioGroup, {
            norm: treeNormKey,
            szenario: scenarioName,
          });
          const docs = collectDocsRecursive(scenarioGroup, {
            norm: treeNormKey,
            szenario: scenarioName,
          });

          const main = isMainScenario(normKey, scenarioName, scenarioIndex);

          if (main) {
            idx.mainValues[normKey] = values;
            idx.msgsMainByNorm[normKey] = messages;
            idx.docsMainByNorm[normKey] = docs;
          } else {
            idx.altValues[normKey][scenarioName] = {
              anzeigename: scenarioLabel,
              ...values,
            };
            idx.altLabelsByNorm[normKey][scenarioName] = scenarioLabel;
            idx.msgsByAlt[normKey][scenarioName] = messages;
            idx.docsByAlt[normKey][scenarioName] = docs;
          }

          addCountsFromMessages(idx.counts[normKey], main ? "_gesamt" : scenarioName, messages);
        });
      }

      return idx;
    },

    _proto: {
      getMainValue(normKey, key) {
        const v = this.mainValues?.[normKey]?.[key];
        return v === undefined ? null : v;
      },

      listAlternativen(normKey) {
        return Object.keys(this.altValues?.[normKey] || {});
      },

      getAltValue(normKey, altName, key) {
        const v = this.altValues?.[normKey]?.[altName]?.[key];
        return v === undefined ? null : v;
      },

      getAltLabel(normKey, altName) {
        const byNorm = this.altLabelsByNorm?.[normKey] || {};
        return byNorm[altName] || altName;
      },

      getDocs(normKey, altName = null) {
        if (altName) {
          return this.docsByAlt?.[normKey]?.[altName] || [];
        }
        return this.docsMainByNorm?.[normKey] || [];
      },

      listDocs(normKey, scenario = null) {
        if (scenario == null || String(scenario).trim() === "" || scenario === "_gesamt") {
          return this.getDocs(normKey, null);
        }

        const sc = String(scenario).trim();
        const altNames = new Set(this.listAlternativen(normKey));
        if (altNames.has(sc)) return this.getDocs(normKey, sc);

        return this.getDocs(normKey, null).filter((d) => {
          const ctx = d?.context || {};
          return String(ctx.szenario || "") === sc;
        });
      },

      listDocsMainOnly(normKey) {
        return this.getDocs(normKey, null);
      },

      getMessages(normKey, altName = null) {
        if (altName) {
          return this.msgsByAlt?.[normKey]?.[altName] || [];
        }
        return this.msgsMainByNorm?.[normKey] || [];
      },

      getMessageTexts(normKey, altName = null) {
        return this.getMessages(normKey, altName)
          .map((m) => m?.text)
          .filter(Boolean);
      },

      getCounts(normKey, scenario = "_gesamt") {
        const byNorm = this.counts?.[normKey] || {};
        const c = byNorm[scenario] || createZeroCounts();
        return { error: c.error, warn: c.warn, hint: c.hint, info: c.info };
      },

      getCountsAllScenarios(normKey) {
        const byNorm = this.counts?.[normKey] || {};
        const sum = createZeroCounts();

        for (const c of Object.values(byNorm)) {
          sum.error += c.error;
          sum.warn += c.warn;
          sum.hint += c.hint;
          sum.info += c.info;
        }

        return sum;
      },

      getCountsMainOnly(normKey) {
        return this.getCounts(normKey, "_gesamt");
      },

      listMessageTexts(normKey, scenario = null) {
        if (scenario == null || String(scenario).trim() === "" || scenario === "_gesamt") {
          return this.getMessageTexts(normKey, null);
        }

        const sc = String(scenario).trim();
        const altNames = new Set(this.listAlternativen(normKey));
        if (altNames.has(sc)) return this.getMessageTexts(normKey, sc);

        return this.getMessages(normKey, null)
          .filter((m) => String(m?.context?.szenario || "") === sc)
          .map((m) => m?.text)
          .filter(Boolean);
      },

      listMessages(normKey, scenario = null) {
        if (scenario == null || String(scenario).trim() === "" || scenario === "_gesamt") {
          return this.getMessages(normKey, null);
        }

        const sc = String(scenario).trim();
        const altNames = new Set(this.listAlternativen(normKey));
        if (altNames.has(sc)) return this.getMessages(normKey, sc);

        return this.getMessages(normKey, null).filter((m) => {
          const ctx = m?.context || {};
          return String(ctx.szenario || "") === sc;
        });
      },

      listMessagesMainOnly(normKey) {
        return this.getMessages(normKey, null);
      },
    },
  };

  global.ResultsIndex = ResultsIndex;
})(window);