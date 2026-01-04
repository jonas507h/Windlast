// static/js/modal/norminfo.js
// Minimal-Adapter, damit footer.js nichts von der neuen Help-Engine wissen muss

import { getNorminfo as _getNorminfo, openNormHelp as _openNormHelp } from "./help.js";

export function getNorminfo(normKey, szenario = null) {
  return _getNorminfo(normKey, szenario);
}

export function openNormHelp(normKey, szenario = null) {
  return _openNormHelp(normKey, szenario);
}
