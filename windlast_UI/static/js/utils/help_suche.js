// static/js/utils/help_suche.js

// -----------------------------------------------------------------------------
// Konfiguration / Konstanten
// -----------------------------------------------------------------------------

// Basis-Punkte für das Feld, in dem der Treffer gefunden wurde
const FIELD_PENALTY_TITLE = 0;
const FIELD_PENALTY_BODY  = 2;

// Fuzzy-Matching: bis zu 3 Zeichen Abweichung sind "kostenlos"
const MAX_FREE_EDIT_DISTANCE = 3;

// Begriffzerlegung (Query → mehrere Teile)
const PENALTY_DECOMPOSITION      = 1;  // wenn wir statt Volltreffer auf Teilbegriffe gehen
const PENALTY_GAP_PER_50_CHARS   = 1;  // 1 Punkt pro 50 Zeichen zwischen Begriffsstücken
const GAP_CHARS_PER_POINT        = 50;

// Reihenfolge-Verletzung
const PENALTY_PER_SWAP           = 1;  // 1 Punkt pro "Reihenfolgetausch" (Inversion)

// Voller Begriff taucht nicht am Stück auf
const PENALTY_MISSING_FULL_TERM  = 1;

// Synonyme
const PENALTY_PER_SYNONYM        = 1;

// Obergrenze: Treffer mit Score > MAX_TOTAL_SCORE fliegen raus
// (Wert kannst du später feinjustieren)
const MAX_TOTAL_SCORE            = 12;

// -----------------------------------------------------------------------------
// Synonyme
// Struktur: { <normalizedSuchbegriff>: [<normalizedSynonym1>, <normalizedSynonym2>, ...] }
// Alles wird intern eh noch normalisiert, aber hier kannst du später bequem erweitern.
// -----------------------------------------------------------------------------
const SYNONYMS = {
  // Beispiele, kannst du anpassen / löschen / erweitern:
  // "windlast": ["windlasten", "wind"],
  // "tor": ["traversentor"],
  // "tisch": ["traversentisch"],
};

// -----------------------------------------------------------------------------
// Help-Content registrieren (eigene Registry, um Zyklus mit help.js zu vermeiden)
// -----------------------------------------------------------------------------

import { NORM_HELP_PAGES } from "../help_content/norminfo.js";
import { GENERAL_HELP_PAGES } from "../help_content/allgemein.js";
import { MELDUNGEN_HELP_PAGES } from "../help_content/meldungen.js";
import { HEADER_HELP_PAGES } from "../help_content/header.js";
import { TOR_HELP_PAGES } from "../help_content/tor.js";
import { STEHER_HELP_PAGES } from "../help_content/steher.js";
import { TISCH_HELP_PAGES } from "../help_content/tisch.js";
import { ERGEBNISSE_HELP_PAGES } from "../help_content/ergebnisse.js";
import { ZWISCHENERGEBNISSE_HELP_PAGES } from "../help_content/zwischenergebnisse.js";

const PAGES_BY_ID = Object.create(null);
const ALL_PAGES   = [];

function registerPages(list) {
  for (const p of list || []) {
    if (!p || !p.id) continue;
    PAGES_BY_ID[p.id] = p;
    ALL_PAGES.push(p);
  }
}

registerPages(NORM_HELP_PAGES);
registerPages(GENERAL_HELP_PAGES);
registerPages(MELDUNGEN_HELP_PAGES);
registerPages(HEADER_HELP_PAGES);
registerPages(TOR_HELP_PAGES);
registerPages(STEHER_HELP_PAGES);
registerPages(TISCH_HELP_PAGES);
registerPages(ERGEBNISSE_HELP_PAGES);
registerPages(ZWISCHENERGEBNISSE_HELP_PAGES);

// -----------------------------------------------------------------------------
// Utility: Normalisierung, Textaufbereitung
// -----------------------------------------------------------------------------

function normalizeString(str) {
  return String(str || "")
    .normalize("NFD")                    // Umlaute etc. zerlegen
    .replace(/[\u0300-\u036f]/g, "")     // Akzentzeichen entfernen
    .toLowerCase();
}

