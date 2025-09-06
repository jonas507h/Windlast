from dataclasses import dataclass
from rechenfunktionen.geom3d import Vec3

@dataclass
class Achse:
    punkt: Vec3  # Ein Punkt auf der Achse
    richtung: Vec3  # Einheitsvektor der Achse