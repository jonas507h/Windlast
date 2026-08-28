export function startClientLifecycle() {
  if (!window.Runtime?.isLocal) {
    return;
  }

  const KEY = "windlast_client_id";

  let id = sessionStorage.getItem(KEY);

  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(KEY, id);
  }

  function send(event) {
    const payload = JSON.stringify({
      event,
      id,
      t: Date.now()
    });

    try {
      const blob = new Blob(
        [payload],
        { type: "application/json" }
      );

      if (
        navigator.sendBeacon &&
        navigator.sendBeacon(
          "/__client_event",
          blob
        )
      ) {
        return;
      }

    } catch {}

    fetch("/__client_event", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: payload,
      keepalive: true
    }).catch(() => {});
  }

  window.addEventListener(
    "pageshow",
    () => send("open"),
    { once: true }
  );

  const heartbeat = setInterval(
    () => send("beat"),
    3000
  );

  const close = () => {
    try {
      clearInterval(heartbeat);
    } catch {}

    send("close");
  };

  window.addEventListener(
    "pagehide",
    close
  );

  window.addEventListener(
    "beforeunload",
    close
  );
}