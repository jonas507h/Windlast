from flask import jsonify
from . import bp_v1

# CORE-Enums importieren
from windlast_CORE.datenstruktur.enums import Zeitfaktor, Windzone

def _enum_to_options(enum_cls):
    # value = Enum-Member-Name (stabil fürs Backend), label = Anzeige-String (deine .value)
    return [{"value": member.name, "label": member.value} for member in enum_cls]

@bp_v1.get("/config/dauer-einheiten")
def get_dauer_einheiten():
    return jsonify({"options": _enum_to_options(Zeitfaktor)})

@bp_v1.get("/config/windzonen")
def get_windzonen():
    return jsonify({"options": _enum_to_options(Windzone)})
