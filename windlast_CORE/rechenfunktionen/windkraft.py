# rechenfunktionen/windkraft.py
from __future__ import annotations
from typing import Dict, Callable, Optional
import math

from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)

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
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    if objekttyp == ObjektTyp.TRAVERSE:
        wert = kraftbeiwert * staudruck * projizierte_flaeche

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft F_w",
                wert=wert,
                einzelwerte=[kraftbeiwert, staudruck, projizierte_flaeche],
                formel="F = c · q · A",
                formelzeichen=["F", "c", "q", "A"],
                quelle_formelzeichen=["Projektinterne Bezeichnungen"],
            ),
            kontext=merge_kontext(kontext, {
                "funktion": "windkraft",
                "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
            }),
        )
        return Zwischenergebnis(wert=wert)
    
    # Andere Objekttypen:
    raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _windkraft_default,
}

def windkraft(
    norm: Norm,
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,
    projizierte_flaeche: float,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "windkraft",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs(objekttyp, kraftbeiwert, staudruck, projizierte_flaeche)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDKRAFT/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Windkraft F_w", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, kraftbeiwert, staudruck, projizierte_flaeche,
        protokoll=protokoll, kontext=base_ctx,
    )
