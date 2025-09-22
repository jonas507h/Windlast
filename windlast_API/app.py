# windlast_API/app.py
# --- Pfad-Shim: Projektwurzel in sys.path, damit windlast_CORE importierbar ist ---
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]              # .../Windlast
CORE_DIR = ROOT / "windlast_CORE"                       # .../Windlast/windlast_CORE

for p in (str(ROOT), str(CORE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
# --- Ende Shim ---

from flask import Flask, send_from_directory, abort
from api.v1 import bp_v1

# Pfade relativ zur Projektwurzel:
UI_ROOT = (ROOT / "windlast_UI").resolve()
STATIC_DIR = (UI_ROOT / "static").resolve()
PARTIALS_DIR = (UI_ROOT / "partials").resolve()

def create_app():
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

    @app.get("/")
    def index():
        return send_from_directory(UI_ROOT, "index.html")

    @app.get("/partials/<path:filename>")
    def serve_partials(filename: str):
        target = (PARTIALS_DIR / filename).resolve()
        if not target.is_file() or (PARTIALS_DIR not in target.parents and target != PARTIALS_DIR):
            abort(404)
        return send_from_directory(PARTIALS_DIR, filename)
    
    # API v1 mounten
    app.register_blueprint(bp_v1, url_prefix="/api/v1")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
