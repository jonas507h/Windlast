# windlast_API/app.py
from flask import Flask, send_from_directory, abort
from pathlib import Path

# Pfade relativ zum API-Ordner:
UI_ROOT = (Path(__file__).resolve().parents[1] / "windlast_UI").resolve()
STATIC_DIR = (UI_ROOT / "static").resolve()
PARTIALS_DIR = (UI_ROOT / "partials").resolve()

def create_app():
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

    @app.get("/")
    def index():
        return send_from_directory(UI_ROOT, "index.html")

    # Partials (inkl. Unterordner wie konstruktionen/)
    @app.get("/partials/<path:filename>")
    def serve_partials(filename: str):
        target = (PARTIALS_DIR / filename).resolve()
        if not target.is_file() or PARTIALS_DIR not in target.parents and target != PARTIALS_DIR:
            abort(404)
        return send_from_directory(PARTIALS_DIR, filename)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app

if __name__ == "__main__":
    # Direkter Start: python windlast_API/app.py
    create_app().run(debug=True)
