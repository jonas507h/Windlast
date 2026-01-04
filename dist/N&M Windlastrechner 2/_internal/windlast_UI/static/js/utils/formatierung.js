// utils/formatierung.js  (ES module)
// → Aus footer.js ausgelagerte Konstanten + Formatierungsfunktionen (1:1)

// ------------------------------------
// Konstanten
// ------------------------------------
export const DISPLAY_EPS = 1e-9;

const FLAG_LABELS = {
  show_zwischenergebnisse_tooltip: "Debug-Tooltip für Zwischenergebnisse anzeigen",
  show_nichtZertifiziert_warnung: '"Berechnung nicht zertifiziert"-Warnung anzeigen',
  show_doppelte_meldungen: "Doppelte Meldungen anzeigen",
  show_meldungen_tooltip: "Debug-Tooltips für Meldungen anzeigen",
  show_real_kontext_keys: "Interne Kontext-Schlüssel anzeigen",
  show_nullpunkt: "Nullpunkt anzeigen",
  show_suche_tooltip: "Debug-Tooltip für Suche anzeigen",
  show_test_options_dropdown: "Test-Optionen in den Dropdowns anzeigen",
  use_eps_on_anzeige: "Kleine Werte als Null anzeigen",
  show_einstellungen_button: "Einstellungen-Button anzeigen",
};

export const ALT_LABELS = {
  IN_BETRIEB: "mit Schutzmaßnahmen",
  VERSTAERKEND: "mit verstärkenden Sicherungsmaßnahmen",
  SCHUETZEND: "mit schützenden Sicherungsmaßnahmen",
};

export const SEVERITY_ORDER = ["error", "warn", "hint", "info"];

export const NORM_DISPLAY_NAMES = {
  EN_13814_2005: "DIN EN 13814:2005-06",
  EN_17879_2024: "DIN EN 17879:2024-08",
  EN_1991_1_4_2010: "DIN EN 1991-1-4:2010-12"
};

// Wunschreihenfolge für Kontext-Felder
export const CONTEXT_ORDER = [
  "anzahl_windrichtungen",
  "windrichtung", "windrichtung_deg",
  "szenario", "scenario", "szenario_anzeigename",
  "windzone",
  "nachweis",
  "abschnitt",
  "phase",
  "komponente", "element", "bauteil",
  "einwirkungsart", "stelle",
  "element_index",
  "id", "element_id", "element_id_intern",
  "objekttyp",
  "objekt_name",
  "objekt_name_intern",
  "funktion",
  "norm", "norm_label",
  "methode",
];

// Anzeigenamen/Aliase für Kontext-Keys
export const CONTEXT_ALIASES = {
  funktion: "Funktion",
  norm: "Norm",
  nachweis: "Nachweis",
  abschnitt: "Abschnitt",
  komponente: "Komponente",
  element: "Element",
  bauteil: "Bauteil",
  element_id: "Element-ID",
  element_id_intern: "Element-ID (intern)",
  bodenplatte_name_intern: "Bodenplatte",
  szenario: "Szenario",
  scenario: "Szenario",
  szenario_anzeigename: "Szenario",
  einwirkungsart: "Einwirkungsart",
  stelle: "Stelle",
  id: "ID",
  gesamt_hoehe: "Gesamthöhe",
  gesamthoehe: "Gesamthöhe",
  h_bau: "Gesamthöhe",
  h_max: "Max. gültige Höhe",
  z_max: "Max. erlaubte Höhe",
  windzone: "Windzone",
  windrichtung_deg: "Windrichtung",
  paarung: "Materialpaarung",
  norm_used: "Verwendete Norm",
  segment_index: "Segment",
};

export const CONTEXT_BLACKLIST = new Set([
  "szenario",
  "element_index",
  "element_id_intern",
]);

export const CONTEXT_BLACKLIST_PREFIXES = [
  /^debug_/,
  /^internal_/,
];

