from typing import Dict, Callable
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, TraversenTyp
from materialdaten.catalog import catalog
from rechenfunktionen.geom3d import Vec3, vektor_laenge, abstand_punkte

def _validate_inputs(
    traversentyp: TraversenTyp,
    windrichtung: Vec3,
    startpunkt: Vec3,
    endpunkt: Vec3,
    orientierung: Vec3,
    traverse_name_intern: str) -> None:
    if not isinstance(traversentyp, TraversenTyp):
        raise TypeError("traversentyp muss vom Typ TraversenTyp sein.")
    for name, v in (("windrichtung", windrichtung), ("orientierung", orientierung)):
        n = vektor_laenge(v)
        if not (0.999 <= n <= 1.001):
            raise ValueError(f"{name} soll Einheitsvektor sein (||v||≈1), ist {n:.6f}.")
    if (startpunkt[0] == endpunkt[0]
        and startpunkt[1] == endpunkt[1]
        and startpunkt[2] == endpunkt[2]):
        raise ValueError("startpunkt und endpunkt dürfen nicht identisch sein.")

def _tatsaechliche_flaeche_traverse_default(
    traversentyp: TraversenTyp,
    windrichtung: Vec3,
    startpunkt: Vec3,
    endpunkt: Vec3,
    orientierung: Vec3,
    traverse_name_intern: str
) -> Zwischenergebnis:

    # simple Berechnung nach Ebner
    laenge = abstand_punkte(startpunkt, endpunkt)
    traverse = catalog.get_traverse(traverse_name_intern)
    d_Gurt = traverse.d_gurt
    d_Diagonale = traverse.d_diagonalen

    wert = (2 * laenge * d_Gurt) + (3.2 * laenge * d_Diagonale)

    return Zwischenergebnis(
        wert=wert,
        formel="---",
        quelle_formel="---",
        formelzeichen=["---", "---", "---"],
        quelle_formelzeichen=["---"]
    )

#zuweisung Norm -> Funktion
_DISPATCH: Dict[Norm, Callable[
    [TraversenTyp, Vec3, Vec3, Vec3, Vec3, str], Zwischenergebnis
]] = {
    Norm.DEFAULT: _tatsaechliche_flaeche_traverse_default,
}

def tatsaechliche_flaeche_traverse(
    traversentyp: TraversenTyp,
    windrichtung: Vec3,
    startpunkt: Vec3,
    endpunkt: Vec3,
    orientierung: Vec3,
    traverse_name_intern: str,
    norm: Norm = Norm.DEFAULT
) -> Zwischenergebnis:
    _validate_inputs(traversentyp, windrichtung, startpunkt, endpunkt, orientierung, traverse_name_intern)
    funktion = _DISPATCH.get(norm, _tatsaechliche_flaeche_traverse_default)
    return funktion(traversentyp, windrichtung, startpunkt, endpunkt, orientierung, traverse_name_intern)