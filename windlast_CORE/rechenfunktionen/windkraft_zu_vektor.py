# rechenfunktionen/windkraft_zu_vektor.py
from __future__ import annotations
from typing import Dict, Callable, Sequence, Optional
import math

from datenstruktur.enums import Norm, ObjektTyp, Severity
from datenstruktur.zwischenergebnis import (
    Zwischenergebnis_Vektor,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from rechenfunktionen.geom3d import Vec3, vektor_laenge

def _validate_inputs(
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,   # Einheitsvektor
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if not math.isfinite(windkraft) or windkraft < 0:
        raise ValueError("windkraft muss endlich und ≥ 0 sein.")

    n = vektor_laenge(windrichtung)
    if not (0.999 <= n <= 1.001):
        raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n:.6f}.")

    # punkte ist optional. Wenn übergeben, kurz prüfen:
    if punkte is not None and not isinstance(punkte, (list, tuple)):
        raise ValueError("punkte muss eine Sequenz sein, falls gesetzt.")
    
def _windkraft_zu_vektor_default(
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis_Vektor:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "windkraft_zu_vektor",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "windkraft": windkraft,
        "windrichtung": windrichtung,
    })

    if objekttyp == ObjektTyp.TRAVERSE:
        # Für Traverse: Richtung der Windkraft = Windrichtung
        ex, ey, ez = windrichtung
        kraft_vec: Vec3 = (windkraft * ex, windkraft * ey, windkraft * ez)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft-Vektor F⃗_w",
                wert=kraft_vec,
                einzelwerte=[windkraft, ex, ey, ez],
                formel="F⃗ = F · ê",
                formelzeichen=["F⃗", "F", "ê"],
                quelle_formelzeichen=["Projektinterne Bezeichnungen"],
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis_Vektor(wert=kraft_vec)
    raise NotImplementedError(f"windkraft_zu_vektor für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis_Vektor]] = {
    Norm.DEFAULT: _windkraft_zu_vektor_default,
}

def windkraft_zu_vektor(
    norm: Norm,
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis_Vektor:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "windkraft_zu_vektor",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "norm": getattr(norm, "name", str(norm)),
        "windkraft": windkraft,
        "windrichtung": windrichtung,
    })

    try:
        _validate_inputs(objekttyp, punkte, windkraft, windrichtung)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDVEK/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        bad = (float("nan"), float("nan"), float("nan"))
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Windkraft-Vektor F⃗_w", wert=bad),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis_Vektor(wert=bad)
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, punkte, windkraft, windrichtung,
        protokoll=protokoll, kontext=base_ctx,
    )
