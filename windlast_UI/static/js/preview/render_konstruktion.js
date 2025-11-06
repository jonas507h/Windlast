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

function createUnlitPlateMesh(THREE, polygon, frame) {
  const { u, v, n, C } = frame;

  // 2D-Shape im lokalen Frame (x = v, y = u)
  const shape = new THREE.Shape();
  for (let i = 0; i < polygon.length; i++) {
    const rel = {
      x: polygon[i][0] - C[0],
      y: polygon[i][1] - C[1],
      z: polygon[i][2] - C[2],
    };
    // x = u (Tiefe), y = v (Breite)
    const xu = rel.x * u[0] + rel.y * u[1] + rel.z * u[2];
    const yv = rel.x * v[0] + rel.y * v[1] + rel.z * v[2];
    if (i === 0) shape.moveTo(xu, yv); else shape.lineTo(xu, yv);
  }
  shape.closePath();

  const geom = new THREE.ShapeGeometry(shape);
  const mat = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    side: THREE.DoubleSide,   // ← von oben UND unten sichtbar
    depthWrite: true,
    depthTest: true,
    polygonOffset: true,      // ↓ minimiert Z-Fighting mit deinen Linien
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1
  });

  const mesh = new THREE.Mesh(geom, mat);

  // Vollständige Orientierung: Basis (x=u, y=v, z=n)
  const uVec = new THREE.Vector3(u[0], u[1], u[2]).normalize();
  const vVec = new THREE.Vector3(v[0], v[1], v[2]).normalize();
  const nVec = new THREE.Vector3(n[0], n[1], n[2]).normalize();
  const basis = new THREE.Matrix4().makeBasis(uVec, vVec, nVec); // right-handed, da u × v = n
  const q = new THREE.Quaternion().setFromRotationMatrix(basis);
  mesh.quaternion.copy(q);
  mesh.position.set(C[0], C[1], C[2]);

  // Damit die Linien sicher “oben” liegen:
  mesh.renderOrder = 0;

  return mesh;
}

export function render_konstruktion(container, konstruktion, opts = {}) {
  const preserveView = opts.preserveView ?? false;
  const prevView = opts.prevView ?? null;

  // Falls vom letzten Render vorhanden: Position/Rotation & Controls-Target merken
  let initialView = null;
  if (preserveView && prevView?.camera) {
    initialView = {
      camPos: prevView.camera.position.clone(),
      camQuat: prevView.camera.quaternion.clone(),
      controlsTarget: prevView.controls?.target?.clone?.() || null,
    };
  }

  const width = Math.max(1, opts.width || container.clientWidth || 800);
  const height = Math.max(1, opts.height || container.clientHeight || 600);

  // 1) Linien sammeln
  const allSegments = [];
  const plateMeshes = [];
  let lines = null;

  for (const el of konstruktion.bauelemente || []) {
    if (el.typ === 'Bodenplatte') {
      const data = bodenplatte_linien(el);
      allSegments.push(...(data.segments || []));
      if (data.polygon && data.frame) {
        const m = createUnlitPlateMesh(THREE, data.polygon, data.frame);
        plateMeshes.push(m);
      }
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
  //scene.add(new THREE.AxesHelper(1));

  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  // 3) Linien-Mesh bauen und Szene hinzufügen
  if (allSegments.length) {
    lines = segmentsToThreeLineSegments(allSegments);
    lines.renderOrder = 1;
    scene.add(lines);
  }

  for (const m of plateMeshes) scene.add(m);

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

  // ===== Blick erhalten, falls gewünscht =====
  if (initialView) {
    camera.position.copy(initialView.camPos);
    camera.quaternion.copy(initialView.camQuat);
    if (controls && initialView.controlsTarget) {
      controls.target.copy(initialView.controlsTarget);
      controls.update();
    }
  }

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
    plateMeshes,
    dispose() {
      disposed = true;
      window.removeEventListener('resize', onResize);
      renderer.dispose?.();
    }
  };
}
