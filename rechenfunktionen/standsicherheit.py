from standsicherheit_utils import generiere_windrichtungen, kippachsen_aus_eckpunkten
from rechenfunktionen.geom3d import Vec3

def kippsicherheit(konstruktion) -> float:
    # TODO: hier Eckpunkte der Bodenplatten sammeln
    # eckpunkte = sammle_eckpunkte(konstruktion)
    eckpunkte = ...  # <- du füllst das gleich

    achsen = kippachsen_aus_eckpunkten(eckpunkte, include_Randpunkte=False)

    for winkel, richtung in generiere_windrichtungen(anzahl=4):
        for achse in achsen:
            pass  # hier kommt später die eigentliche Bewertung rein

    return 1.0  # TODO: echte Formel

def gleitsicherheit(konstruktion) -> float:
    return 1.0  # TODO

def abhebesicherheit(konstruktion) -> float:
    return 1.0  # TODO
