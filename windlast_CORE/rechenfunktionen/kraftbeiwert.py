# rechenfunktionen/kraftbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional
import math

from datenstruktur.enums import Norm, ObjektTyp, Severity
from datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)

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
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "kraftbeiwert",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
    })

    if objekttyp == ObjektTyp.TRAVERSE:
        wert = grundkraftbeiwert * abminderungsfaktor_schlankheit
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kraftbeiwert c",
                wert=wert,
                einzelwerte=[grundkraftbeiwert, abminderungsfaktor_schlankheit],
                formel="c = c₀ · η_schlank",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)

    # Andere Objekttypen:
    raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _kraftbeiwert_default,
}

def kraftbeiwert(
    norm: Norm,
    objekttyp: ObjektTyp,
    grundkraftbeiwert: float,
    abminderungsfaktor_schlankheit: Optional[float] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "kraftbeiwert",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs(objekttyp, grundkraftbeiwert, abminderungsfaktor_schlankheit)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="KRAFT/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Kraftbeiwert c", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, grundkraftbeiwert, abminderungsfaktor_schlankheit,
        protokoll=protokoll, kontext=base_ctx,
    )
