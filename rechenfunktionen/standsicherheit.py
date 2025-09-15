from typing import List, Tuple
from standsicherheit_utils import generiere_windrichtungen, kippachsen_aus_eckpunkten
from rechenfunktionen.geom3d import Vec3
from datenstruktur.kraefte import Kraefte
from datenstruktur.enums import Norm

def kippsicherheit(konstruktion) -> float:
    eckpunkte: List[Vec3] = []

    for obj in getattr(konstruktion, "bauelemente", []):
        ep = getattr(obj, "eckpunkte", None)
        if callable(ep):
            punkte = ep()
            if punkte:
                eckpunkte.extend(punkte)

    achsen = kippachsen_aus_eckpunkten(eckpunkte, include_Randpunkte=False)

    for winkel, richtung in generiere_windrichtungen(anzahl=4):
        kraefte_windrichtung: List[Kraefte] = []

        for elem in (getattr(konstruktion, "bauelemente", None) or []):
            # Gewicht
            fn_gewicht = getattr(elem, "gewichtskraefte", None)
            if callable(fn_gewicht):
                kraefte_gewicht = fn_gewicht()  # -> List[Kraefte]
                if kraefte_gewicht:
                    kraefte_windrichtung.extend(kraefte_gewicht)

            # Wind
            fn_wind = getattr(elem, "windkraefte", None)
            if callable(fn_wind):
                kraefte_wind = fn_wind(
                    norm=Norm.DEFAULT,
                    windrichtung=richtung,
                    staudruecke=[350.0],          # Platzhalter
                    obergrenzen=[float("inf")],   # Platzhalter
                    konst=None,
                )  # -> List[Kraefte]
                if kraefte_wind:
                    kraefte_windrichtung.extend(kraefte_wind)

        for achse in achsen:
            pass  # hier kommt später die eigentliche Bewertung rein

    return 1.0  # TODO: echte Formel

def gleitsicherheit(konstruktion) -> float:
    return 1.0  # TODO

def abhebesicherheit(konstruktion) -> float:
    return 1.0  # TODO
