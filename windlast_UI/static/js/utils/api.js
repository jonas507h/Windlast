// utils/api.js

const API_BASE = "/api/v1";


export function apiUrl(path) {
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }

  return `${API_BASE}${path}`;
}


export async function fetchJSON(url, opts = {}) {
  let res;

  try {
    res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        ...(opts.headers ?? {}),
      },
      ...opts,
    });

  } catch (err) {
    throw new Error(`Netzwerkfehler: ${err.message}`);
  }


  if (!res.ok) {
    let message = res.statusText;

    try {
      const data = await res.json();

      message =
        data?.error?.message ??
        data?.message ??
        message;

    } catch {
      const text = await res.text().catch(() => "");

      if (text) {
        message = text;
      }
    }

    throw new Error(
      `HTTP ${res.status}: ${message}`
    );
  }


  try {
    return await res.json();

  } catch {
    throw new Error(
      "Serverantwort enthält kein gültiges JSON."
    );
  }
}

export async function fetchOptions(url) {
  const data = await fetchJSON(url);
  return data.options || [];
}

export async function fetchText(url, opts = {}) {
  let res;

  try {
    res = await fetch(url, {
      ...opts,
      headers: {
        ...(opts.headers ?? {}),
      },
    });
  } catch (err) {
    throw new Error(`Netzwerkfehler: ${err.message}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `HTTP ${res.status}: ${text || res.statusText}`
    );
  }

  return res.text();
}