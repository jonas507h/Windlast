from typing import Dict, Callable, Optional
import math
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.datenstruktur.enums import Norm, Severity

_EPS = 1e-12  # numerische Toleranz gegen Division durch ~0

def _validate_inputs_voelligkeitsgrad(
    a_projiziert: float,
    a_eingeschlossen: float,
) -> None:
    # Finitheit prüfen (kein NaN/Inf)
    for name, val in (("projizierte_flaeche", a_projiziert), ("eingeschlossene_flaeche", a_eingeschlossen)):
        if not math.isfinite(val):
            raise ValueError(f"{name} muss endlich sein (kein NaN/Inf).")
    # Physikalische Plausibilität
    if a_projiziert < 0:
        raise ValueError("projizierte_flaeche muss ≥ 0 sein.")
    if a_eingeschlossen <= 0:
        raise ValueError("eingeschlossene_flaeche muss > 0 sein.")
    if a_eingeschlossen <= _EPS:
        raise ValueError("eingeschlossene_flaeche ist zu klein (numerisch ~0).")

def _voelligkeitsgrad_default(
    a_projiziert: float,
    a_eingeschlossen: float,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "voelligkeitsgrad",
    })

    wert = a_projiziert / a_eingeschlossen

    if not (0.0 - _EPS <= wert <= 1.0 + _EPS):
        protokolliere_msg(
            protokoll,
            severity=Severity.WARN,
            code="VOELLIG/OUT_OF_RANGE",
            text=f"Völligkeitsgrad φ={wert:.4f} liegt außerhalb [0,1].",
            kontext=merge_kontext(base_ctx, {"phi": wert}),
        )

    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(
            titel="Völligkeitsgrad φ",
            wert=wert,
            formel="φ = A_proj / A_e",
            formelzeichen=["φ", "A_proj", "A_e"],
            einzelwerte=[a_projiziert, a_eingeschlossen],
        ),
        kontext=base_ctx,
    )
    return Zwischenergebnis(wert=wert)

_DISPATCH_VG: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _voelligkeitsgrad_default,
}

def voelligkeitsgrad(
    norm: Norm,
    projizierte_flaeche: float,
    eingeschlossene_flaeche: float,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "voelligkeitsgrad",
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs_voelligkeitsgrad(projizierte_flaeche, eingeschlossene_flaeche)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="VOELLIG/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Völligkeitsgrad φ", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH_VG.get(norm, _DISPATCH_VG[Norm.DEFAULT])
    return funktion(
        projizierte_flaeche, eingeschlossene_flaeche,
        protokoll=protokoll, kontext=base_ctx,
    )
