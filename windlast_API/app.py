import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from runtime import RuntimeMode


# ============================================================
# Projektpfade / Import-Shim
# ============================================================

# Bei .exe zeigt sys._MEIPASS auf das entpackte Temp-Verzeichnis.
BASE = Path(
    getattr(
        sys,
        "_MEIPASS",
        Path(__file__).resolve().parents[1],
    )
)

ROOT = BASE
CORE_DIR = ROOT / "windlast_CORE"
API_DIR = Path(__file__).resolve().parent

for path in (ROOT, CORE_DIR, API_DIR):
    path_str = str(path)

    if path_str not in sys.path:
        sys.path.insert(0, path_str)


# Import erst nach dem Pfad-Shim
from api.v1 import bp_v1


# ============================================================
# UI-Pfade
# ============================================================

UI_ROOT = (ROOT / "windlast_UI").resolve()
STATIC_DIR = (UI_ROOT / "static").resolve()
PARTIALS_DIR = (UI_ROOT / "partials").resolve()


# ============================================================
# Lokaler Browser-Lifecycle
# ============================================================

HB_TIMEOUT = 900       # s ohne Heartbeat -> Client gilt als weg
HK_PERIOD = 2.0        # s Housekeeper-Intervall
GRACE = 10             # s Gnadenfrist vor Shutdown
STARTUP_GRACE = 300    # s Wartezeit nach Programmstart

_clients: dict[str, float] = {}
_lock = threading.Lock()

_ever_had_client = False
_start_ts = time.time()

_shutdown_timer: threading.Timer | None = None
_housekeeper_started = False


def _cancel_shutdown():
    global _shutdown_timer

    if _shutdown_timer is not None:
        _shutdown_timer.cancel()
        _shutdown_timer = None


def _schedule_shutdown():
    """Plant den Shutdown der lokalen Anwendung nach GRACE Sekunden."""
    global _shutdown_timer

    _cancel_shutdown()

    def _do_exit():
        logging.info("shutdown now")
        os._exit(0)

    timer = threading.Timer(GRACE, _do_exit)
    timer.daemon = True
    timer.start()

    _shutdown_timer = timer


def _reap_stale(now: float | None = None):
    """Entfernt Clients ohne Heartbeat > HB_TIMEOUT."""
    if now is None:
        now = time.time()

    stale = [
        client_id
        for client_id, last_seen in _clients.items()
        if now - last_seen > HB_TIMEOUT
    ]

    for client_id in stale:
        _clients.pop(client_id, None)


def _ensure_housekeeper():
    """Startet den Housekeeper für den lokalen Browser-Lifecycle."""
    global _housekeeper_started

    if _housekeeper_started:
        return

    def _loop():
        while True:
            time.sleep(HK_PERIOD)

            now = time.time()

            with _lock:
                _reap_stale(now)

                if _clients:
                    continue

                # Beim Start nicht beenden, bevor jemals ein Client da war.
                if (
                    not _ever_had_client
                    and (now - _start_ts) < STARTUP_GRACE
                ):
                    continue

                if _shutdown_timer is None:
                    _schedule_shutdown()

    thread = threading.Thread(
        target=_loop,
        daemon=True,
    )

    thread.start()

    _housekeeper_started = True


# ============================================================
# Flask-App
# ============================================================

def create_app(
    *,
    runtime_mode: RuntimeMode = RuntimeMode.LOCAL,
):
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
    )

    # Runtime-Modus zentral in der Flask-Konfiguration ablegen.
    app.config["RUNTIME_MODE"] = runtime_mode


    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    @app.get("/")
    def index():
        return send_from_directory(
            UI_ROOT,
            "index.html",
        )


    @app.get("/partials/<path:filename>")
    def serve_partials(filename: str):
        target = (PARTIALS_DIR / filename).resolve()

        # Sicherstellen, dass die Datei innerhalb von PARTIALS_DIR liegt.
        if (
            not target.is_file()
            or PARTIALS_DIR not in target.parents
        ):
            abort(404)

        return send_from_directory(
            PARTIALS_DIR,
            filename,
        )


    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    app.register_blueprint(
        bp_v1,
        url_prefix="/api/v1",
    )


    # --------------------------------------------------------
    # System-Endpunkte
    # --------------------------------------------------------

    @app.get("/healthz")
    def healthz():
        return {
            "status": "ok",
        }


    @app.get("/licenses")
    def licenses():
        return send_from_directory(
            ROOT,
            "THIRD_PARTY_NOTICES.txt",
        )


    # --------------------------------------------------------
    # Lokaler Browser-Lifecycle
    # --------------------------------------------------------

    if runtime_mode == RuntimeMode.LOCAL:
        _ensure_housekeeper()


    @app.post("/__client_event")
    def client_event():
        global _ever_had_client

        # Auf dem Server hat der Browser-Lifecycle keine Bedeutung.
        if runtime_mode != RuntimeMode.LOCAL:
            return {
                "ok": True,
                "active": None,
            }

        if request.remote_addr not in (
            "127.0.0.1",
            "::1",
        ):
            return jsonify({
                "ok": False,
                "reason": "forbidden",
            }), 403

        data = request.get_json(silent=True) or {}

        event = (data.get("event") or "").lower()
        client_id = data.get("id")

        if not client_id:
            return {
                "ok": False,
                "reason": "missing id",
            }, 400

        now = time.time()

        with _lock:
            if event in ("open", "beat"):
                _ever_had_client = True

                _clients[client_id] = now

                _reap_stale(now)
                _cancel_shutdown()

            elif event == "close":
                _clients.pop(client_id, None)

                _reap_stale(now)

                if not _clients:
                    _schedule_shutdown()

        return {
            "ok": True,
            "active": len(_clients),
        }


    return app


# ============================================================
# Helfer für lokalen Programmstart
# ============================================================

def find_free_port(
    preferred: int = 5500,
    span: int = 50,
):
    for port in range(
        preferred,
        preferred + span,
    ):
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as sock:
            try:
                sock.bind(
                    ("127.0.0.1", port)
                )

                return port

            except OSError:
                continue

    return 0


def wait_until_listening(
    host: str,
    port: int,
    timeout: float = 6.0,
):
    end = time.time() + timeout

    while time.time() < end:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as sock:
            sock.settimeout(0.3)

            try:
                sock.connect(
                    (host, port)
                )

                return True

            except OSError:
                time.sleep(0.15)

    return False


def open_browser_when_ready(
    url: str,
    host: str,
    port: int,
):
    if not wait_until_listening(
        host,
        port,
    ):
        return

    try:
        webbrowser.open(url)

    except Exception:
        pass