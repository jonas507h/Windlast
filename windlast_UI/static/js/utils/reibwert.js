// utils/reibwert.js
import { fetchJSON, apiUrl } from "./api.js";

export async function fetchKompatibilitaet({ bodenplatte, gummimatte }) {
  const qs = new URLSearchParams({
    bodenplatte,
    gummimatte: gummimatte || "nein",
  });

  const res = await fetchJSON(apiUrl(`reibwert/kompatibilitaet?${qs.toString()}`));
  return res;
}