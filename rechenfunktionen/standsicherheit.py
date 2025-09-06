from typing import List, Tuple
from standsicherheit_utils import generiere_windrichtungen, kippachsen_aus_eckpunkten
from rechenfunktionen.geom3d import Vec3

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
        for achse in achsen:
            pass  # hier kommt später die eigentliche Bewertung rein

    return 1.0  # TODO: echte Formel

def gleitsicherheit(konstruktion) -> float:
    return 1.0  # TODO

def abhebesicherheit(konstruktion) -> float:
    return 1.0  # TODO
