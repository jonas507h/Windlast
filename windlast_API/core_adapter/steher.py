from typing import Dict, Any
from math import isfinite
from windlast_CORE.konstruktionen.steher import Steher
from windlast_CORE.datenstruktur.enums import (
    MaterialTyp, Zeitfaktor, Windzone as WindzoneEnum, Norm, Nachweis, TraversenOrientierung
)
from windlast_CORE.datenstruktur.zeit import Dauer
from windlast_CORE.rechenfunktionen.standsicherheit import standsicherheit
from .ergebnis_mapper import build_api_output

# Hilfsfunktion: Untergrund für alle Bodenplatten im Steher setzen
def _set_untergrund_bodenplatten(steher: Steher, mat: MaterialTyp) -> None:
    for el in getattr(steher, "bauelemente", []):
        if el.__class__.__name__ == "Bodenplatte":
            el.untergrund = mat

# Hauptfunktion: Steher berechnen
def berechne_steher(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Steher bauen
    steher = Steher(
        hoehe=payload["hoehe_m"],
        rohr_laenge=payload["rohr_laenge_m"],
        rohr_hoehe=payload["rohr_hoehe_m"],
        traverse_name_intern=payload["traverse_name_intern"],
        bodenplatte_name_intern=payload["bodenplatte_name_intern"],
        rohr_name_intern=payload["rohr_name_intern"],
        gummimatte_vorhanden=payload.get("gummimatte", True),
    )

    # 2) Untergrund setzen
    try:
        mat = MaterialTyp(payload["untergrund_typ"])
    except Exception as e:
        raise ValueError(f"Unbekannter untergrund_typ: {payload['untergrund_typ']}") from e
    _set_untergrund_bodenplatten(steher, mat)

    # 3) Header-Inputs -> Enums
    if payload.get("aufstelldauer"):
        da = payload["aufstelldauer"]
        aufstelldauer = Dauer(wert=int(da["wert"]), einheit=Zeitfaktor[da["einheit"]])
    else:
        aufstelldauer = None

    try:
        windzone = WindzoneEnum[payload["windzone"]]
    except Exception as e:
        raise ValueError(f"Unbekannte windzone: {payload['windzone']}") from e

    # 4) Rechnen (liefert reiches Ergebnis-Objekt)
    er = standsicherheit(
        steher,
        aufstelldauer=aufstelldauer,
        windzone=windzone,
        # optional: konst=..., methode=..., vereinfachung_konstruktion=..., anzahl_windrichtungen=...
    )

    # 5) Auf Minimalformat mappen
    return build_api_output(er, payload)