// HTML-Tags raus, FAQ-Question-Texte behalten, Wiki-Links in sichtbaren Text umwandeln
function extractSearchableText(rawHtml) {
  if (!rawHtml) return "";

  let text = String(rawHtml);

  // FAQ-Fragen sichtbar machen: <faq question="...">
  text = text.replace(/<faq[^>]*question="([^"]+)"[^>]*>/gi, " $1 ");

  // Closing FAQ-Tags entfernen
  text = text.replace(/<\/faq>/gi, " ");

  // Wiki-Links [[id|Label]] → Label; [[id]] → id
  text = text.replace(/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g, (_m, id, _rest, label) => {
    return " " + (label || id) + " ";
  });

  // HTML-Tags entfernen
  text = text.replace(/<[^>]+>/g, " ");

  // Whitespace normalisieren
  text = text.replace(/\s+/g, " ").trim();

  return text;
}

// Tokenisierung + Positionsdaten
function tokenizeWithPositions(normalizedText) {
  const tokens = [];
  let i = 0;
  const len = normalizedText.length;

  while (i < len) {
    // Skip Non-Word
    while (i < len && !/[a-z0-9äöüß]/.test(normalizedText[i])) {
      i++;
    }
    if (i >= len) break;

    const start = i;
    while (i < len && /[a-z0-9äöüß]/.test(normalizedText[i])) {
      i++;
    }
    const end = i;
    const token = normalizedText.slice(start, end);
    if (token) {
      tokens.push({ token, start, end });
    }
  }

  return tokens;
}

// Levenshtein-Distanz (klassisch, aber ausreichend schnell für unsere Textmengen)
function levenshtein(a, b) {
  a = String(a);
  b = String(b);

  const lenA = a.length;
  const lenB = b.length;

  if (lenA === 0) return lenB;
  if (lenB === 0) return lenA;

  const dp = new Array(lenB + 1);

  for (let j = 0; j <= lenB; j++) {
    dp[j] = j;
  }

  for (let i = 1; i <= lenA; i++) {
    let prev = dp[0];
    dp[0] = i;
    for (let j = 1; j <= lenB; j++) {
      const tmp = dp[j];
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[j] = Math.min(
        dp[j] + 1,       // Deletion
        dp[j - 1] + 1,   // Insertion
        prev + cost      // Substitution
      );
      prev = tmp;
    }
  }

  return dp[lenB];
}

// Inversionen zählen (Anzahl minimaler Swaps bei Bubble-Sort)
function countInversions(arr) {
  let count = 0;
  const tmp = arr.slice();

  function mergeSort(start, end) {
    if (end - start <= 1) return;
    const mid = (start + end) >> 1;
    mergeSort(start, mid);
    mergeSort(mid, end);
    let i = start;
    let j = mid;
    const buf = [];
    while (i < mid && j < end) {
      if (tmp[i] <= tmp[j]) {
        buf.push(tmp[i++]);
      } else {
        buf.push(tmp[j++]);
        count += (mid - i);
      }
    }
    while (i < mid) buf.push(tmp[i++]);
    while (j < end) buf.push(tmp[j++]);
    for (let k = start; k < end; k++) {
      tmp[k] = buf[k - start];
    }
  }

  mergeSort(0, tmp.length);
  return count;
}

// -----------------------------------------------------------------------------
// Matching-Logik für eine Seite / ein Feld
// -----------------------------------------------------------------------------

// Versuch 1: Volltreffer – komplette Query als (normalisierter) Substring im Text
function checkFullPhraseMatch(normText, normQuery) {
  if (!normQuery) return null;
  const idx = normText.indexOf(normQuery);
  if (idx === -1) return null;

  return {
    matchType: "full",
    start: idx,
    end: idx + normQuery.length,
    penalties: {
      decomposition: 0,
      gap: 0,
      order: 0,
      missingFullTerm: 0,
      synonyms: 0
    },
    usedParts: [] // für Volltreffer brauchen wir keine Einzelteile
  };
}

