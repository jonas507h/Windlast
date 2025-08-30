from typing import Dict, Callable
from datenstruktur.zwischenergebnis import Norm,Zwischenergebnis

def _validate_inputs(laenge: float, hoehe: float) -> None:
    if laenge <= 0 or hoehe <= 0:
        raise ValueError("laenge und hoehe müssen > 0 sein.")

def _schlankheit_default(laenge: float, hoehe: float) -> Zwischenergebnis:
    # Faktor bestimmen
    if laenge >= 50:
        faktor = 1.4
    elif laenge < 15:
        faktor = 2.0
    else:
        # lineare Interpolation zwischen (15,2.0) und (50,1.4)
        faktor = 2.0 + (laenge - 15) * (1.4 - 2.0) / (50 - 15)

    rechenwert = faktor * (laenge / hoehe)

    wert = min(rechenwert, 70.0)

    return Zwischenergebnis(
        wert=wert,
        formel="---",
        quelle="---",
        formelzeichen=["---", "---", "---"],
        quelle_formelzeichen=["---"]
    )

#zuweisung Norm -> Funktion
_DISPATCH: Dict[Norm, Callable[[float, float], Zwischenergebnis]] = {
    Norm.DEFAULT: _schlankheit_default,
}

def schlankheit(laenge: float, hoehe: float, norm: Norm = Norm.DEFAULT) -> Zwischenergebnis:
    _validate_inputs(laenge, hoehe)
    funktion = _DISPATCH.get(norm, _schlankheit_default)
    return funktion(laenge, hoehe)