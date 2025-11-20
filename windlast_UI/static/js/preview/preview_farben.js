// preview_farben.js — zentrale Farbdefinitionen für die Preview (Light/Dark + erweiterbar)

// Farbschemata können später einfach erweitert werden (z.B. "high-contrast", "print", ...).
export const PREVIEW_THEMES = {
  light: {
    name: 'light',

    // Szene
    background: 0xffffff,

    // Konstruktion
    lineColor: 0x111111,
    plateFill: 0xf5f5f5,

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

  dark: {
    name: 'dark',

    // etwas dunkler Hintergrund, damit Linien gut sichtbar sind
    background: 0x111111,

    // Konstruktion
    lineColor: 0xaaaaaa,
    plateFill: 0x222222,

    // Maße (leicht leuchtendes Rot mit dunkler Outline)
    dimensions: {
      lineColor: 0xff6b6b,

      textFill: '#ff6b6b',
      textOutline: '#000000',
      textOutlineWidth: 4,

      textBackground: '#000000',
      textBorder: '#ff6b6b',
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
  const name = getCurrentPreviewThemeName(explicitName);
  return PREVIEW_THEMES[name] || PREVIEW_THEMES.light;
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
    const theme = PREVIEW_THEMES[val] || PREVIEW_THEMES.light;
    cb({ name: val, theme });
  };

  window.addEventListener('message', handler);
  return () => window.removeEventListener('message', handler);
}
