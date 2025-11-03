// render_konstruktion.js — Minimaler Linien-Renderer (aufgeteilt in Module)
// V0: Bodenplatte = Viereck (lokale Katalog-Defaults in Modul),
//     Traversenstrecke = ein Segment von start → ende

import * as THREE from '/static/vendor/three.module.js';
import { OrbitControls } from '/static/vendor/OrbitControls.js';
import { bodenplatte_linien } from './linien_bodenplatte.js';
import { traversenstrecke_linien } from './linien_traverse.js';
import { computeAABB, expandAABB, segmentsToThreeLineSegments, fitCameraToAABB } from './linien_helpers.js';
import { render_dimensions } from './render_dimensions.js';
import { computeDimensionsTor } from './dimensions_tor.js';

export function render_konstruktion(konstruktion, opts = {}) {
  const container = opts.container || document.body;
  const width = Math.max(1, opts.width || container.clientWidth || 800);
  const height = Math.max(1, opts.height || container.clientHeight || 600);

  // 1) Linien sammeln
  const allSegments = [];
  for (const el of konstruktion.bauelemente || []) {
    if (el.typ === 'Bodenplatte') {
      const { segments } = bodenplatte_linien(el);
      allSegments.push(...segments);
    } else if (el.typ === 'Traversenstrecke') {
      const { segments } = traversenstrecke_linien(el);
      allSegments.push(...segments);
    }
  }
  if (!allSegments.length) { console.warn('render_konstruktion: keine Segmente'); return null; }

  // 2) Three.js Grundsetup
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 1000);
  camera.up.set(0, 0, 1);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  scene.add(new THREE.AxesHelper(1));

  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  // 3) Linien-Mesh bauen und Szene hinzufügen
  const lines = segmentsToThreeLineSegments(allSegments);
  scene.add(lines);

  // 4) Kamera auf Bounding Box fitten
  const aabb = expandAABB(computeAABB(allSegments), 0.15);
  fitCameraToAABB(camera, aabb);
  // Maße (Preview-spezifisch)
  if (opts.showDimensions !== false && konstruktion?.typ === 'Tor') {
    const specs = computeDimensionsTor(konstruktion);
    render_dimensions(specs, { scene });
  }

  // Controls
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = true;
  controls.screenSpacePanning = true; // bei Z-up angenehm
  controls.minDistance = 0.1;
  controls.target.copy(new THREE.Vector3(
    (aabb.min.x + aabb.max.x) * 0.5,
    (aabb.min.y + aabb.max.y) * 0.5,
    (aabb.min.z + aabb.max.z) * 0.5
  ));
  controls.update();

  // Resize-Handler (Container-responsiv)
  function onResize() {
    const w = Math.max(1, container.clientWidth || width);
    const h = Math.max(1, container.clientHeight || height);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  window.addEventListener('resize', onResize);

  // Render-Loop
  let disposed = false;
  function animate() {
    if (disposed) return;
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // Rückgabe inkl. Dispose
  return {
    scene, camera, renderer, lines, controls,
    dispose() {
      disposed = true;
      window.removeEventListener('resize', onResize);
      renderer.dispose?.();
    }
  };
}
