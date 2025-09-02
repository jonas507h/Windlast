# rechenfunktionen/windkraft.py
from __future__ import annotations
from typing import Dict, Callable
import math

from datenstruktur.enums import Norm, ObjektTyp
from datenstruktur.zwischenergebnis import Zwischenergebnis

def _validate_inputs(
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,              # N/m²
    projizierte_flaeche: float,    # m²
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    for name, val, cond in (
        ("kraftbeiwert", kraftbeiwert, kraftbeiwert > 0),
        ("staudruck", staudruck, staudruck >= 0),
        ("projizierte_flaeche", projizierte_flaeche, projizierte_flaeche >= 0),
    ):
        if not math.isfinite(val):
            raise ValueError(f"{name} muss endlich sein (kein NaN/Inf).")
        if not cond:
            raise ValueError(f"{name} hat unzulässigen Wert ({val}).")

def _windkraft_default(
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,
    projizierte_flaeche: float,
) -> Zwischenergebnis:
    if objekttyp == ObjektTyp.TRAVERSE:
        wert = kraftbeiwert * staudruck * projizierte_flaeche

        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )
    
    # Andere Objekttypen:
    raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[[ObjektTyp, float, float, float], Zwischenergebnis]] = {
    Norm.DEFAULT: _windkraft_default,
}

def windkraft(
    norm: Norm,
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,
    projizierte_flaeche: float,
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, kraftbeiwert, staudruck, projizierte_flaeche)
    funktion = _DISPATCH.get(norm, _windkraft_default)
    return funktion(objekttyp, kraftbeiwert, staudruck, projizierte_flaeche)
