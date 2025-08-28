# app.py
from flask import Flask, render_template, request, abort
from materialdaten.catalog import catalog  # zentrale Registry

app = Flask(__name__)

# Mapping: Konstruktion -> Template-Datei
KONSTRUKTIONS_TEMPLATES = {
    "tor": "konstruktionen/tor.html",
}

def context_for_konstruktion(konstruktion: str) -> dict:
    """Daten, die das jeweilige Konstruktionstemplate braucht."""
    if konstruktion == "tor":
        bodenplatten = sorted(
            catalog.bodenplatten.values(),
            key=lambda bp: bp.anzeige_name.lower()
        )
        return {"bodenplatten": bodenplatten}
    return {}

@app.route("/", methods=["GET"])   # <-- Route ist wichtig
def index():
    k = request.args.get("k", "tor")
    tpl = KONSTRUKTIONS_TEMPLATES.get(k)
    if not tpl:
        abort(404)
    ctx = context_for_konstruktion(k)
    return render_template(
        "index.html",
        konstruktion_template=tpl,
        aktive_konstruktion=k,
        **ctx
    )

if __name__ == "__main__":        # <-- Serverstart ist wichtig
    app.run(debug=True)
