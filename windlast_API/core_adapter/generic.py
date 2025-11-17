from typing import Dict, Any

from windlast_CORE.konstruktionen.generic import Konstruktion
from windlast_CORE.datenstruktur.enums import Zeitfaktor, Windzone as WindzoneEnum
from windlast_CORE.datenstruktur.zeit import Dauer
from windlast_CORE.rechenfunktionen.standsicherheit import standsicherheit

from .ergebnis_mapper import build_api_output

def _build_konstruktion_from_payload(konstr_dict: Dict[str, Any]) -> Konstruktion:
    """
    Erwartet das Objekt, das aus dem UI-Build kommt:
      {
        version: 1,
        typ: 'Tor' | 'Steher' | 'Tisch' | ...,
        name: '...',
        bauelemente: [...],
        ...
      }
    """
    name = konstr_dict.get("name") or konstr_dict.get("typ") or "Konstruktion"

    return Konstruktion(
        name=name,
        build=konstr_dict,
    )

def berechne_konstruktion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generischer Rechenpfad:
    - payload['konstruktion'] kommt direkt aus der UI (buildX(...))
    - Untergrund/Gummimatte/etc. stehen in den Bauelementen (Bodenplatten)
    - Header liefert nur Windzone & Aufstelldauer
    """
    # 1) Konstruktion aus dem Build-Dict erzeugen
    konstr_dict = payload["konstruktion"]
    konstruktion = _build_konstruktion_from_payload(konstr_dict)

    # 2) Header-Inputs -> Enums
    if payload.get("aufstelldauer"):
        da = payload["aufstelldauer"]
        aufstelldauer = Dauer(
            wert=int(da["wert"]),
            einheit=Zeitfaktor[da["einheit"]],
        )
    else:
        aufstelldauer = None

    try:
        windzone = WindzoneEnum[payload["windzone"]]
    except Exception as e:
        raise ValueError(f"Unbekannte windzone: {payload['windzone']}") from e

    # 3) Rechnen
    er = standsicherheit(
        konstruktion,
        aufstelldauer=aufstelldauer,
        windzone=windzone,
    )

    # 4) Auf Minimalformat mappen
    return build_api_output(er, payload)