// Versuch 2: Zerlegung der Query in Teile (Leerzeichen-basiert)
function matchDecomposed(normText, tokens, normQuery, fieldName) {
  if (!tokens.length) return null;

  const textTokens = tokenizeWithPositions(normText);

  // Map: partIndex -> bestMatch
  const partMatches = [];
  let totalSynonymsUsed = 0;

  for (let partIndex = 0; partIndex < tokens.length; partIndex++) {
    const part = tokens[partIndex];
    const partSyns = SYNONYMS[part] || [];

    let best = null;

    // Kandidaten: der Begriff selbst + Synonyme
    const candidates = [{ token: part, isSynonym: false }];
    for (const syn of partSyns) {
      candidates.push({ token: syn, isSynonym: true });
    }

    for (const cand of candidates) {
      const candToken = cand.token;
      for (let i = 0; i < textTokens.length; i++) {
        const t = textTokens[i];
        const dist = levenshtein(candToken, t.token);
        if (dist <= MAX_FREE_EDIT_DISTANCE) {
          if (!best || dist < best.dist) {
            best = {
              partIndex,
              textTokenIndex: i,
              start: t.start,
              end: t.end,
              dist,
              isSynonym: cand.isSynonym,
              matchedText: t.token
            };
          }
        }
      }
    }

    if (best) {
      if (best.isSynonym) {
        totalSynonymsUsed += 1;
      }
      partMatches.push(best);
    } else {
      // Kein Match für diesen Part → merken wir uns als "fehlend"
      partMatches.push({
        partIndex,
        textTokenIndex: null,
        start: null,
        end: null,
        dist: null,
        isSynonym: false,
        matchedText: null,
        missing: true
      });
    }
  }

  // Wenn wir *gar kein* Teilstück matchen konnten, geben wir null zurück
  const anyMatched = partMatches.some(m => !m.missing);
  if (!anyMatched) {
    return null;
  }

  // Gap- und Reihenfolge-Berechnung nur für tatsächlich gefundene Stücke
  const matched = partMatches.filter(m => !m.missing);
  matched.sort((a, b) => a.textTokenIndex - b.textTokenIndex);

  // Reihenfolge: Sequenz der ursprünglichen partIndex in Text-Reihenfolge
  const orderSeq = matched.map(m => m.partIndex);
  const swaps = countInversions(orderSeq);

  // Gap: Zeichenabstand zwischen aufeinanderfolgenden Stücken
  let totalGapChars = 0;
  for (let i = 0; i < matched.length - 1; i++) {
    const curr = matched[i];
    const next = matched[i + 1];
    const gap = Math.max(0, next.start - curr.end);
    totalGapChars += gap;
  }

  const gapPenalty = Math.floor(totalGapChars / GAP_CHARS_PER_POINT) * PENALTY_GAP_PER_50_CHARS;
  const orderPenalty = swaps * PENALTY_PER_SWAP;
  const synonymsPenalty = totalSynonymsUsed * PENALTY_PER_SYNONYM;

  // Voller Begriff im Text?
  const hasFullPhrase = normText.indexOf(normQuery) !== -1;
  const missingFullTermPenalty = hasFullPhrase ? 0 : PENALTY_MISSING_FULL_TERM;

  return {
    matchType: "decomposed",
    usedParts: partMatches,
    penalties: {
      decomposition: PENALTY_DECOMPOSITION,
      gap: gapPenalty,
      order: orderPenalty,
      missingFullTerm: missingFullTermPenalty,
      synonyms: synonymsPenalty
    }
  };
}

function scoreFieldForQuery(page, fieldName, normQuery, queryParts) {
  const isTitle = fieldName === "title";
  const basePenalty = isTitle ? FIELD_PENALTY_TITLE : FIELD_PENALTY_BODY;

  const rawText = fieldName === "title" ? page.title : page.body;
  if (!rawText) return null;

  const searchable = extractSearchableText(rawText);
  if (!searchable) return null;

  const normText = normalizeString(searchable);

  // 1. Versuch: Volltreffer
  const fullMatch = checkFullPhraseMatch(normText, normQuery);
  if (fullMatch) {
    const totalScore = basePenalty; // keine zusätzlichen Strafpunkte
    return {
      field: fieldName,
      score: totalScore,
      debug: {
        field: fieldName,
        basePenalty,
        matchType: "full",
        penalties: fullMatch.penalties
      },
      hits: [{
        field: fieldName,
        start: fullMatch.start,
        end: fullMatch.end,
        type: "full",
        query: normQuery
      }],
      text: searchable
    };
  }

  // 2. Versuch: Zerlegung
  const decomp = matchDecomposed(normText, queryParts, normQuery, fieldName);
  if (!decomp) {
    // Feld trägt nichts Sinnvolles bei
    return null;
  }

  const p = decomp.penalties;
  const totalScore =
    basePenalty +
    p.decomposition +
    p.gap +
    p.order +
    p.missingFullTerm +
    p.synonyms;

  // Hits für spätere Markierung
  const hits = [];
  for (const partMatch of decomp.usedParts) {
    if (partMatch.missing || partMatch.start == null || partMatch.end == null) {
      continue;
    }
    hits.push({
      field: fieldName,
      start: partMatch.start,
      end: partMatch.end,
      type: partMatch.isSynonym ? "synonym" : (partMatch.dist > 0 ? "fuzzy" : "exact"),
      partIndex: partMatch.partIndex,
      matchedText: partMatch.matchedText
    });
  }

  return {
    field: fieldName,
    score: totalScore,
    debug: {
      field: fieldName,
      basePenalty,
      matchType: "decomposed",
      penalties: p,
      usedParts: decomp.usedParts
    },
    hits,
    text: searchable
  };
}

