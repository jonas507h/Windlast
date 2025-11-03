from flask import jsonify
from . import bp_v1

# CORE: Katalog & Enums
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.datenstruktur.enums import MaterialTyp

def _options_from_dict(d, *, label_attr="anzeige_name", value_attr="name_intern"):
    items = []
    for key, spec in d.items():
        # alle Attribute des Spec übernehmen
        data = spec.__dict__.copy()

        # Standardfelder ergänzen / überschreiben
        data["value"] = getattr(spec, value_attr, key)
        data["label"] = getattr(spec, label_attr, str(spec))

        items.append(data)

    # hübsch sortieren nach Label
    items.sort(key=lambda x: (x.get("label") or "").lower())
    return items

@bp_v1.get("/catalog/traversen")
def get_traversen():
    return jsonify({"options": _options_from_dict(catalog.traversen)})

@bp_v1.get("/catalog/bodenplatten")
def get_bodenplatten():
    return jsonify({"options": _options_from_dict(catalog.bodenplatten)})

@bp_v1.get("/catalog/rohre")
def get_rohre():
    return jsonify({"options": _options_from_dict(catalog.rohre)})

@bp_v1.get("/catalog/untergruende")
def get_untergruende():
    # Enum-Werte sind bereits als Anzeigetext gedacht → value=label=Enum.value
    opts = [{"value": m.value, "label": m.value} for m in MaterialTyp]
    opts.sort(key=lambda x: x["label"])
    return jsonify({"options": opts})
