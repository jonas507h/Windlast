let RESOURCE_MAP = {};

export async function loadResources() {
  const res = await fetch("/api/v1/resources");

  if (!res.ok) {
    throw new Error(`Resources konnten nicht geladen werden: ${res.status}`);
  }

  const data = await res.json();
  RESOURCE_MAP = data.resources || {};

  return RESOURCE_MAP;
}

export function resolveResource(key, fallback = null) {
  if (!key) return fallback;

  if (Object.prototype.hasOwnProperty.call(RESOURCE_MAP, key)) {
    return RESOURCE_MAP[key];
  }

  return fallback ?? `[missing: ${key}]`;
}

export function getResourceMap() {
  return { ...RESOURCE_MAP };
}