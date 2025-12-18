// utils/reibwert.js

export async function fetchKompatibilitaet({ bodenplatte, gummimatte }) {
  const qs = new URLSearchParams({
    bodenplatte,
    gummimatte: gummimatte || "nein",
  });

  const res = await fetch(`/api/v1/reibwert/kompatibilitaet?${qs.toString()}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) throw new Error(`Kompatibilität HTTP ${res.status}`);
  return res.json();
}
