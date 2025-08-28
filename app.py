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

@app.route("/", methods=["GET", "POST"])
def index():
    k = request.args.get("k", "tor")
    tpl = KONSTRUKTIONS_TEMPLATES.get(k) or abort(404)

    # Grundkontext (Dropdown-Daten etc.)
    ctx = dict(konstruktion_template=tpl, aktive_konstruktion=k)
    ctx.update(context_for_konstruktion(k))

    gesamtgewicht = None
    selected_bodenplatte = None

    if k == "tor":
        selected_bodenplatte = (
            request.form.get("bodenplatte_name_intern")
            or request.args.get("bodenplatte_name_intern")
            or None
        )
        if request.method == "POST" and selected_bodenplatte:
            from konstruktionen import Tor
            tor = Tor(bodenplatte_name_intern=selected_bodenplatte, anzahl_bodenplatten=2)
            gesamtgewicht = tor.gesamtgewicht()

    return render_template(
        "index.html",
        gesamtgewicht=gesamtgewicht,
        selected_bodenplatte=selected_bodenplatte,
        **ctx,
    )

if __name__ == "__main__":        # <-- Serverstart ist wichtig
    app.run(debug=True)
