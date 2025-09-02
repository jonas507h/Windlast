# rechenfunktionen/grundkraftbeiwert_fachwerk.py
from __future__ import annotations
from typing import Tuple, Dict, Callable
from enum import Enum
import math

from datenstruktur.enums import Norm, TraversenTyp
from datenstruktur.zwischenergebnis import Zwischenergebnis
from rechenfunktionen.geom3d import Vec3, vektor_normieren, vektor_laenge, vektor_zwischen_punkten, projektion_vektor_auf_ebene, vektor_winkel, vektor_invertieren
from rechenfunktionen.interpolation import interpol_2D


class Anstroemrichtung(Enum):
    FLAECHE = "flaeche"
    ECKE = "ecke"
    MITTE = "mitte"
    PARALLEL = "parallel"

_TRUSS_TO_FACES = {
    TraversenTyp.ZWEI_PUNKT: 2,
    TraversenTyp.DREI_PUNKT: 3,
    TraversenTyp.VIER_PUNKT: 4,
}

def anzahl_flaechen(typ: TraversenTyp) -> int:
    return _TRUSS_TO_FACES[typ]

# --- Eingabe-Validierung ----------------------------------------------------

def _validate_inputs(
    voelligkeitsgrad: float,
    reynolds: float,
    traversentyp: TraversenTyp,
    windrichtung: Vec3,
    startpunkt: Vec3,
    endpunkt: Vec3,
    orientierung: Vec3,
) -> None:
    if not (0.0 <= voelligkeitsgrad <= 1.0):
        raise ValueError("voelligkeitsgrad muss in [0, 1] liegen.")
    if reynolds <= 0:
        raise ValueError("reynoldszahl muss > 0 sein.")
    if reynolds > 2e5:
        raise ValueError("reynoldszahl muss <= 2e5 sein.")
    if not isinstance(traversentyp, TraversenTyp):
        raise TypeError("traversentyp muss vom Typ TraversenTyp sein.")
    for name, v in (("windrichtung", windrichtung), ("orientierung", orientierung)):
        n = vektor_laenge(v)
        if not (0.999 <= n <= 1.001):
            raise ValueError(f"{name} soll Einheitsvektor sein (||v||≈1), ist {n:.6f}.")
    # Start- und Endpunkt dürfen nicht identisch sein
    if (startpunkt[0] == endpunkt[0]
        and startpunkt[1] == endpunkt[1]
        and startpunkt[2] == endpunkt[2]):
        raise ValueError("startpunkt und endpunkt dürfen nicht identisch sein.")


def _grundkraftbeiwert_fachwerk_default(
    voelligkeitsgrad: float,
    reynolds: float,
    traversentyp: TraversenTyp,
    windrichtung: Vec3,
    startpunkt: Vec3,
    endpunkt: Vec3,
    orientierung: Vec3,
) -> Zwischenergebnis:

    # Winkel zwischen Traverse und Windrichtung
    traversenachse = vektor_zwischen_punkten(startpunkt, endpunkt)
    traversenachse_norm = vektor_normieren(traversenachse)
    windrichtung_projiziert = vektor_invertieren(projektion_vektor_auf_ebene(windrichtung, traversenachse_norm))
    if vektor_laenge(windrichtung_projiziert) < 1e-9:
        anstroemrichtung = Anstroemrichtung.PARALLEL
    else:
        winkel = vektor_winkel(windrichtung_projiziert, orientierung)

        # Bestimmung der Anströmrichtung (Anströmung auf Ecke oder Fläche)
        if traversentyp == traversentyp.DREI_PUNKT:
            winkel += 90.0
        halbe_Bereichsgroesse = 180.0 / anzahl_flaechen(traversentyp)
        rest = math.fmod(winkel, halbe_Bereichsgroesse)
        if rest < 0:
            rest += halbe_Bereichsgroesse
        if rest < halbe_Bereichsgroesse / 2:
            anstroemrichtung = Anstroemrichtung.FLAECHE
        elif rest < halbe_Bereichsgroesse:
            anstroemrichtung = Anstroemrichtung.ECKE
        else:
            anstroemrichtung = Anstroemrichtung.MITTE

    # Berechnung des Grundkraftbeiwerts
    if traversentyp == TraversenTyp.ZWEI_PUNKT:
        if anstroemrichtung == Anstroemrichtung.FLAECHE or anstroemrichtung == Anstroemrichtung.MITTE or anstroemrichtung == Anstroemrichtung.PARALLEL:
            wert = 1.1
        elif anstroemrichtung == Anstroemrichtung.ECKE:
            voelligkeitsgrade = [0.2, 0.35, 0.55]
            grundkraftbeiwerte = [0.7, 0.6, 0.5]
            wert = interpol_2D(voelligkeitsgrade, grundkraftbeiwerte, voelligkeitsgrad)
    elif traversentyp == TraversenTyp.DREI_PUNKT:
        if anstroemrichtung == Anstroemrichtung.FLAECHE or anstroemrichtung == Anstroemrichtung.PARALLEL:
            wert  = 1.3
        elif anstroemrichtung == Anstroemrichtung.ECKE or anstroemrichtung == Anstroemrichtung.MITTE:
            wert = 1.45
    elif traversentyp == TraversenTyp.VIER_PUNKT:
        if anstroemrichtung == Anstroemrichtung.FLAECHE or anstroemrichtung == Anstroemrichtung.PARALLEL:
            voelligkeitsgrade = [0.2, 0.35, 0.55]
            grundkraftbeiwerte = [1.85, 1.6, 1.4]
            wert = interpol_2D(voelligkeitsgrade, grundkraftbeiwerte, voelligkeitsgrad)
        elif anstroemrichtung == Anstroemrichtung.ECKE:
            voelligkeitsgrade = [0.25, 0.5]
            grundkraftbeiwerte = [2, 1.9]
            wert = interpol_2D(voelligkeitsgrade, grundkraftbeiwerte, voelligkeitsgrad)

    return Zwischenergebnis(
        wert=wert,
        formel="---",
        quelle_formel="---",
        formelzeichen=["---"],
        quelle_formelzeichen=["---"],
    )

# --- Zuweisung Norm -> Funktion --------------------------------------------

_DISPATCH: Dict[Norm, Callable[
    [float, float, TraversenTyp, Vec3, Vec3, Vec3, Vec3], Zwischenergebnis
]] = {
    Norm.DEFAULT: _grundkraftbeiwert_fachwerk_default,
}

# --- Öffentliche Funktion ---------------------------------------------------

def grundkraftbeiwert_fachwerk(
    voelligkeitsgrad: float,
    reynolds: float,
    traversentyp: TraversenTyp,
    windrichtung: Vec3,
    startpunkt: Vec3,
    endpunkt: Vec3,
    orientierung: Vec3,
    norm: Norm = Norm.DEFAULT,
) -> Zwischenergebnis:
    _validate_inputs(voelligkeitsgrad, reynolds, traversentyp, windrichtung, startpunkt, endpunkt, orientierung)
    funktion = _DISPATCH.get(norm, _grundkraftbeiwert_fachwerk_default)
    return funktion(voelligkeitsgrad, reynolds, traversentyp, windrichtung, startpunkt, endpunkt, orientierung)
