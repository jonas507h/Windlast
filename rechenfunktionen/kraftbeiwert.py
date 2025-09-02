# rechenfunktionen/kraftbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional
import math

from datenstruktur.enums import Norm, ObjektTyp
from datenstruktur.zwischenergebnis import Zwischenergebnis

def _validate_inputs(
    objekttyp: ObjektTyp,
    grundkraftbeiwert: float,
    abminderungsfaktor_schlankheit: Optional[float],
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if not math.isfinite(grundkraftbeiwert) or grundkraftbeiwert <= 0:
        raise ValueError("grundkraftbeiwert muss endlich und > 0 sein.")
    if objekttyp == ObjektTyp.TRAVERSE:
        # Pflicht und positiv (0 < η < ∞), außerdem endlich
        if abminderungsfaktor_schlankheit is None:
            raise ValueError("Für TRAVERSE ist abminderungsfaktor_schlankheit erforderlich.")
        if not math.isfinite(abminderungsfaktor_schlankheit) or abminderungsfaktor_schlankheit <= 0:
            raise ValueError("abminderungsfaktor_schlankheit muss > 0 und endlich sein.")

def _kraftbeiwert_default(
    objekttyp: ObjektTyp,
    grundkraftbeiwert: float,
    abminderungsfaktor_schlankheit: Optional[float],
) -> Zwischenergebnis:
    if objekttyp == ObjektTyp.TRAVERSE:
        wert = grundkraftbeiwert * abminderungsfaktor_schlankheit
        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
    )

    # Andere Objekttypen:
    raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[[ObjektTyp, float, Optional[float]], Zwischenergebnis]] = {
    Norm.DEFAULT: _kraftbeiwert_default,
}

def kraftbeiwert(
    norm: Norm,
    objekttyp: ObjektTyp,
    grundkraftbeiwert: float,
    abminderungsfaktor_schlankheit: Optional[float] = None,
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, grundkraftbeiwert, abminderungsfaktor_schlankheit)
    funktion = _DISPATCH.get(norm, _kraftbeiwert_default)
    return funktion(objekttyp, grundkraftbeiwert, abminderungsfaktor_schlankheit)
