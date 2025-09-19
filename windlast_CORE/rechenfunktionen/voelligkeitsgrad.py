from typing import Dict, Callable
import math
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm

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
) -> Zwischenergebnis:
    wert = a_projiziert / a_eingeschlossen

    return Zwischenergebnis(
        wert=wert,
        formel="---",
        quelle_formel="---",
        formelzeichen=["---", "---", "---"],
        quelle_formelzeichen=["---"]
    )

_DISPATCH_VG: Dict[Norm, Callable[[float, float], Zwischenergebnis]] = {
    Norm.DEFAULT: _voelligkeitsgrad_default,
}

def voelligkeitsgrad(
    norm: Norm,
    projizierte_flaeche: float,
    eingeschlossene_flaeche: float,
) -> Zwischenergebnis:
    _validate_inputs_voelligkeitsgrad(projizierte_flaeche, eingeschlossene_flaeche)
    funktion = _DISPATCH_VG.get(norm, _voelligkeitsgrad_default)
    return funktion(projizierte_flaeche, eingeschlossene_flaeche)
