import sys

from threading import Thread

from windlast_API.app import (
    create_app,
    find_free_port,
    open_browser_when_ready,
)


app = create_app(local_lifecycle=True)

port = find_free_port() or 5000
host = "127.0.0.1"

url = f"http://{host}:{port}"

Thread(
    target=open_browser_when_ready,
    args=(url, host, port),
    daemon=True,
).start()

debug = not hasattr(sys, "_MEIPASS")

app.run(
    host=host,
    port=port,
    debug=debug,
    use_reloader=False,
)