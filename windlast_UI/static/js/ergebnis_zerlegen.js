(function (global) {
  const SEVS = ["error","warn","hint","info"];

  function normalizeSeverity(s) {
    if (!s) return null;
    s = String(s).toLowerCase();
    if (s === "warning") s = "warn";
    if (s === "information") s = "info";
    if (s === "hinweis") s = "hint";
    return SEVS.includes(s) ? s : null;
  }

  function createZeroCounts() { return { error:0, warn:0, hint:0, info:0 }; }

  const ResultsIndex = {
    build(payload) {
      const idx = Object.create(ResultsIndex._proto);
      idx.payload = payload || { normen: {} };
      idx.counts = {}; // counts[normKey][scenario] => {error,warn,hint,info}

      for (const [normKey, norm] of Object.entries(idx.payload.normen || {})) {
        const c = {};
        const ensure = (sc) => (c[sc] ||= createZeroCounts());

        const messages = Array.isArray(norm?.messages) ? norm.messages : [];
        for (const m of messages) {
          const sev = normalizeSeverity(m?.severity);
          if (!sev) continue;
          const ctx = m?.context || {};
          const scen = String(ctx.szenario ?? ctx.scenario ?? "_gesamt");
          ensure(scen)[sev] += 1;
        }
        idx.counts[normKey] = c;
      }
      return idx;
    },

    _proto: {
      // ---- Wertezugriff (Hauptwerte) ----
      getMainValue(normKey, key) {
        const v = this.payload?.normen?.[normKey]?.[key];
        // unverändert zurückgeben: float | "INF" | "-INF" | null
        return v === undefined ? null : v;
      },

      // ---- Wertezugriff (Alternativen) ----
      listAlternativen(normKey) {
        const alts = this.payload?.normen?.[normKey]?.alternativen || {};
        return Object.keys(alts);
      },
      getAltValue(normKey, altName, key) {
        const v = this.payload?.normen?.[normKey]?.alternativen?.[altName]?.[key];
        return v === undefined ? null : v;
      },

      // ---- Meldungs-Zählungen ----
      getCounts(normKey, scenario = "_gesamt") {
        const byNorm = this.counts?.[normKey] || {};
        const c = byNorm[scenario] || createZeroCounts();
        // Kopie, damit der Aufrufer nicht intern mutiert
        return { error:c.error, warn:c.warn, hint:c.hint, info:c.info };
      },

      // Summen über alle Szenarien
      getCountsAllScenarios(normKey) {
        const byNorm = this.counts?.[normKey] || {};
        const sum = createZeroCounts();
        for (const c of Object.values(byNorm)) {
          sum.error += c.error; sum.warn += c.warn; sum.hint += c.hint; sum.info += c.info;
        }
        return sum;
      }
    }
  };

  global.ResultsIndex = ResultsIndex;
})(window);