// -----------------------------------------------------------------------------
// Öffentliches API
// -----------------------------------------------------------------------------

/**
 * Wird von help.js aufgerufen, wenn das Suchfeld angelegt wird.
 * Hier könnten später Keyboard-Shortcuts, History etc. andocken.
 */
export function initHelpSearch(_inputElement) {
  // Aktuell noch nichts nötig – Platzhalter für spätere Erweiterung.
}

/**
 * Führt eine Suche über alle Hilfe-Seiten durch.
 *
 * Rückgabe:
 * {
 *   query: "<original query>",
 *   results: [
 *     {
 *       id,
 *       score,
 *       title,
 *       shortTitle,
 *       field,         // "title" oder "body"
 *       text,          // bereinigter Text des Felds (für Ausschnitt / Highlighting)
 *       hits: [        // Fundstellen
 *         {
 *           field,
 *           start,
 *           end,
 *           type,      // "full" | "exact" | "fuzzy" | "synonym"
 *           partIndex,
 *           matchedText
 *         },
 *       ],
 *       debug: {
 *         field,
 *         basePenalty,
 *         matchType,
 *         penalties: {
 *           decomposition,
 *           gap,
 *           order,
 *           missingFullTerm,
 *           synonyms
 *         },
 *         usedParts: [...] // bei decomposed
 *       }
 *     },
 *     ...
 *   ],
 *   byId: {
 *     [id]: <gleiche Struktur wie Einträge in results[]>
 *   }
 * }
 */
export function runHelpSearch(query) {
  const originalQuery = String(query || "").trim();
  if (!originalQuery) {
    return {
      query: "",
      results: [],
      byId: Object.create(null)
    };
  }

  const normQuery = normalizeString(originalQuery);
  const queryParts = normalizeString(originalQuery)
    .split(/\s+/)
    .map(s => s.trim())
    .filter(Boolean);

  const results = [];
  const byId = Object.create(null);

  for (const page of ALL_PAGES) {
    const titleScore = scoreFieldForQuery(page, "title", normQuery, queryParts);
    const bodyScore  = scoreFieldForQuery(page, "body",  normQuery, queryParts);

    if (!titleScore && !bodyScore) {
      continue; // Seite hat nichts Brauchbares für diesen Query
    }

    // Wir nehmen das bessere der beiden Felder
    let best = null;
    if (titleScore && bodyScore) {
      best = titleScore.score <= bodyScore.score ? titleScore : bodyScore;
    } else {
      best = titleScore || bodyScore;
    }

    if (best.score > MAX_TOTAL_SCORE) {
      continue; // zu schlecht, wird abgeschnitten
    }

    const resultEntry = {
      id: page.id,
      score: best.score,
      title: page.title || page.id,
      shortTitle: page.shortTitle || page.title || page.id,
      field: best.field,
      text: best.text,
      hits: best.hits,
      debug: best.debug
    };

    results.push(resultEntry);
    byId[page.id] = resultEntry;
  }

  // Sortierung: beste (kleinste Score) zuerst, bei Gleichstand nach Titel
  results.sort((a, b) => {
    if (a.score !== b.score) {
      return a.score - b.score;
    }
    return String(a.title).localeCompare(String(b.title), "de");
  });

  return {
    query: originalQuery,
    results,
    byId
  };
}
