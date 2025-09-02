# rechenfunktionen/grundkraftbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional, Sequence
from enum import Enum
import math

from datenstruktur.enums import Norm, TraversenTyp, ObjektTyp
from datenstruktur.zwischenergebnis import Zwischenergebnis
from materialdaten.catalog import catalog
from rechenfunktionen.geom3d import (
    Vec3,
    vektor_normieren,
    vektor_laenge,
    vektor_zwischen_punkten,
    projektion_vektor_auf_ebene,
    vektor_winkel,
    vektor_invertieren,
    abstand_punkte,
)
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


def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],           # TRAVERSE: [start, ende, orientierung]
    abschnitt: Optional[str],         
    windrichtung: Vec3,               # Einheitsvektor
    voelligkeitsgrad: Optional[float],
    reynoldszahl: Optional[float],
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    n_wind = vektor_laenge(windrichtung)
    if not (0.999 <= n_wind <= 1.001):
        raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n_wind:.6f}.")

    if objekttyp == ObjektTyp.TRAVERSE:
        if not objekt_name_intern:
            raise ValueError("Für TRAVERSE ist objekt_name_intern erforderlich.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 3:
            raise ValueError("Für TRAVERSE werden [start, ende, orientierung] erwartet.")
        startpunkt, endpunkt, orientierung = punkte[0], punkte[1], punkte[2]
        if abstand_punkte(startpunkt, endpunkt) <= 1e-9:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
        n_ori = vektor_laenge(orientierung)
        if not (0.999 <= n_ori <= 1.001):
            raise ValueError(f"orientierung soll Einheitsvektor sein (||v||≈1), ist {n_ori:.6f}.")
        if voelligkeitsgrad is None or reynoldszahl is None:
            raise ValueError("Für TRAVERSE sind voelligkeitsgrad und reynoldszahl erforderlich.")
        if not (0.0 <= voelligkeitsgrad <= 1.0):
            raise ValueError("voelligkeitsgrad muss in [0, 1] liegen.")
        if not (0.0 < reynoldszahl <= 2e5):
            raise ValueError("reynoldszahl muss in (0, 2e5] liegen.")
    else:
        if not isinstance(punkte, (list, tuple)) or len(punkte) == 0:
            raise ValueError("punkte darf nicht leer sein.")

def _grundkraftbeiwert_default(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    abschnitt: Optional[str],
    windrichtung: Vec3,
    voelligkeitsgrad: Optional[float],
    reynoldszahl: Optional[float],
) -> Zwischenergebnis:

    if objekttyp == ObjektTyp.TRAVERSE:
        startpunkt, endpunkt, orientierung = punkte[0], punkte[1], punkte[2]

        traversenachse = vektor_zwischen_punkten(startpunkt, endpunkt)
        traversenachse_norm = vektor_normieren(traversenachse)
        windrichtung_projiziert = vektor_invertieren(
            projektion_vektor_auf_ebene(windrichtung, traversenachse_norm)
        )
        traverse = catalog.get_traverse(objekt_name_intern)
        traversentyp = TraversenTyp.from_points(traverse.anzahl_gurtrohre)

        # Anströmrichtung
        if vektor_laenge(windrichtung_projiziert) < 1e-9:
            anstroemrichtung = Anstroemrichtung.PARALLEL
        else:
            winkel = vektor_winkel(windrichtung_projiziert, orientierung)
            if traversentyp == TraversenTyp.DREI_PUNKT:
                winkel += 90.0

            halbe_Abschnittgroesse = 180.0 / anzahl_flaechen(traversentyp)
            rest = math.fmod(winkel, halbe_Abschnittgroesse)
            if rest < 0:
                rest += halbe_Abschnittgroesse
            if rest < halbe_Abschnittgroesse / 2:
                anstroemrichtung = Anstroemrichtung.FLAECHE
            elif rest < halbe_Abschnittgroesse:
                anstroemrichtung = Anstroemrichtung.ECKE
            else:
                anstroemrichtung = Anstroemrichtung.MITTE

        wert: Optional[float] = None
        if traversentyp == TraversenTyp.ZWEI_PUNKT:
            if anstroemrichtung in (Anstroemrichtung.FLAECHE, Anstroemrichtung.MITTE, Anstroemrichtung.PARALLEL):
                wert = 1.1
            elif anstroemrichtung == Anstroemrichtung.ECKE:
                x = [0.2, 0.35, 0.55]
                y = [0.7, 0.6, 0.5]
                wert = interpol_2D(x, y, voelligkeitsgrad)

        elif traversentyp == TraversenTyp.DREI_PUNKT:
            if anstroemrichtung in (Anstroemrichtung.FLAECHE, Anstroemrichtung.PARALLEL):
                wert = 1.3
            elif anstroemrichtung in (Anstroemrichtung.ECKE, Anstroemrichtung.MITTE):
                wert = 1.45

        elif traversentyp == TraversenTyp.VIER_PUNKT:
            if anstroemrichtung in (Anstroemrichtung.FLAECHE, Anstroemrichtung.PARALLEL):
                x = [0.2, 0.35, 0.55]
                y = [1.85, 1.6, 1.4]
                wert = interpol_2D(x, y, voelligkeitsgrad)
            elif anstroemrichtung == Anstroemrichtung.ECKE:
                x = [0.25, 0.5]
                y = [2.0, 1.9]
                wert = interpol_2D(x, y, voelligkeitsgrad)

        if wert is None:
            raise NotImplementedError(
                f"Keine Zuordnung für TraversenTyp={traversentyp.value} und Anströmung={anstroemrichtung.value}."
            )

        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )

    elif objekttyp == ObjektTyp.ROHR:
        # TODO: Später 'abschnitt' (z.B. Dach/Wand) verwenden, falls relevant
        raise NotImplementedError("Grundkraftbeiwert für ROHR ist noch nicht implementiert.")

    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH: Dict[Norm, Callable[
    [ObjektTyp, Optional[str], Sequence[Vec3], Optional[str], Vec3, Optional[float], Optional[float]],
    Zwischenergebnis
]] = {
    Norm.DEFAULT: _grundkraftbeiwert_default,
}

def grundkraftbeiwert(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],                # TRAVERSE: [start, ende, orientierung]
    abschnitt: Optional[str],
    windrichtung: Vec3,                    # Einheitsvektor
    voelligkeitsgrad: Optional[float] = None,
    reynoldszahl: Optional[float] = None,
    norm: Norm = Norm.DEFAULT,
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, objekt_name_intern, punkte, abschnitt, windrichtung, voelligkeitsgrad, reynoldszahl)
    funktion = _DISPATCH.get(norm, _grundkraftbeiwert_default)
    return funktion(objekttyp, objekt_name_intern, punkte, abschnitt, windrichtung, voelligkeitsgrad, reynoldszahl)
