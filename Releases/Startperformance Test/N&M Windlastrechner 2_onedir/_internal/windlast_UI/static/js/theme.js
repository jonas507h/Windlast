(() => {
  let __lastNonSpecialTheme = null;
  function currentSystem() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function getTheme() {
    return localStorage.getItem('theme') || currentSystem();
  }
  function applyTheme(theme) {
    let t;

    if (theme === 'special') {
      t = 'special';
    } else if (theme === 'dark' || theme === 'light') {
      t = theme;
      __lastNonSpecialTheme = theme; // 🔑 merken
    } else {
      t = 'light';
      __lastNonSpecialTheme = 'light';
    }

    document.documentElement.setAttribute('data-theme', t);
  }
  function forward(theme) {
    // an untergeordnete iframes weiterreichen (nur markierte)
    document.querySelectorAll('iframe[data-theme-sync]').forEach(f => {
      try { f.contentWindow && f.contentWindow.postMessage({ type: 'theme', value: theme }, '*'); } catch {}
    });
  }

  // init beim Laden
  const initial = getTheme();
  applyTheme(initial);
  forward(initial);

  // auf Theme-Events reagieren
  window.addEventListener('message', (e) => {
    const d = e && e.data;
    if (!d || d.type !== 'theme') return;
    const t = (d.value === 'dark' || d.value === 'light' || d.value === 'special')
      ? d.value
      : 'light';
    localStorage.setItem('theme', t);
    applyTheme(t);
    forward(t);
  });

  // globaler Setter für Toggler in Header
  window.__setTheme = (t) => {
    let theme = (t === 'dark' || t === 'light' || t === 'special' || t === 'standard')
      ? t
      : 'light';
    if (theme === 'standard' && __lastNonSpecialTheme) {
      // Sondermodus: letztes normales Theme wiederherstellen
      theme = __lastNonSpecialTheme;
    }
    localStorage.setItem('theme', theme);
    applyTheme(theme);
    forward(theme);

    try {
      window.postMessage({ type: 'theme', value: theme }, '*');
    } catch {}
    // Parent informieren, damit Geschwister-Frames aktualisiert werden
    if (window.parent && window.parent !== window) {
      try { window.parent.postMessage({ type: 'theme', value: theme }, '*'); } catch {}
    }
  };
})();

(function attachHoeheFlaecheEasteregg() {
  const MAGIC = "hallo";
  let buffer = "";
  let timer = null;

  document.addEventListener("keydown", (e) => {
    const el = e.target;

    // 🔑 nur genau dieses Feld
    if (!(el instanceof HTMLInputElement)) return;
    if (el.id !== "hoehe_flaeche_m") return;
    if (el.type !== "number") return;

    // nur Buchstaben
    if (e.key.length !== 1 || !/[a-zA-Z]/.test(e.key)) return;

    buffer += e.key.toLowerCase();
    if (buffer.length > MAGIC.length) {
      buffer = buffer.slice(-MAGIC.length);
    }

    clearTimeout(timer);
    timer = setTimeout(() => (buffer = ""), 1200);

    if (buffer === MAGIC) {
      window.__setTheme?.("special");
      buffer = "";
    }
  }, true); // capturing → zuverlässig bei dynamischem DOM
})();
