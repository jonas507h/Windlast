import math
from typing import List, Tuple, Optional, Sequence
from rechenfunktionen.geom3d import Vec3, einheitsvektor_aus_winkeln

def generiere_windrichtungen(
    anzahl: int = 4,
    *,
    startwinkel: float = 0.0,
    winkel: Optional[Sequence[float]] = None
    ) -> List[Tuple[float, Vec3]]:
    
    if winkel is not None:
        return [(w, einheitsvektor_aus_winkeln(w, 0.0)) for w in winkel]
    if anzahl < 1:
        raise ValueError("Anzahl der Windrichtungen muss mindestens 1 sein.")
    winkelabstand = 360.0 / anzahl
    return [(i * winkelabstand + startwinkel, einheitsvektor_aus_winkeln(i * winkelabstand + startwinkel, 0.0)) for i in range(anzahl)]
