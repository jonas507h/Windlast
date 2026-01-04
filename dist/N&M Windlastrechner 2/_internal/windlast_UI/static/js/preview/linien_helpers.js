// linien_helpers.js — kleine Utilities für Linien-Rendering
import * as THREE from '/static/vendor/three.module.js';
import { LineSegments2 } from '/static/vendor/lines/LineSegments2.js';
import { LineSegmentsGeometry } from '/static/vendor/lines/LineSegmentsGeometry.js';
import { LineMaterial } from '/static/vendor/lines/LineMaterial.js';

export function computeAABB(segments) {
  if (!segments.length) return { min: new THREE.Vector3(), max: new THREE.Vector3() };
  const min = new THREE.Vector3(+Infinity, +Infinity, +Infinity);
  const max = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
  for (const [a, b] of segments) {
    for (const p of [a, b]) {
      min.x = Math.min(min.x, p[0]); min.y = Math.min(min.y, p[1]); min.z = Math.min(min.z, p[2]);
      max.x = Math.max(max.x, p[0]); max.y = Math.max(max.y, p[1]); max.z = Math.max(max.z, p[2]);
    }
  }
  return { min, max };
}

export function expandAABB(aabb, pad = 0.1) {
  const size = new THREE.Vector3().subVectors(aabb.max, aabb.min);
  const padVec = size.multiplyScalar(pad);
  return {
    min: new THREE.Vector3().subVectors(aabb.min, padVec),
    max: new THREE.Vector3().addVectors(aabb.max, padVec),
  };
}

export function segmentsToThreeLineSegments(segments, color = 0x111111) {
  const points = [];
  for (const [a, b] of segments) {
    points.push(a[0], a[1], a[2], b[0], b[1], b[2]);
  }
  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
  const mat = new THREE.LineBasicMaterial({ linewidth: 1, color});
  return new THREE.LineSegments(geom, mat);
}

export function segmentsToThreeLineSegments2(segments, color, linewidthPx, width, height) {
  const positions = new Float32Array(segments.length * 2 * 3);
  let i = 0;

  for (const [a, b] of segments) {
    positions[i++] = a[0]; positions[i++] = a[1]; positions[i++] = a[2];
    positions[i++] = b[0]; positions[i++] = b[1]; positions[i++] = b[2];
  }

  const geometry = new LineSegmentsGeometry();
  geometry.setPositions(positions);

  const material = new LineMaterial({
    color,
    linewidth: linewidthPx,  // Pixelbreite (weil worldUnits:false)
    worldUnits: false,
    depthTest: true,
    depthWrite: true,
  });

  // extrem wichtig, sonst skaliert die Dicke komisch / gar nicht
  material.resolution.set(width, height);

  const line = new LineSegments2(geometry, material);
  return line;
}

export function fitCameraToAABB(camera, aabb) {
  const center = new THREE.Vector3().addVectors(aabb.min, aabb.max).multiplyScalar(0.5);
  const size = new THREE.Vector3().subVectors(aabb.max, aabb.min);
  const diag = Math.max(1e-3, size.length());
  camera.position.set(center.x - diag, center.y - diag, center.z + diag * 0.6);
  camera.near = 0.01;
  camera.far = diag * 10 + 10;
  camera.updateProjectionMatrix();
}
