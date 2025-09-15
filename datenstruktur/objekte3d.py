from dataclasses import dataclass
from typing import Tuple

Vec3 = Tuple[float, float, float]

@dataclass
class Achse:
    punkt: Vec3  # Ein Punkt auf der Achse
    richtung: Vec3  # Einheitsvektor der Achse