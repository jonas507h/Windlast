// render_konstruktion.js — Minimaler Linien-Renderer (aufgeteilt in Module)
// V0: Bodenplatte = Viereck (lokale Katalog-Defaults in Modul),
//     Traversenstrecke = ein Segment von start → ende

import * as THREE from '/static/vendor/three.module.js';
import { bodenplatte_linien } from './linien_bodenplatte.js';
import { traversenstrecke_linien } from './linien_traverse.js';
import { computeAABB, expandAABB, segmentsToThreeLineSegments, fitCameraToAABB } from './linien_helpers.js';

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

  // 5) Rendern (einmalig)
  renderer.render(scene, camera);
  return { scene, camera, renderer, lines };
}
