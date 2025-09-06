import math
from typing import List, Tuple, Optional, Sequence
from rechenfunktionen.geom3d import Vec3, vektor_zwischen_punkten, vektor_normieren, einheitsvektor_aus_winkeln, konvexe_huelle_xy
from datenstruktur.objekte3d import Achse

_EPS = 1e-9

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

def kippachsen_aus_eckpunkten(punkte: List[Vec3], *, include_Randpunkte: bool = False) -> List[Achse]:
    if len(punkte) < 3:
        raise ValueError("Mindestens 3 Punkte sind erforderlich, um Kippachsen zu bestimmen.")
    
    huelle = konvexe_huelle_xy(punkte)

    if len(huelle) < 2:
        raise ValueError("Die konvexe Hülle muss mindestens 2 Punkte enthalten.")
    
    kippachsen: List[Achse] = []
    for i in range(len(huelle)):
        p1 = huelle[i]
        p2 = huelle[(i + 1) % len(huelle)]

        richtung = vektor_zwischen_punkten(p1, p2)
        richtung_norm = vektor_normieren(richtung)
        if richtung_norm == (0.0, 0.0, 0.0):
            continue
        kippachsen.append(Achse(punkt=p1, richtung=richtung))
    
    return kippachsen
