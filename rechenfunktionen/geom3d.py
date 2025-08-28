# rechenfunktionen/geom3d.py
from math import hypot
from typing import Sequence, Tuple

Punkt3 = Tuple[float, float, float]

__all__ = ["abstand", "Punkt3"]

def abstand_punkte(a: Sequence[float], b: Sequence[float]) -> float:
    """
    Euklidischer Abstand zweier 3D-Punkte.

    Parameter
    ---------
    a, b : Sequenzen mit genau drei Zahlen (x, y, z)
           z.B. Tupel, Listen: (x, y, z)

    Rückgabe
    --------
    float : Abstand in gleichen Einheiten wie die Eingabe

    Raises
    ------
    ValueError : falls a oder b nicht genau 3 Komponenten haben
    """
    if len(a) != 3 or len(b) != 3:
        raise ValueError("abstand erwartet Punkte mit genau 3 Komponenten (x, y, z).")

    ax, ay, az = map(float, a)
    bx, by, bz = map(float, b)
    return hypot(bx - ax, by - ay, bz - az)
