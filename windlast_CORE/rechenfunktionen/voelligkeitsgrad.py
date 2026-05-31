from typing import Dict, Callable, Optional
import math
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.datenstruktur.enums import Norm, Severity
from windlast_CORE.datenstruktur.konstanten import _EPS

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
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "voelligkeitsgrad_default",
    }

    wert = a_projiziert / a_eingeschlossen

    if not (0.0 - _EPS <= wert <= 1.0 + _EPS):
        protokolliere_msg(
            protokoll,
            severity=Severity.WARN,
            code="VOELLIG/OUT_OF_RANGE",
            text=f"Völligkeitsgrad φ={wert:.4f} liegt außerhalb [0,1].",
            breadcrumb=base_bc,
            meta=base_meta,
        )

    protokolliere_ergebnis(
        protokoll,
        breadcrumb=base_bc,
        name="voelligkeitsgrad",
        wert=wert,
        label="math.voelligkeitsgrad.label",
        formelzeichen="math.voelligkeitsgrad.symbol",
        formel="math.voelligkeitsgrad.formula",
        meta=base_meta,
    )
    return Zwischenergebnis(wert=wert)

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _voelligkeitsgrad_default,
}

def voelligkeitsgrad(
    norm: Norm,
    projizierte_flaeche: float,
    eingeschlossene_flaeche: float,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "voelligkeitsgrad",
    }

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
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="voelligkeitsgrad",
            wert=float("nan"),
            label="math.voelligkeitsgrad.label",
            formelzeichen="math.voelligkeitsgrad.symbol",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        projizierte_flaeche, eingeschlossene_flaeche,
        protokoll=protokoll, breadcrumb=base_bc,
    )
