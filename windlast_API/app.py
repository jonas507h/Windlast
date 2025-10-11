# --- Pfad-Shim: Projektwurzel & CORE in sys.path, für Dev **und** .exe ---
import sys
from pathlib import Path

import os, threading, time, logging
from flask import request, jsonify

# Bei .exe zeigt sys._MEIPASS auf das entpackte Temp-Verzeichnis
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))  # .../Windlast oder _MEIPASS
ROOT = BASE
CORE_DIR = ROOT / "windlast_CORE"
API_DIR  = Path(__file__).resolve().parent

for p in (str(ROOT), str(CORE_DIR), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
# -------------------------------------------------------------------------

import socket, time, webbrowser
from threading import Thread
from flask import Flask, send_from_directory, abort
from api.v1 import bp_v1  # klappt jetzt, weil ROOT/API/CORE im sys.path sind

UI_ROOT      = (ROOT / "windlast_UI").resolve()
STATIC_DIR   = (UI_ROOT / "static").resolve()
PARTIALS_DIR = (UI_ROOT / "partials").resolve()

_clients: dict[str, float] = {}           # {client_id: last_seen_ts}
_lock = threading.Lock()
_shutdown_timer: threading.Timer | None = None
HB_TIMEOUT = 8.0   # s – wenn länger kein Heartbeat, gilt Client als weg

def _schedule_shutdown(delay=0.6):
    """App beenden (auch ohne Werkzeugs Shutdown-Hook)."""
    def _do_exit():
        logging.info("shutdown now")
        time.sleep(delay)
        os._exit(0)
    t = threading.Timer(0.2, _do_exit)
    t.daemon = True
    t.start()
    return t

def _reap_and_maybe_shutdown():
    """Inaktive Clients entfernen; wenn keiner mehr da, beenden."""
    now = time.time()
    with _lock:
        stale = [cid for cid, ts in _clients.items() if now - ts > HB_TIMEOUT]
        for cid in stale:
            _clients.pop(cid, None)
        if not _clients:
            _schedule_shutdown()

def create_app():
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
    # ... deine vorhandenen Routen ...

    @app.get("/")
    def index():
        return send_from_directory(UI_ROOT, "index.html")

    @app.get("/partials/<path:filename>")
    def serve_partials(filename: str):
        target = (PARTIALS_DIR / filename).resolve()
        # Sicherstellen, dass die Datei innerhalb von PARTIALS_DIR liegt
        if not target.is_file() or PARTIALS_DIR not in target.parents:
            abort(404)
        return send_from_directory(PARTIALS_DIR, filename)

    app.register_blueprint(bp_v1, url_prefix="/api/v1")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}
    
    @app.post("/__client_event")
    def __client_event():
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"ok": False, "reason": "forbidden"}), 403

        d = request.get_json(silent=True) or {}
        ev = (d.get("event") or "").lower()
        cid = d.get("id")
        if not cid:
            return {"ok": False, "reason": "missing id"}, 400

        now = time.time()
        with _lock:
            if ev == "open" or ev == "beat":
                _clients[cid] = now
            elif ev == "close":
                _clients.pop(cid, None)

        # nach jedem Event kurz prüfen
        _reap_and_maybe_shutdown()
        return {"ok": True, "active": len(_clients)}

    return app

def find_free_port(preferred=5500, span=50):
    for p in range(preferred, preferred + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return 0

def wait_until_listening(host, port, timeout=6.0):
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.15)
    return False

def open_browser_when_ready(url, host, port):
    if wait_until_listening(host, port):
        try:
            webbrowser.open(url)
        except Exception:
            pass

if __name__ == "__main__":
    app = create_app()
    port = find_free_port() or 5000
    url = f"http://127.0.0.1:{port}"
    Thread(target=open_browser_when_ready, args=(url, "127.0.0.1", port), daemon=True).start()
    debug = not hasattr(sys, "_MEIPASS")  # Dev: True, EXE: False
    app.run(host="127.0.0.1", port=port, debug=debug)
