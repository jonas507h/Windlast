// utils/number.js

export function isPositiveNumber(v) {
  return typeof v === "number" && isFinite(v) && v > 0;
}
