import { NORM_HELP_PAGES } from "./norminfo.js";
import { GENERAL_HELP_PAGES } from "./allgemein.js";
import { MELDUNGEN_HELP_PAGES } from "./meldungen.js";
import { HEADER_HELP_PAGES } from "./header.js";
import { TOR_HELP_PAGES } from "./tor.js";
import { STEHER_HELP_PAGES } from "./steher.js";
import { TISCH_HELP_PAGES } from "./tisch.js";
import { ERGEBNISSE_HELP_PAGES } from "./ergebnisse.js";
import { ZWISCHENERGEBNISSE_HELP_PAGES } from "./zwischenergebnisse.js";

export const HELP_PAGE_GROUPS = [
  NORM_HELP_PAGES,
  GENERAL_HELP_PAGES,
  MELDUNGEN_HELP_PAGES,
  HEADER_HELP_PAGES,
  TOR_HELP_PAGES,
  STEHER_HELP_PAGES,
  TISCH_HELP_PAGES,
  ERGEBNISSE_HELP_PAGES,
  // ZWISCHENERGEBNISSE_HELP_PAGES,
];

export const HELP_PAGES = HELP_PAGE_GROUPS.flatMap(group => group || []);

export const HELP_PAGES_BY_ID = Object.create(null);

for (const page of HELP_PAGES) {
  if (!page?.id) continue;

  if (HELP_PAGES_BY_ID[page.id]) {
    console.warn("[Help] Doppelte Hilfe-ID:", page.id, page);
  }

  HELP_PAGES_BY_ID[page.id] = page;
}

export function getHelpPage(id) {
  return HELP_PAGES_BY_ID[id] || null;
}