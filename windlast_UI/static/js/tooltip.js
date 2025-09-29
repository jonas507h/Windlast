/* Lightweight Tooltip Manager
 * - event delegation: ein Satz Listener für alle registrierten Selektoren
 * - follow cursor
 * - content: string | Node | () => (string|Node|Promise)
 * - conditional: predicate(el) => boolean
 * - priority: höhere Zahl gewinnt, bei Gleichstand zuletzt registriert
 */

(function (global) {
  const OFFSET = { x: 12, y: 16 };
  const MOVE_RAF = { id: 0 };

  // Root aufbauen (einmal)
  const root = (() => {
    let el = document.getElementById("tt-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "tt-root";
      const bubble = document.createElement("div");
      bubble.className = "tt-bubble";
      el.appendChild(bubble);
      document.body.appendChild(el);
    }
    return el;
  })();

  const bubble = root.querySelector(".tt-bubble");

  /** @type {Array<{
   *   selector:string,
   *   getContent:(ev:MouseEvent, el:Element)=> (string|Node|Promise<string|Node>|null|undefined),
   *   predicate?: (el:Element)=>boolean,
   *   priority:number,
   *   delay:number,
   *   className?:string
   * }>} */
  const registry = [];

  // State
  let active = null; // {entry, el, hideTimer, showTimer}
  let lastMouse = { x: 0, y: 0 };

  // Utilities
  function clearTimers(a) {
    if (!a) return;
    if (a.hideTimer) { clearTimeout(a.hideTimer); a.hideTimer = null; }
    if (a.showTimer) { clearTimeout(a.showTimer); a.showTimer = null; }
  }

  function setRootVisible(vis) {
    root.classList.toggle("is-visible", !!vis);
  }

  function setRootClass(mod) {
    root.classList.remove("tt-danger", "tt-warn", "tt-info");
    if (mod) root.classList.add(mod);
  }

  function setContent(nodeOrString, { loading = false } = {}) {
    root.classList.toggle("tt-loading", !!loading);
    // leeren
    bubble.textContent = "";
    bubble.replaceChildren(); // sicherstellen, dass leer ist
    if (nodeOrString == null) return;

    if (nodeOrString instanceof Node) {
      bubble.appendChild(nodeOrString);
    } else {
      // Als Text einsetzen – wenn du bewusst HTML willst, erlaube innerHTML hier gezielt
      bubble.textContent = String(nodeOrString);
    }
  }

  function scheduleMove(x, y) {
    lastMouse = { x, y };
    if (MOVE_RAF.id) return;
    MOVE_RAF.id = requestAnimationFrame(() => {
      MOVE_RAF.id = 0;
      const nx = lastMouse.x + OFFSET.x;
      const ny = lastMouse.y + OFFSET.y;

      // einfache Kanten-Kollisionsvermeidung (Viewport)
      const vw = document.documentElement.clientWidth;
      const vh = document.documentElement.clientHeight;
      root.style.transform = `translate(${nx}px, ${ny}px)`;
      root.style.maxWidth = Math.min(360, vw - nx - 8) + "px";

      // wenn zu nah am unteren Rand, leicht nach oben versetzen
      const rect = root.getBoundingClientRect();
      if (rect.bottom > vh) {
        root.style.transform = `translate(${nx}px, ${Math.max(8, vh - rect.height - 8)}px)`;
      }
    });
  }

  async function resolveContent(entry, ev, el) {
    try {
      const c = entry.getContent(ev, el);
      if (c && typeof c.then === "function") {
        setContent("Lade", { loading: true });
        const resolved = await c;
        return resolved ?? null;
      }
      return c ?? null;
    } catch (err) {
      return "Fehler beim Laden des Tooltips";
    }
  }

  function bestEntryFor(el) {
    // Alle passenden Registrierungen sammeln
    const matches = registry
      .filter(r => el.closest(r.selector))
      .filter(r => (r.predicate ? r.predicate(el) : true));
    if (!matches.length) return null;
    // priorisiert auswählen
    matches.sort((a, b) => b.priority - a.priority);
    return matches[0];
  }

  async function showFor(ev, el, entry) {
    clearTimers(active);
    active = { entry, el, hideTimer: null, showTimer: null };

    // Delay optional
    const delay = entry.delay ?? 100;
    active.showTimer = setTimeout(async () => {
      // Klasse setzen
      setRootClass(entry.className);

      // Content laden
      const content = await resolveContent(entry, ev, el);
      if (active && active.entry === entry) {
        setContent(content, { loading: false });
        setRootVisible(true);
        scheduleMove(ev.clientX, ev.clientY);
      }
    }, delay);
  }

  function hideSoon() {
    if (!active) return;
    clearTimers(active);
    active.hideTimer = setTimeout(() => {
      setRootVisible(false);
      setContent("");
      active = null;
    }, 60);
  }

  // Event Delegation
  document.addEventListener("mousemove", (ev) => {
    if (!active) return;
    scheduleMove(ev.clientX, ev.clientY);
  }, { passive: true });

  document.addEventListener("mouseover", (ev) => {
    const el = /** @type {Element} */(ev.target);
    const entry = bestEntryFor(el);
    if (!entry) return;
    showFor(ev, el, entry);
  }, { passive: true });

  document.addEventListener("mouseout", (ev) => {
    if (!active) return;
    const related = ev.relatedTarget;
    // Wenn wir in ein Element wechseln, das dieselbe Regel matcht, bleib sichtbar
    if (related instanceof Element) {
      const stillMatches = related.closest(active.entry.selector);
      if (stillMatches) return;
    }
    hideSoon();
  }, { passive: true });

  // Öffentliche API
  const Tooltip = {
    /**
     * Registriert einen Tooltip.
     * @param {string} selector CSS-Selector (event delegation, kann breit sein)
     * @param {object} options
     * @param {string|Node|function} options.content String/Node oder Funktion (ev, el) => string|Node|Promise
     * @param {(el:Element)=>boolean} [options.predicate] Bedingung (true => zeigen)
     * @param {number} [options.priority=0] Priorität (höher gewinnt)
     * @param {number} [options.delay=100] Verzögerung bis Anzeige (ms)
     * @param {string} [options.className] optionaler Klassen-Mod (z.B. "tt-warn"|"tt-danger"|"tt-info")
     * @returns {() => void} unregister-Funktion
     */
    register(selector, { content, predicate, priority = 0, delay = 100, className } = {}) {
      const entry = {
        selector,
        getContent: (typeof content === "function") ? content : () => content,
        predicate, priority, delay, className
      };
      registry.push(entry);
      return () => {
        const i = registry.indexOf(entry);
        if (i >= 0) registry.splice(i, 1);
      };
    },

    // Imperativ: sofort an Position zeigen (z.B. für Debug oder programmatische Hinweise)
    showAt(x, y, content, { className } = {}) {
      clearTimers(active);
      active = { entry: { selector: "body", delay: 0, priority: 9999, className, getContent: ()=>content }, el: document.body };
      setRootClass(className);
      setContent(content);
      setRootVisible(true);
      scheduleMove(x, y);
    },

    hide() { hideSoon(); }
  };

  // Exponieren
  global.Tooltip = Tooltip;
})(window);
