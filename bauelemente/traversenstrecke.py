from dataclasses import dataclass
from typing import Tuple
from materialdaten.catalog import catalog
from rechenfunktionen import abstand_punkte

Point3 = Tuple[float, float, float]

@dataclass
class Traversenstrecke:
    traverse_name_intern: str
    start: Point3
    ende:  Point3

    def laenge(self) -> float:
        return abstand_punkte(self.start, self.ende)

    def gewicht(self) -> float:
        spec = catalog.get_traverse(self.traverse_name_intern)
        return self.laenge() * float(spec.gewicht_linear_kg_m)
