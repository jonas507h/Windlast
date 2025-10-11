# --- Pfad-Shim: Projektwurzel & CORE in sys.path, für Dev **und** .exe ---
import sys
from pathlib import Path

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

def create_app():
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

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
