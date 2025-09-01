# rechenfunktionen/geom3d.py
from math import hypot
from typing import Sequence, Tuple
import math

Vec3 = Tuple[float, float, float]

__all__ = ["abstand", "Vec3"]

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
        raise ValueError("abstand_punkte erwartet Punkte mit genau 3 Komponenten (x, y, z).")

    ax, ay, az = map(float, a)
    bx, by, bz = map(float, b)
    return hypot(bx - ax, by - ay, bz - az)

def vektor_normieren(v: Sequence[float]) -> Vec3:
    """
    Normiert einen 3D-Vektor.

    Parameter
    ---------
    v : Sequenz mit genau drei Zahlen (x, y, z)
        z.B. Tupel, Listen: (x, y, z)

    Rückgabe
    --------
    Punkt3 : normierter Vektor als Tupel (x, y, z) mit Länge 1

    Raises
    ------
    ValueError : falls v nicht genau 3 Komponenten hat oder der Vektor die Länge 0 hat
    """
    if len(v) != 3:
        raise ValueError("vektor_normieren erwartet Vektor mit genau 3 Komponenten (x, y, z).")

    x, y, z = map(float, v)
    laenge = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if laenge == 0:
        raise ValueError("Kann Vektor der Länge 0 nicht normieren.")

    return (x / laenge, y / laenge, z / laenge)

def vektor_laenge(v: Sequence[float]) -> float:
    """
    Berechnet die Länge eines 3D-Vektors.

    Parameter
    ---------
    v : Sequenz mit genau drei Zahlen (x, y, z)
        z.B. Tupel, Listen: (x, y, z)

    Rückgabe
    --------
    float : Länge des Vektors

    Raises
    ------
    ValueError : falls v nicht genau 3 Komponenten hat
    """
    if len(v) != 3:
        raise ValueError("vektor_laenge erwartet Vektor mit genau 3 Komponenten (x, y, z).")

    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def vektor_skalarprodukt(a: Vec3, b: Vec3) -> float:
    """
    Berechnet das Skalarprodukt zweier 3D-Vektoren.

    Parameter
    ---------
    a, b : Vektoren als Tupel (x, y, z)

    Rückgabe
    --------
    float : Skalarprodukt von a und b

    Raises
    ------
    ValueError : falls a oder b nicht genau 3 Komponenten haben
    """
    if len(a) != 3 or len(b) != 3:
        raise ValueError("vektor_skalarprodukt erwartet Vektoren mit genau 3 Komponenten (x, y, z).")

    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def vektor_winkel(a: Vec3, b: Vec3) -> float:
    """
    Berechnet den Winkel (in Grad) zwischen zwei 3D-Vektoren.

    Parameter
    ---------
    a, b : Vektoren als Tupel (x, y, z)

    Rückgabe
    --------
    float : Winkel in Grad zwischen 0 und 180

    Raises
    ------
    ValueError : falls a oder b nicht genau 3 Komponenten haben oder einer der Vektoren die Länge 0 hat
    """
    if len(a) != 3 or len(b) != 3:
        raise ValueError("vektor_winkel erwartet Vektoren mit genau 3 Komponenten (x, y, z).")

    laenge_a = vektor_laenge(a)
    laenge_b = vektor_laenge(b)
    if laenge_a == 0 or laenge_b == 0:
        raise ValueError("Kann Winkel mit Vektor der Länge 0 nicht berechnen.")

    cos_theta = vektor_skalarprodukt(a, b) / (laenge_a * laenge_b)
    # Numerische Ungenauigkeiten abfangen
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.degrees(math.acos(cos_theta))

def projektion_vektor_auf_ebene(v: Vec3, normal: Vec3) -> Vec3:
    """
    Projektiert einen 3D-Vektor orthogonal auf eine Ebene.

    Parameter
    ---------
    v : Vec3
        Der zu projizierende Vektor.
    normal : Vec3
        Der Normalenvektor der Ebene.

    Rückgabe
    --------
    Vec3 : Der projizierte Vektor.

    Raises
    ------
    ValueError : falls v oder normal nicht genau 3 Komponenten haben oder der Normalenvektor die Länge 0 hat
    """
    if len(v) != 3 or len(normal) != 3:
        raise ValueError("vektor_projektion_auf_ebene erwartet Vektoren mit genau 3 Komponenten (x, y, z).")

    normalisiert = vektor_normieren(normal)
    skalar = vektor_skalarprodukt(v, normalisiert)
    return (
        v[0] - skalar * normalisiert[0],
        v[1] - skalar * normalisiert[1],
        v[2] - skalar * normalisiert[2]
    )

def vektor_zwischen_punkten(start: Vec3, end: Vec3) -> Vec3:
    """
    Berechnet den Vektor zwischen zwei Punkten im 3D-Raum.

    Parameter
    ---------
    start : Vec3
        Der Startpunkt als Vektor (x, y, z).
    end : Vec3
        Der Endpunkt als Vektor (x, y, z).

    Rückgabe
    --------
    Vec3 : Der Vektor von start nach end.

    Raises
    ------
    ValueError : falls start oder end nicht genau 3 Komponenten haben
    """
    if len(start) != 3 or len(end) != 3:
        raise ValueError("vektor_zwischen_punkten erwartet Punkte mit genau 3 Komponenten (x, y, z).")

    return (
        end[0] - start[0],
        end[1] - start[1],
        end[2] - start[2]
    )

def vektor_invertieren(v: Vec3) -> Vec3:
    """
    Invertiert einen 3D-Vektor.

    Parameter
    ---------
    v : Vec3
        Der zu invertierende Vektor.

    Rückgabe
    --------
    Vec3 : Der invertierte Vektor.

    Raises
    ------
    ValueError : falls v nicht genau 3 Komponenten hat
    """
    if len(v) != 3:
        raise ValueError("vektor_invertieren erwartet Vektor mit genau 3 Komponenten (x, y, z).")

    return (-v[0], -v[1], -v[2])
