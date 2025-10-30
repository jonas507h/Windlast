// /static/js/preview/svgTrussRenderer.js
// API: SvgTrussRenderer.mount(container) -> { update(params), dispose() }
// params: { breite_m, hoehe_m, nMittelstuetzen }
// Keine Fremdbibliotheken.

(function (global) {
  const SvgTrussRenderer = {};

  // --- Mathe: Isometrische Projektion (Rz(45°) * Rx(35.264°)) ---
  const deg = Math.PI / 180;
  const AX = 35.264 * deg;  // ≈ arctan(sin(45°))
  const AZ = 45 * deg;
  const cx = Math.cos(AX), sx = Math.sin(AX);
  const cz = Math.cos(AZ), sz = Math.sin(AZ);

  function isoProject(p) {
    // Rz(AZ)
    const x1 =  cz*p.x - sz*p.y;
    const y1 =  sz*p.x + cz*p.y;
    const z1 =  p.z;
    // Rx(AX)
    const X =  x1;
    const Y =  cx*y1 - sx*z1;
    const Z =  sx*y1 + cx*z1; // Tiefe (für Sort/Dash)
    return { X, Y, Z };
  }

  // --- SVG helpers ---
  const NS = "http://www.w3.org/2000/svg";
  const S = (tag, attrs={}, children) => {
    const n = document.createElementNS(NS, tag);
    for (const [k,v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (children != null) n.textContent = children;
    return n;
  };

  function ensureDefs(svg) {
    const defs = S('defs');
    defs.appendChild(S('style', {}, `
      .edge { stroke: currentColor; stroke-width: 3; fill: none; }
      .hidden { stroke-dasharray: 8 6; opacity: .8; }
      .dim   { stroke: currentColor; stroke-width: 2; fill: none; }
      .dim-text { font: 14px system-ui, sans-serif; fill: currentColor; user-select: none; }
    `));
    // Pfeilspitze für Maße
    const marker = S('marker', { id: 'arrow', viewBox: '0 0 10 10', refX: '6', refY: '5', markerWidth: '6', markerHeight: '6', orient: 'auto-start-reverse' });
    marker.appendChild(S('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: 'currentColor' }));
    defs.appendChild(marker);
    svg.appendChild(defs);
  }

  // --- Geometrie: einfache Traversenstrecke (2 Stützen + Kopfträger) ---
  function buildModel({ breite_m=8, hoehe_m=4, nMittelstuetzen=0 }) {
    // Nodes im Weltkoordinatensystem (Meter)
    // x: horizontal, y: Tiefe (hier 0), z: vertikal
    const nodes = [];
    function addNode(x,y,z){ const id = nodes.length; nodes.push({id,x,y,z}); return id; }

    const leftBottom  = addNode(0, 0, 0);
    const leftTop     = addNode(0, 0, hoehe_m);
    const rightBottom = addNode(breite_m, 0, 0);
    const rightTop    = addNode(breite_m, 0, hoehe_m);

    // Kopfträger (oben)
    // optional: leichte Tiefe für hübschere Kanten? Wir bleiben bei y=0 (2.5D)
    const edges = [];
    function addEdge(a,b, meta={}){ edges.push({a,b, ...meta}); }

    // Stützen
    addEdge(leftBottom, leftTop);
    addEdge(rightBottom, rightTop);

    // Kopfträger
    // Teilsegmente (alle 1 m) – rein optisch
    const nSeg = Math.max(1, Math.round(breite_m));
    let last = leftTop;
    for (let i=1; i<=nSeg; i++) {
      const x = (breite_m/nSeg)*i;
      const nid = addNode(x, 0, hoehe_m);
      addEdge(last, nid);
      last = nid;
    }

    // Mittelstützen (gestrichelt)
    if (nMittelstuetzen > 0) {
      const dx = breite_m / (nMittelstuetzen + 1);
      for (let i=1; i<=nMittelstuetzen; i++) {
        const x = i*dx;
        const btm = addNode(x, 0, 0);
        const top = addNode(x, 0, hoehe_m);
        addEdge(btm, top, { dashed: true });
      }
    }

    return { nodes, edges };
  }

  function computeViewBox(projectedPoints, pad=40, scale=50) {
    let minX=Infinity, maxX=-Infinity, minY=Infinity, maxY=-Infinity;
    for (const p of projectedPoints) {
      const x = p.X*scale, y = p.Y*scale;
      if (x<minX) minX=x; if (x>maxX) maxX=x;
      if (y<minY) minY=y; if (y>maxY) maxY=y;
    }
    // Falls alles auf einem Punkt (Edgecase)
    if (!isFinite(minX)) { minX=-50; maxX=50; minY=-50; maxY=50; }
    const w = (maxX-minX) + pad*2;
    const h = (maxY-minY) + pad*2;
    const ox = minX - pad;
    const oy = minY - pad;
    return { w, h, ox, oy, scale };
  }

  function drawSvg(container, params) {
    const { breite_m=8, hoehe_m=4, nMittelstuetzen=0 } = params || {};
    const model = buildModel({ breite_m, hoehe_m, nMittelstuetzen });

    // Projektieren
    const projected = model.nodes.map(n => ({ id:n.id, ...isoProject(n) }));
    const projMap = Object.fromEntries(projected.map(p => [p.id, p]));

    // Segmente sortieren: hinten → vorne (Painter's Algorithm)
    const segs = model.edges.map(e => {
      const a = projMap[e.a], b = projMap[e.b];
      const zmid = (a.Z + b.Z)/2;
      return { a, b, dashed: !!e.dashed, zmid };
    }).sort((s1,s2) => s1.zmid - s2.zmid);

    // SVG vorbereiten
    const svg = S('svg', { class: 'svg-truss', xmlns: NS });
    ensureDefs(svg);

    // ViewBox/Scale bestimmen
    const vb = computeViewBox(projected, 50, 50);
    svg.setAttribute('viewBox', `${vb.ox} ${vb.oy} ${vb.w} ${vb.h}`);
    svg.style.width = '100%';
    svg.style.height = '100%';

    // Kanten zeichnen
    const g = S('g');
    for (const s of segs) {
      const x1 = s.a.X*vb.scale, y1 = s.a.Y*vb.scale;
      const x2 = s.b.X*vb.scale, y2 = s.b.Y*vb.scale;
      const cls = 'edge ' + ((s.zmid < 0 || s.dashed) ? 'hidden' : '');
      g.appendChild(S('line', { x1, y1, x2, y2, class: cls }));
    }
    svg.appendChild(g);

    // Maße (Breite/Höhe) – simpel, gut lesbar
    const dim = S('g');
    // Breite
    const yDim = vb.oy + vb.h - 30;
    dim.appendChild(S('line', { x1: vb.ox+60, y1: yDim, x2: vb.ox+vb.w-60, y2: yDim, class: 'dim', 'marker-start':'url(#arrow)', 'marker-end':'url(#arrow)' }));
    dim.appendChild(S('text', { x: vb.ox + vb.w/2, y: yDim + 16, class: 'dim-text', 'text-anchor':'middle' }, `Breite = ${breite_m.toFixed(2)} m`));
    // Höhe
    const xDim = vb.ox + vb.w - 30;
    dim.appendChild(S('line', { x1: xDim, y1: vb.oy+60, x2: xDim, y2: vb.oy+vb.h-60, class: 'dim', 'marker-start':'url(#arrow)', 'marker-end':'url(#arrow)' }));
    const tx = xDim + 16, ty = vb.oy + vb.h/2;
    const t = S('text', { x: tx, y: ty, class: 'dim-text', 'text-anchor':'middle', transform: `rotate(90 ${tx} ${ty})` }, `Höhe = ${hoehe_m.toFixed(2)} m`);
    dim.appendChild(t);
    svg.appendChild(dim);

    // In Container setzen
    container.innerHTML = '';
    container.appendChild(svg);
  }

  SvgTrussRenderer.mount = function mount(container) {
    if (!container) throw new Error('SvgTrussRenderer: container fehlt');

    // Initial mit Defaults
    drawSvg(container, { breite_m: 8, hoehe_m: 4, nMittelstuetzen: 2 });

    // Event-Bridge: hört auf globale Daten-Events
    function onParams(ev) {
      const p = ev.detail || {};
      drawSvg(container, p);
    }
    document.addEventListener('tor:params', onParams);

    // Responsive Redraw (bei Größenänderung neu zeichnen)
    const ro = new ResizeObserver(() => {
      // Redraw mit letzten bekannten Werten? Einfach im DOM ablesen:
      const svg = container.querySelector('svg');
      if (!svg) return;
      const last = container.__lastParams || { breite_m: 8, hoehe_m: 4, nMittelstuetzen: 2 };
      drawSvg(container, last);
    });

    ro.observe(container);

    return {
      update(params){ container.__lastParams = params; drawSvg(container, params); },
      dispose(){
        document.removeEventListener('tor:params', onParams);
        ro.disconnect();
        container.innerHTML = '';
      }
    };
  };

  global.SvgTrussRenderer = SvgTrussRenderer;
})(window);
