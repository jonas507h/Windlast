# rechenfunktionen/windkraft_zu_vektor.py
from __future__ import annotations
from typing import Dict, Callable, Sequence, Optional
import math

from datenstruktur.enums import Norm, ObjektTyp
from datenstruktur.zwischenergebnis import Zwischenergebnis_Vektor
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
) -> Zwischenergebnis_Vektor:

    if objekttyp == ObjektTyp.TRAVERSE:
        # Für Traverse: Richtung der Windkraft = Windrichtung
        ex, ey, ez = windrichtung
        kraft_vec: Vec3 = (windkraft * ex, windkraft * ey, windkraft * ez)

        return Zwischenergebnis_Vektor(
            wert=kraft_vec,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )

    raise NotImplementedError(f"windkraft_zu_vektor für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[[ObjektTyp, Sequence[Vec3], float, Vec3], Zwischenergebnis_Vektor]] = {
    Norm.DEFAULT: _windkraft_zu_vektor_default,
}

def windkraft_zu_vektor(
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,
    norm: Norm = Norm.DEFAULT,
) -> Zwischenergebnis_Vektor:
    _validate_inputs(objekttyp, punkte, windkraft, windrichtung)
    funktion = _DISPATCH.get(norm, _windkraft_zu_vektor_default)
    return funktion(objekttyp, punkte, windkraft, windrichtung)
