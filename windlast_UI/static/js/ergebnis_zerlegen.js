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

      // --- NEU: Container für Docs & Messages (Haupt + Alternativen) ---
      idx.docsMainByNorm = {};
      idx.docsByAlt      = {};
      idx.msgsMainByNorm = {};
      idx.msgsByAlt      = {};

      // --- Counts wie gehabt (jetzt inkl. Alternativen) ---
      idx.counts = {}; // counts[normKey][scenario] => {error,warn,hint,info}

      // --- Anzeigename für Alternativen ---
      idx.altLabelsByNorm = {};

      for (const [normKey, norm] of Object.entries(idx.payload.normen || {})) {
        // 1) Haupt-Docs/-Messages in den Index legen
        const mainDocs = Array.isArray(norm?.docs) ? norm.docs : [];
        const mainMsgs = Array.isArray(norm?.messages) ? norm.messages : [];
        idx.docsMainByNorm[normKey] = mainDocs;
        idx.msgsMainByNorm[normKey] = mainMsgs;

        // 2) Alternativen-Container initialisieren
        idx.docsByAlt[normKey] = {};
        idx.msgsByAlt[normKey] = {};
        idx.altLabelsByNorm[normKey] = {};

        // 3) Counts-Map für diese Norm vorbereiten
        const c = {};
        const ensure = (sc) => (c[sc] ||= createZeroCounts());

        // ---- Counts & Ablage: Haupt-Messages (Szenario "_gesamt" oder aus context.szenario) ----
        for (const m of mainMsgs) {
          const sev = normalizeSeverity(m?.severity);
          if (!sev) continue;
          const ctx = m?.context || {};
          const rawScen = (ctx.szenario ?? ctx.scenario);
          const scen = (rawScen === undefined || rawScen === null || String(rawScen).trim() === "")
            ? "_gesamt"
            : String(rawScen);
          ensure(scen)[sev] += 1;
        }

        // ---- Alternativen einlesen (Docs & Messages) ----
        const alts = norm?.alternativen || {};
        for (const [altName, altVal] of Object.entries(alts)) {
          const altDocs = Array.isArray(altVal?.docs) ? altVal.docs : [];
          const altMsgs = Array.isArray(altVal?.messages) ? altVal.messages : [];

          idx.docsByAlt[normKey][altName] = altDocs;
          idx.msgsByAlt[normKey][altName] = altMsgs;

          // NEU: Anzeigename aus Payload (Fallback = altName)
          const label = (altVal && altVal.anzeigename) ? String(altVal.anzeigename) : String(altName);
          idx.altLabelsByNorm[normKey][altName] = label;

          // Counts: für Alternativen unter eigenem Szenario (Alt-Name) zählen;
          // falls Messages bereits context.szenario tragen, nehmen wir das, sonst fallback = altName
          for (const m of altMsgs) {
            const sev = normalizeSeverity(m?.severity);
            if (!sev) continue;
            const ctx = m?.context || {};
            const rawScen = (ctx.szenario ?? ctx.scenario);
            const scen = (rawScen === undefined || rawScen === null || String(rawScen).trim() === "")
              ? String(altName)
              : String(rawScen);
            ensure(scen)[sev] += 1;
          }
        }

        // 4) Counts-Ergebnis für diese Norm ablegen
        idx.counts[normKey] = c;
      }

      return idx;
    },

    _proto: {
      // ---- Wertezugriff (Hauptwerte) ----
      getMainValue(normKey, key) {
        const v = this.payload?.normen?.[normKey]?.[key];
        return v === undefined ? null : v; // float | "INF" | "-INF" | null
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
      getAltLabel(normKey, altName) {
        const byNorm = this.altLabelsByNorm?.[normKey] || {};
        return byNorm[altName] || altName;
      },

      // ==================== MESSAGES ====================

      // Direkter Zugriff: Haupt vs. Alternative
      getMessages(normKey, altName = null) {
        if (altName) {
          return this.msgsByAlt?.[normKey]?.[altName] || [];
        }
        return this.msgsMainByNorm?.[normKey] || [];
      },

      // Texte statt ganzer Objekte (komfortabel für Tooltips/Badges)
      getMessageTexts(normKey, altName = null) {
        const arr = this.getMessages(normKey, altName);
        return arr.map(m => m?.text).filter(Boolean);
      },

      // ---- Meldungs-Zählungen (Counts bleiben wie gebaut) ----
      getCounts(normKey, scenario = "_gesamt") {
        const byNorm = this.counts?.[normKey] || {};
        const c = byNorm[scenario] || createZeroCounts();
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
      },

      // Nur Hauptberechnung (Alternativen sind bereits separiert)
      getCountsMainOnly(normKey) {
        const byNorm = this.counts?.[normKey] || {};
        const altNames = Object.keys(this.payload?.normen?.[normKey]?.alternativen || {});
        const sum = createZeroCounts();
        for (const [sc, c] of Object.entries(byNorm)) {
          if (altNames.includes(sc)) continue;
          sum.error += c.error; sum.warn += c.warn; sum.hint += c.hint; sum.info += c.info;
        }
        return sum;
      },

      // ============ Back-compat Wrapper (optional) ============
      // Falls alter Code noch mit scenario-Strings arbeitet:
      // - scenario === null           -> Haupt
      // - scenario === "_gesamt"      -> Haupt
      // - scenario == <Alt-Name>      -> Alternative
      listMessageTexts(normKey, scenario = null) {
        if (scenario == null || String(scenario).trim() === "" || scenario === "_gesamt") {
          return this.getMessageTexts(normKey, null);
        }
        // Wenn es eine Alternative ist, hole deren Liste:
        const altNames = new Set(this.listAlternativen(normKey));
        const sc = String(scenario).trim();
        if (altNames.has(sc)) return this.getMessageTexts(normKey, sc);

        // Fallback: seltene Sonder-Szenarien in Haupt filtern (sollte es kaum geben)
        const main = this.getMessages(normKey, null);
        return main
          .filter(m => (m?.context?.szenario ?? m?.context?.scenario ?? "") === sc)
          .map(m => m?.text).filter(Boolean);
      },

      listMessages(normKey, scenario = null) {
        if (scenario == null || String(scenario).trim() === "" || scenario === "_gesamt") {
          return this.getMessages(normKey, null);
        }
        const altNames = new Set(this.listAlternativen(normKey));
        const sc = String(scenario).trim();
        if (altNames.has(sc)) return this.getMessages(normKey, sc);

        // Fallback-Filter auf Haupt (wie oben)
        const main = this.getMessages(normKey, null);
        return main.filter(m => (m?.context?.szenario ?? m?.context?.scenario ?? "") === sc);
      },

      // Alt: Nur Haupt-Messages
      listMessagesMainOnly(normKey) {
        // Früher: Filter nötig. Jetzt: Haupt enthält schon keine Alt-Messages mehr.
        return this.getMessages(normKey, null);
      },
    }
  };

  global.ResultsIndex = ResultsIndex;
})(window);