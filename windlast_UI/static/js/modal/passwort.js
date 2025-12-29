// modal/passwort.js
// Passwort-Abfrage über bestehendes Modal-System

export function askAdminPassword() {
  return new Promise((resolve) => {
    const wrap = document.createElement("div");

    const title = document.createElement("h3");
    title.id = "modal-title";
    title.textContent = "Admin-Passwort";

    const hint = document.createElement("div");
    hint.textContent = "Bitte Admin-Passwort eingeben:";
    hint.style.marginBottom = "10px";
    hint.style.opacity = "0.85";

    const input = document.createElement("input");
    input.type = "password";
    input.autocomplete = "current-password";
    input.style.width = "100%";
    input.style.boxSizing = "border-box";
    input.style.padding = "10px 12px";
    input.style.borderRadius = "10px";
    input.style.border = "1px solid var(--master-border, #414141)";
    input.style.background = "var(--master-bg, #0b0e13)";
    input.style.color = "var(--master-text, #e8eef9)";
    input.style.marginBottom = "14px";

    const actions = document.createElement("div");
    actions.style.display = "flex";
    actions.style.justifyContent = "flex-end";
    actions.style.gap = "10px";

    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.textContent = "Abbrechen";

    const ok = document.createElement("button");
    ok.type = "button";
    ok.textContent = "OK";
    ok.style.background = "var(--master-accent, #fdc300)";
    ok.style.color = "var(--master-on-accent, #000)";
    ok.style.borderRadius = "10px";
    ok.style.padding = "8px 12px";

    actions.appendChild(cancel);
    actions.appendChild(ok);

    wrap.appendChild(title);
    wrap.appendChild(hint);
    wrap.appendChild(input);
    wrap.appendChild(actions);

    const done = (val) => {
      Modal.close();
      resolve(val);
    };

    cancel.addEventListener("click", () => done(null));
    ok.addEventListener("click", () => done(input.value || ""));

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") done(input.value || "");
      if (e.key === "Escape") done(null);
    });

    Modal.open(wrap, {
      onOpen: () => {
        setTimeout(() => input.focus(), 0);
      }
    });
  });
}

// zusätzlich global anbieten (für config.js / APP_STATE.requestAdmin)
window.askAdminPassword = askAdminPassword;