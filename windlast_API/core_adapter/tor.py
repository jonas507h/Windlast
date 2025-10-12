from typing import Dict, Any
from math import isfinite
from windlast_CORE.konstruktionen.tor import Tor
from windlast_CORE.datenstruktur.enums import (
    MaterialTyp, Zeitfaktor, Windzone as WindzoneEnum, Norm, Nachweis
)
from windlast_CORE.datenstruktur.zeit import Dauer
from windlast_CORE.rechenfunktionen.standsicherheit import standsicherheit
from .ergebnis_mapper import build_api_output

# Hilfsfunktion: Untergrund für alle Bodenplatten im Tor setzen
def _set_untergrund_bodenplatten(tor: Tor, mat: MaterialTyp) -> None:
    for el in getattr(tor, "bauelemente", []):
        if el.__class__.__name__ == "Bodenplatte":
            el.untergrund = mat

# Hauptfunktion: Tor berechnen
def berechne_tor(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Tor bauen
    tor = Tor(
        breite=payload["breite_m"],
        hoehe=payload["hoehe_m"],
        traverse_name_intern=payload["traverse_name_intern"],
        bodenplatte_name_intern=payload["bodenplatte_name_intern"],
        gummimatte_vorhanden=payload.get("gummimatte", True),
    )

    # 2) Untergrund setzen
    try:
        mat = MaterialTyp(payload["untergrund_typ"])
    except Exception as e:
        raise ValueError(f"Unbekannter untergrund_typ: {payload['untergrund_typ']}") from e
    _set_untergrund_bodenplatten(tor, mat)

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
        tor,
        aufstelldauer=aufstelldauer,
        windzone=windzone,
        # optional: konst=..., methode=..., vereinfachung_konstruktion=..., anzahl_windrichtungen=...
    )

    # 5) Auf Minimalformat mappen
    return build_api_output(er, payload)
