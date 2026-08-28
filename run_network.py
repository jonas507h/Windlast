from windlast_API.app import create_app


app = create_app(local_lifecycle=False)

app.run(
    host="0.0.0.0",
    port=5500,
    debug=False,
    use_reloader=False,
)