// ------------------------------------
// Helfer
// ------------------------------------
function useDisplayEps() {
  try {
    if (typeof window === "undefined") return false;
    return !!(window.APP_STATE?.flags?.use_eps_on_anzeige);
  } catch {
    return false;
  }
}

export function getFlagLabel(flagKey) {
  if (FLAG_LABELS[flagKey]) return FLAG_LABELS[flagKey];

  // Fallback: show_nullpunkt -> Show Nullpunkt
  return flagKey
    .replace(/^show_/, "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

export function displayAltName(name) {
  return (name && ALT_LABELS[name]) || name || "";
}

export function getNormDisplayName(normKey) {
  return NORM_DISPLAY_NAMES[normKey] || normKey.replace(/_/g, " ");
}

export function escapeHtml(s){
  return String(s).replace(/[&<>"']/g,m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
}

// 1:1 Zahl-/Vektorformatierung (DE, wissenschaftlich bei großen/kleinen Zahlen)
export function formatNumberDE(value, sig = 4) {
  if (value == null || value === "INF" || value === "-INF" || Number.isNaN(value)) {
    return String(value);
  }

  let num = Number(value);
  if (!Number.isFinite(num)) return String(value);

  // Optional: sehr kleine Beträge auf 0 setzen (nur Anzeige)
  if (useDisplayEps() && Math.abs(num) < DISPLAY_EPS) {
    num = 0;
  }

  // Ganzzahlen ohne Nachkommastellen
  if (Number.isInteger(num)) {
    return num.toString();
  }

  // wissenschaftliche Notation auseinandernehmen
  let [mantissa, exp] = num.toExponential(sig - 1).split("e");
  exp = Number(exp);

  // Standardfall: normale Zahl (Punkt→Komma)
  if (exp > -3 && exp < 4) {
    const rounded = num.toPrecision(sig);
    return rounded.replace(".", ",");
  }

  // wissenschaftliche Darstellung →  mantissa ×10^exp
  const mant = parseFloat(mantissa).toString().replace(".", ",");
  return `${mant}×10<sup>${exp}</sup>`;
}

export function formatVectorDE(vec, sig = 4) {
  if (!Array.isArray(vec)) return formatNumberDE(vec, sig);
  const parts = vec.map(v => formatNumberDE(v, sig));
  return `(${parts.join("; ")})`;
}

// Mathe-Sub/Sup (leichtgewichtig); 1:1 zur bestehenden Logik
export function formatMathWithSubSup(input) {
  const s = String(input ?? "");
  const pattern = /([A-Za-z\u0370-\u03FF0-9])_(\{[^}]+\}|[^\s^_<>()]+)|([A-Za-z\u0370-\u03FF0-9])\^(\{[^}]+\}|[^\s^_<>()]+)/g;
  let out = "";
  let last = 0;

  const esc = (t) => t.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

  for (let m; (m = pattern.exec(s)); ) {
    // Text vor dem Match escapen
    out += esc(s.slice(last, m.index));
    last = pattern.lastIndex;

    if (m[1] != null) {
      // Subscript: base _ sub
      const base = m[1];
      const rawSub = m[2];
      const inner = rawSub.startsWith("{") ? rawSub.slice(1, -1) : rawSub;
      out += esc(base) + "<sub>" + esc(inner) + "</sub>";
    } else {
      // Superscript: base ^ sup
      const base = m[3];
      const rawSup = m[4];
      const inner = rawSup.startsWith("{") ? rawSup.slice(1, -1) : rawSup;
      out += esc(base) + "<sup>" + esc(inner) + "</sup>";
    }
  }
  // Rest anhängen
  out += esc(s.slice(last));
  return out;
}

// Key → hübscher Labeltext
export function prettyKey(k) {
  if (!k || typeof k !== "string") return String(k);
  if (CONTEXT_ALIASES[k]) return CONTEXT_ALIASES[k];
  // snake_case → "Snake Case"
  return k.replace(/_/g, " ").replace(/\b\p{L}/gu, (c) => c.toUpperCase());
}

// zentraler Value→String/HTML (wie im Footer)
export function formatVal(k, v, { html = false } = {}) {
  // Nullish → Gedankenstrich
  if (v === null || v === undefined) return "—";

  // Szenario-Alias
  if ((k === "szenario" || k === "scenario") && typeof v === "string") {
    const s = displayAltName(v) || v;
    return html ? escapeHtml(s) : s;
  }

  // Booleans → Ja/Nein
  if (typeof v === "boolean") return v ? "Ja" : "Nein";

  // Arrays → Vektor, falls numerisch; sonst CSV
  if (Array.isArray(v)) {
    const numeric = v.every(x => x !== null && x !== undefined && isFinite(Number(x)));
    if (numeric) return formatVectorDE(v, 4);
    const items = v.map(x => html ? escapeHtml(String(x)) : String(x));
    return items.join(", ");
  }

  // Objekte mit x/y/z → als Vektor behandeln
  if (v && typeof v === "object" && ["x","y","z"].every(p => p in v)) {
    return formatVectorDE([v.x, v.y, v.z], 4);
  }

  // Andere Objekte → kompakt serialisieren (nur Plaintext sinnvoll)
  if (v && typeof v === "object") {
    try {
      const s = JSON.stringify(v);
      return html ? escapeHtml(s) : s;
    } catch {
      const s = String(v);
      return html ? escapeHtml(s) : s;
    }
  }

  // Zahlen / numerische Strings → deutsch + ×10<sup>…</sup>
  if (typeof v === "number" || (typeof v === "string" && isFinite(Number(v)))) {
    return formatNumberDE(v, 4);
  }

  // Fallback String
  const s = String(v);
  return html ? escapeHtml(s) : s;
}

export function prettyVal(k, v) {
  return formatVal(k, v, { html: false });
}

export function prettyValHTML(k, v) {
  return formatVal(k, v, { html: true });
}

// ------------------------------------
// Kontext-Sortierung/-Filter
// ------------------------------------
export function isBlacklistedKey(k) {
  if (!k) return false;
  if (CONTEXT_BLACKLIST.has(k)) return true;
  return CONTEXT_BLACKLIST_PREFIXES.some(rx => rx.test(k));
}

// Sortiert Kontext-Einträge: erst laut CONTEXT_ORDER, dann Rest in Quell-Reihenfolge
export function orderContextEntries(ctx, pref = CONTEXT_ORDER) {
  if (!ctx || typeof ctx !== "object") return [];

  const withIndex = [];
  let i = 0;
  for (const k in ctx) {
    if (!Object.hasOwn(ctx, k)) continue;
    if (isBlacklistedKey(k)) continue;
    const v = ctx[k];
    if (v === undefined || v === null || v === "") continue;
    withIndex.push([k, v, i++]); // [key, value, originalIndex]
  }

  const rank = new Map(pref.map((k, idx) => [k, idx]));
  withIndex.sort((a, b) => {
    const ra = rank.has(a[0]) ? rank.get(a[0]) : Infinity;
    const rb = rank.has(b[0]) ? rank.get(b[0]) : Infinity;
    if (ra !== rb) return ra - rb;
    return a[2] - b[2];
  });

  return withIndex.map(([k, v]) => [k, v]);
}

// ------------------------------------
// Severity / Meldungen
// ------------------------------------
export function sortMessagesBySeverity(msgs) {
  return [...msgs].sort((a, b) => {
    const sa = (a.severity || "").toLowerCase();
    const sb = (b.severity || "").toLowerCase();
    const ia = SEVERITY_ORDER.indexOf(sa);
    const ib = SEVERITY_ORDER.indexOf(sb);
    // unbekannte Severities ans Ende
    const ra = ia >= 0 ? ia : SEVERITY_ORDER.length;
    const rb = ib >= 0 ? ib : SEVERITY_ORDER.length;
    return ra - rb;
  });
}
