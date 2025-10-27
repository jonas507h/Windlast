// alles in IIFE kapseln und die Funktion global machen
(() => {
  function setActive(view){
    document.querySelectorAll('.tab')
      .forEach(b => b.setAttribute('aria-current', b.dataset.view === view ? 'page' : 'false'));
  }

  function switch_konstruktion(view){
    const iframe = document.getElementById('konstruktions_iframe');
    let filename;
    
    switch(view) {
      case 'steher':
        filename = 'steher.html';
        break;
      case 'tisch':
        filename = 'tisch.html';
        break;
      default:
        filename = 'tor.html';
    }
    
    iframe.src = './' + filename;
    setActive(view);
  }

  // beim Laden aktiven Tab korrekt markieren
  document.addEventListener('DOMContentLoaded', () => {
    setActive('tor');
  });

  // im globalen Scope verfügbar machen, damit onclick=… funktioniert
  window.switch_konstruktion = switch_konstruktion;
})();
