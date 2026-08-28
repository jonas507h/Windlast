from windlast_API.app import create_app
from windlast_API.runtime import RuntimeMode


app = create_app(
    runtime_mode=RuntimeMode.SERVER,
)

app.run(
    host="0.0.0.0",
    port=5500,
    debug=False,
    use_reloader=False,
)