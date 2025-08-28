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
        traversen = sorted(catalog.traversen.values(),
                           key=lambda tr: tr.anzeige_name.lower())
        return {"bodenplatten": bodenplatten, "traversen": traversen}
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
    selected_traverse = None
    eingabe_breite_m = None
    eingabe_hoehe_m = None

    if k == "tor":
        selected_bodenplatte = (
            request.form.get("bodenplatte_name_intern")
            or request.args.get("bodenplatte_name_intern")
            or None
        )
        selected_traverse = (
            request.form.get("traverse_name_intern")
            or request.args.get("traverse_name_intern")
            or None
        )
        if request.method == "POST":
            # Strings -> float (leere Strings zu None behandeln)
            def as_float(s):
                return float(s) if (s is not None and s != "") else None

            eingabe_breite_m = as_float(request.form.get("breite_m"))
            eingabe_hoehe_m  = as_float(request.form.get("hoehe_m"))

            from konstruktionen import Tor
            tor = Tor(
                bodenplatte_name_intern=selected_bodenplatte,
                anzahl_bodenplatten=2,
                traverse_name_intern=selected_traverse,
                breite_m=eingabe_breite_m,
                hoehe_m=eingabe_hoehe_m,
            )
            # Gewicht (aktuell nur Bodenplatten – Traversen kommen im nächsten Schritt dazu)
            gesamtgewicht = tor.gesamtgewicht()

    return render_template(
        "index.html",
        gesamtgewicht=gesamtgewicht,
        selected_bodenplatte=selected_bodenplatte,
        selected_traverse=selected_traverse, 
        eingabe_breite_m=eingabe_breite_m,
        eingabe_hoehe_m=eingabe_hoehe_m,
        **ctx,
    )

if __name__ == "__main__":        # <-- Serverstart ist wichtig
    app.run(debug=True)
