(() => {
  function currentSystem() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function getTheme() {
    return localStorage.getItem('theme') || currentSystem();
  }
  function applyTheme(theme) {
    const t = theme === 'dark' ? 'dark' : 'light';
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
    const t = d.value === 'dark' ? 'dark' : 'light';
    localStorage.setItem('theme', t);
    applyTheme(t);
    forward(t);
  });

  // globaler Setter für Toggler in Header
  window.__setTheme = (t) => {
    const theme = t === 'dark' ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
    applyTheme(theme);
    forward(theme);
    // Parent informieren, damit Geschwister-Frames aktualisiert werden
    if (window.parent && window.parent !== window) {
      try { window.parent.postMessage({ type: 'theme', value: theme }, '*'); } catch {}
    }
  };
})();
