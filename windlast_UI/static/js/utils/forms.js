// utils/forms.js

export function fillSelect(el, options, { placeholder = null, defaultValue = null } = {}) {
  el.innerHTML = "";
  if (placeholder) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    el.appendChild(opt);
  }
  for (const { value, label } of options) {
    if (value.startsWith("test_") && !window.APP_STATE?.flags?.show_test_options_dropdown) {
      continue;
    }
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    el.appendChild(opt);
  }
  if (defaultValue !== null && defaultValue !== undefined) {
    el.value = defaultValue;
  }
}