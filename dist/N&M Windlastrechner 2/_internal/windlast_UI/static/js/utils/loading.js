export function showLoading() {
  const el = document.getElementById("loading-overlay");
  if (el) el.style.display = "flex";
}

export function hideLoading() {
  const el = document.getElementById("loading-overlay");
  if (el) el.style.display = "none";
}
