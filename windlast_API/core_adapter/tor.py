from typing import Dict, Any
from math import isfinite
from windlast_CORE.konstruktionen.tor import Tor
from windlast_CORE.datenstruktur.enums import (
    MaterialTyp, Zeitfaktor, Windzone as WindzoneEnum, Norm, Nachweis
)
from windlast_CORE.datenstruktur.zeit import Dauer
from windlast_CORE.rechenfunktionen.standsicherheit import standsicherheit

# Norm-Key-Mapping für API-Ausgabe
_NORM_KEY = {
    Norm.DIN_EN_13814_2005_06: "EN_13814_2005",
    Norm.DIN_EN_17879_2024_08: "EN_17879_2024",
    Norm.DIN_EN_1991_1_4_2010_12: "EN_1991_1_4_2010",
}

def _jsonify_number(x):
    try:
        v = float(x)
    except Exception:
        return None
    if isfinite(v):
        return v
    # Information erhalten, aber JSON-sicher
    return "INF" if v > 0 else "-INF"

def _set_untergrund_bodenplatten(tor: Tor, mat: MaterialTyp) -> None:
    for el in getattr(tor, "bauelemente", []):
        if el.__class__.__name__ == "Bodenplatte":
            el.untergrund = mat

def berechne_tor(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Tor bauen
    tor = Tor(
        breite=payload["breite_m"],
        hoehe=payload["hoehe_m"],
        traverse_name_intern=payload["traverse_name_intern"],
        bodenplatte_name_intern=payload["bodenplatte_name_intern"],
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

    # 5) Auf Minimalformat mappen (nur 9 Werte)
    out: Dict[str, Dict[str, float | None]] = {}
    for norm, nres in er.normen.items():
        key = _NORM_KEY.get(norm)
        if not key:
            continue
        out[key] = {
            "kipp":   _jsonify_number(nres.werte.get(Nachweis.KIPP).wert)   if Nachweis.KIPP   in nres.werte else None,
            "gleit":  _jsonify_number(nres.werte.get(Nachweis.GLEIT).wert)  if Nachweis.GLEIT  in nres.werte else None,
            "abhebe": _jsonify_number(nres.werte.get(Nachweis.ABHEBE).wert) if Nachweis.ABHEBE in nres.werte else None,
        }

    return {
        "normen": out,
        "meta": {
            "version": er.meta.version,
            "eingaben": {
                "breite_m": payload["breite_m"],
                "hoehe_m": payload["hoehe_m"],
                "traverse_name_intern": payload["traverse_name_intern"],
                "bodenplatte_name_intern": payload["bodenplatte_name_intern"],
                "untergrund_typ": payload["untergrund_typ"],
                "aufstelldauer": payload.get("aufstelldauer"),
                "windzone": payload["windzone"],
            },
        },
    }
