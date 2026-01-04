// modal/passwort.js
// Passwort-Abfrage über bestehendes Modal-System

export function askAdminPassword() {
  return new Promise((resolve) => {
    const wrap = document.createElement("div");
    wrap.className = "pw-modal";

    const title = document.createElement("h3");
    title.id = "modal-title";
    title.className = "pw-title";
    title.textContent = "Admin-Passwort";

    const hint = document.createElement("div");
    hint.className = "pw-hint";
    hint.textContent = "Bitte Admin-Passwort eingeben:";

    const input = document.createElement("input");
    input.className = "pw-input";
    input.type = "password";
    input.autocomplete = "current-password";

    const actions = document.createElement("div");
    actions.className = "pw-actions";

    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "btn pw-btn-cancel";
    cancel.textContent = "Abbrechen";

    const ok = document.createElement("button");
    ok.type = "button";
    ok.className = "btn pw-btn-ok";
    ok.textContent = "OK";

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
      onOpen: () => setTimeout(() => input.focus(), 0),
    });
  });
}

// zusätzlich global anbieten (für config.js)
window.askAdminPassword = askAdminPassword;