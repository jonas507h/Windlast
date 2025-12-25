// preview_farben.js — zentrale Farbdefinitionen für die Preview (Light/Dark + erweiterbar)

function cssVar(name, fallback = null) {
  try {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  } catch {
    return fallback;
  }
}

// Nimmt '#rrggbb' / 'rgb(...)' / 'rgba(...)' / Zahl 0x..
// und gibt eine Zahl 0xRRGGBB zurück.
function toHexNumber(c) {
  if (typeof c === 'number') return c;

  if (typeof c !== 'string') return 0xffffff;
  const s = c.trim();

  // #rgb / #rrggbb
  if (s[0] === '#') {
    let hex = s.slice(1);
    if (hex.length === 3) hex = hex.split('').map(ch => ch + ch).join('');
    const n = parseInt(hex, 16);
    return Number.isFinite(n) ? n : 0xffffff;
  }

  // rgb/rgba
  const m = s.match(/rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)/i);
  if (m) {
    const r = Math.max(0, Math.min(255, Number(m[1])));
    const g = Math.max(0, Math.min(255, Number(m[2])));
    const b = Math.max(0, Math.min(255, Number(m[3])));
    return ((r & 255) << 16) | ((g & 255) << 8) | (b & 255);
  }

  // '0xrrggbb' als string
  if (s.startsWith('0x')) {
    const n = parseInt(s.slice(2), 16);
    return Number.isFinite(n) ? n : 0xffffff;
  }

  // named colors (z.B. "white") -> über Canvas lösen
  try {
    const ctx = document.createElement('canvas').getContext('2d');
    ctx.fillStyle = s;
    const resolved = ctx.fillStyle; // wird zu rgb(...) normalisiert
    return toHexNumber(resolved);
  } catch {
    return 0xffffff;
  }
}

function buildThemeFromCSS() {
  return {
    name: 'css',

    // Szene
    background: toHexNumber(cssVar('--preview-bg', '#111111')),

    // Konstruktion
    lineColor: toHexNumber(cssVar('--preview-line-color', '#aaaaaa')),
    plateFill: toHexNumber(cssVar('--preview-plate-fill', '#222222')),
    plateFillGummi: toHexNumber(cssVar('--preview-plate-fill-gummi', '#fdc300')),
    wallFill: toHexNumber(cssVar('--preview-wall-fill', '#333333')),

    // Maße (aus euren semantischen Farben, wenn du willst)
    dimensions: {
      lineColor: toHexNumber(cssVar('--preview-dimension-line', '#fdc300')),
      textFill: cssVar('--preview-dimension-text-fill', '#fdc300'),
      textOutline: cssVar('--preview-dimension-text-outline', '#000000'),
      textOutlineWidth: 4,
      textBackground: cssVar('--preview-dimension-text-bg', '#000000'),
      textBorder: cssVar('--preview-dimension-text-border', '#fdc300'),
      textBorderWidth: 20,
    },
  };
}

// Farbschemata können später einfach erweitert werden (z.B. "high-contrast", "print", ...).
export const PREVIEW_THEMES = {
  light: {
    name: 'light', //Fallback

    // Szene
    background: 0xffffff,

    // Konstruktion
    lineColor: 0x111111,
    plateFill: 0xf5f5f5,
    plateFillGummi: 0x0066cc,
    wallFill:  0xaaaaaa,

    // Maße
    dimensions: {
      lineColor: 0xff0000,

      textFill: '#ff0000',
      textOutline: '#ffffff',
      textOutlineWidth: 4,

      // Textkasten
      textBackground: '#ffffff',
      textBorder: '#ff0000',
      textBorderWidth: 20,
    },
  },
};

/**
 * Ermittelt den aktuellen Preview-Theme-Namen.
 * - explicitName: kann z.B. "dark" erzwingen (optional)
 * - sonst: localStorage("theme") → data-theme → prefers-color-scheme
 */
export function getCurrentPreviewThemeName(explicitName) {
  if (explicitName && PREVIEW_THEMES[explicitName]) {
    return explicitName;
  }

  try {
    const ls = window?.localStorage?.getItem('theme');
    if (ls && PREVIEW_THEMES[ls]) return ls;
  } catch {
    // ignore
  }

  try {
    const attr = document?.documentElement?.getAttribute('data-theme');
    if (attr && PREVIEW_THEMES[attr]) return attr;
  } catch {
    // ignore
  }

  const prefersDark =
    typeof window !== 'undefined' &&
    window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: dark)').matches;

  return prefersDark && PREVIEW_THEMES.dark ? 'dark' : 'light';
}

/**
 * Liefert das aktuelle Theme-Objekt.
 */
export function getPreviewTheme(explicitName) {
  try {
    const cssTheme = buildThemeFromCSS();

    // Minimaler Validitätscheck
    if (
      cssTheme &&
      Number.isFinite(cssTheme.background) &&
      Number.isFinite(cssTheme.lineColor) &&
      Number.isFinite(cssTheme.plateFill)
    ) {
      return cssTheme;
    }
  } catch (e) {
    // bewusst leer – wir fallen zurück
  }

  // Fallback
  return PREVIEW_THEMES.light;
}

/**
 * Listener für Theme-Änderungen via postMessage (von deinem globalen theme.js).
 * Rückgabe: unsubscribe-Funktion.
 *
 * cb({ name, theme })
 */
export function subscribePreviewTheme(cb) {
  if (typeof window === 'undefined') return () => {};

  const handler = (e) => {
    const d = e && e.data;
    if (!d || d.type !== 'theme') return;
    const val = d.value === 'dark' ? 'dark' : 'light';

    // 1 Frame warten, damit CSS (data-theme / Variablen) sicher “gezogen” ist
    requestAnimationFrame(() => {
      const theme = getPreviewTheme(val);   // <-- WICHTIG: neu berechnen
      cb({ name: val, theme });
    });
  };

  window.addEventListener('message', handler);
  return () => window.removeEventListener('message', handler);
}
