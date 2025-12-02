# rechenfunktionen/geom3d.py
from math import hypot
from typing import Sequence, Tuple, Optional, List
import math
from windlast_CORE.datenstruktur.objekte3d import Achse

Vec3 = Tuple[float, float, float]
_EPS = 1e-9

__all__ = ["abstand", "Vec3", "flaechenschwerpunkt", "vektor_parallelanteil", "vektor_senkrechtanteil"]

def abstand_punkte(a: Vec3, b: Vec3) -> float:
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

def vektor_normieren(v: Vec3) -> Vec3:
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

def vektor_laenge(v: Vec3) -> float:
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

def schnittpunkt_strecke_ebene(strecke_start: Vec3, strecke_ende: Vec3, ebenenpunkt: Vec3, ebenennormal: Vec3) -> Optional[Vec3]:
    """
    Berechnet den Schnittpunkt einer Strecke mit einer Ebene im 3D-Raum.

    Parameter
    ---------
    strecke_start : Vec3
        Der Startpunkt der Strecke.
    strecke_ende : Vec3
        Der Endpunkt der Strecke.
    ebenenpunkt : Vec3
        Ein Punkt auf der Ebene.
    ebenennormal : Vec3
        Der Normalenvektor der Ebene.

    Rückgabe
    --------
    Optional[Vec3] : Der Schnittpunkt als Vektor (x, y, z) oder None, wenn kein Schnittpunkt existiert.

    Raises
    ------
    ValueError : falls einer der Eingabevektoren nicht genau 3 Komponenten hat oder der Normalenvektor die Länge 0 hat
    """
    if len(strecke_start) != 3 or len(strecke_ende) != 3 or len(ebenenpunkt) != 3 or len(ebenennormal) != 3:
        raise ValueError("schnittpunkt_strecke_ebene erwartet Vektoren mit genau 3 Komponenten (x, y, z).")

    d = vektor_skalarprodukt(ebenennormal, vektor_zwischen_punkten(strecke_start, strecke_ende))
    if abs(d) < 1e-9:
        return None  # Strecke ist parallel zur Ebene

    t = vektor_skalarprodukt(ebenennormal, vektor_zwischen_punkten(strecke_start, ebenenpunkt)) / d
    if t < 0.0 or t > 1.0:
        return None  # Schnittpunkt liegt außerhalb der Strecke

    return (
        strecke_start[0] + t * (strecke_ende[0] - strecke_start[0]),
        strecke_start[1] + t * (strecke_ende[1] - strecke_start[1]),
        strecke_start[2] + t * (strecke_ende[2] - strecke_start[2])
    )

def vektoren_addieren (vektoren: Sequence[Vec3]) -> Vec3:
    """
    Addiert eine Liste von 3D-Vektoren.

    Parameter
    ---------
    vektoren : Sequenz von Vec3
        Die zu addierenden Vektoren.

    Rückgabe
    --------
    Vec3 : Der resultierende Vektor.

    Raises
    ------
    ValueError : falls einer der Vektoren nicht genau 3 Komponenten hat
    """
    sum_x = sum_y = sum_z = 0.0
    for v in vektoren:
        if len(v) != 3:
            raise ValueError("vektoren_addieren erwartet Vektoren mit genau 3 Komponenten (x, y, z).")
        sum_x += v[0]
        sum_y += v[1]
        sum_z += v[2]
    return (sum_x, sum_y, sum_z)

def mittelpunkt (punkte: Sequence[Vec3]) -> Vec3:
    """
    Berechnet den Mittelpunkt einer Liste von 3D-Punkten.

    Parameter
    ---------
    punkte : Sequenz von Vec3
        Die Punkte, deren Mittelpunkt berechnet werden soll.

    Rückgabe
    --------
    Vec3 : Der Mittelpunkt als Vektor (x, y, z).

    Raises
    ------
    ValueError : falls die Liste leer ist oder einer der Punkte nicht genau 3 Komponenten hat
    """
    if not punkte:
        raise ValueError("mittelpunkt erwartet mindestens einen Punkt.")

    sum_x = sum_y = sum_z = 0.0
    for p in punkte:
        if len(p) != 3:
            raise ValueError("mittelpunkt erwartet Punkte mit genau 3 Komponenten (x, y, z).")
        sum_x += p[0]
        sum_y += p[1]
        sum_z += p[2]

    n = len(punkte)
    return (sum_x / n, sum_y / n, sum_z / n)

def vektor_kreuzprodukt(a: Vec3, b: Vec3) -> Vec3:
    """
    Berechnet das Kreuzprodukt zweier 3D-Vektoren.

    Parameter
    ---------
    a, b : Vektoren als Tupel (x, y, z)

    Rückgabe
    --------
    Vec3 : Das Kreuzprodukt von a und b.

    Raises
    ------
    ValueError : falls a oder b nicht genau 3 Komponenten haben
    """
    if len(a) != 3 or len(b) != 3:
        raise ValueError("vektor_kreuzprodukt erwartet Vektoren mit genau 3 Komponenten (x, y, z).")

    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )

def flaechenschwerpunkt(punkte: Sequence[Vec3]) -> Vec3:
    """
    Flächenschwerpunkt eines ebenen (nicht selbstschneidenden) 3D-Polygons.
    Punkte müssen auf einer Ebene liegen und in Reihenfolge des Randes angegeben sein.

    Sonderfälle:
    - 1 Punkt  -> dieser Punkt
    - 2 Punkte -> Mittelpunkt der Strecke
    - >=3 Punkte -> Schwerpunkt der Polygonfläche (Vorzeichen robust bzgl. Orientierung)

    Raises
    ------
    ValueError : bei leerer Liste, kollinearen Punkten oder Fläche ~ 0
    """
    if punkte is None:
        raise ValueError("punkte darf nicht None sein.")

    n = len(punkte)
    if n == 0:
        raise ValueError("flaechenschwerpunkt erwartet mindestens einen Punkt.")
    if n == 1:
        p = punkte[0]
        if len(p) != 3:
            raise ValueError("Punkte müssen 3D sein (x, y, z).")
        # 1 Punkt -> zurückgeben
        return p
    if n == 2:
        # 2 Punkte -> Mittelpunkt
        a, b = punkte[0], punkte[1]
        if len(a) != 3 or len(b) != 3:
            raise ValueError("Punkte müssen 3D sein (x, y, z).")
        return mittelpunkt([a, b])

    # --- Newell-Normale berechnen (robust, auch für konkave Polygone) ---
    Nx = Ny = Nz = 0.0
    for i in range(n):
        j = (i + 1) % n
        xi, yi, zi = map(float, punkte[i])
        xj, yj, zj = map(float, punkte[j])
        # einfachste Newell-Variante: Summe der Kreuzprodukte Pi x Pj
        cx, cy, cz = vektor_kreuzprodukt((xi, yi, zi), (xj, yj, zj))
        Nx += cx; Ny += cy; Nz += cz

    N = (Nx, Ny, Nz)
    # Normale normieren (wirft bei Länge 0 eine Exception)
    try:
        n_hat = vektor_normieren(N)
    except ValueError:
        # Kollinear / degeneriert
        raise ValueError("Degeneriertes Polygon: Normale hat Länge 0 (Punkte evtl. kollinear).")

    # --- Triangulation um P0 ---
    P0 = tuple(map(float, punkte[0]))
    A_sum = 0.0
    Cx = Cy = Cz = 0.0

    for i in range(1, n - 1):
        Pi = tuple(map(float, punkte[i]))
        Pj = tuple(map(float, punkte[i+1]))

        # v1 = Pi - P0, v2 = Pj - P0
        v1 = vektor_zwischen_punkten(P0, Pi)
        v2 = vektor_zwischen_punkten(P0, Pj)

        # vorzeichenbehaftete Teilfläche: 0.5 * ( (v1 x v2) · n_hat )
        cx, cy, cz = vektor_kreuzprodukt(v1, v2)
        area_i = 0.5 * vektor_skalarprodukt((cx, cy, cz), n_hat)

        if area_i != 0.0:
            # Schwerpunkt des Dreiecks (P0, Pi, Pj)
            ci_x = (P0[0] + Pi[0] + Pj[0]) / 3.0
            ci_y = (P0[1] + Pi[1] + Pj[1]) / 3.0
            ci_z = (P0[2] + Pi[2] + Pj[2]) / 3.0

            A_sum += area_i
            Cx += area_i * ci_x
            Cy += area_i * ci_y
            Cz += area_i * ci_z

    if A_sum == 0.0 or not math.isfinite(A_sum):
        # Fläche verschwindet numerisch -> kein Flächenschwerpunkt definiert
        raise ValueError("Polygonfläche ist 0 oder numerisch instabil – überprüfe die Punkte (Planarität/Reihenfolge).")

    return (Cx / A_sum, Cy / A_sum, Cz / A_sum)

def vektor_multiplizieren(v: Vec3, skalar: float) -> Vec3:
    """
    Multipliziert einen 3D-Vektor mit einem Skalar.

    Parameter
    ---------
    v : Vec3
        Der zu skalierende Vektor.
    skalar : float
        Der Skalierungsfaktor.

    Rückgabe
    --------
    Vec3 : Der skalierte Vektor.

    Raises
    ------
    ValueError : falls v nicht genau 3 Komponenten hat
    """
    if len(v) != 3:
        raise ValueError("vektor_multiplizieren erwartet Vektor mit genau 3 Komponenten (x, y, z).")

    return (v[0] * skalar, v[1] * skalar, v[2] * skalar)

def vektor_parallelanteil(v: Vec3, richtung: Vec3) -> Vec3:
    """
    Berechnet den Parallelanteil eines Vektors v auf einen Richtungsvektor.

    Parameter
    ---------
    v : Vec3
        Der zu projizierende Vektor.
    richtung : Vec3
        Der Richtungsvektor (muss normiert sein).

    Rückgabe
    --------
    Vec3 : Der Parallelanteil von v auf richtung.
    """
    if not richtung:
        raise ValueError("Der Richtungsvektor darf nicht der Nullvektor sein.")

    skalar = vektor_skalarprodukt(v, richtung)
    return vektor_multiplizieren(richtung, skalar)

def vektor_senkrechtanteil(v: Vec3, richtung: Vec3) -> Vec3:
    """
    Berechnet den Senkrechtanteil eines Vektors v zu einem Richtungsvektor.

    Parameter
    ---------
    v : Vec3
        Der zu projizierende Vektor.
    richtung : Vec3
        Der Richtungsvektor (muss normiert sein).

    Rückgabe
    --------
    Vec3 : Der Senkrechtanteil von v zu richtung.
    """
    parallel = vektor_parallelanteil(v, richtung)
    return vektor_zwischen_punkten(parallel, v)

def senkrechter_vektor(a: Vec3, b: Vec3) -> Vec3:
    """
    Berechnet einen Vektor, der senkrecht auf den beiden gegebenen Vektoren a und b steht.

    Parameter
    ---------
    a, b : Vec3
        Die beiden Vektoren.

    Rückgabe
    --------
    Vec3 : Ein Vektor, der senkrecht auf a und b steht.

    Raises
    ------
    ValueError : falls a oder b nicht genau 3 Komponenten haben oder die Vektoren kollinear sind
    """
    if len(a) != 3 or len(b) != 3:
        raise ValueError("senkrechter_vektor erwartet Vektoren mit genau 3 Komponenten (x, y, z).")

    kreuz = vektor_kreuzprodukt(a, b)
    if vektor_laenge(kreuz) == 0:
        raise ValueError("Die Vektoren a und b sind kollinear; kein eindeutiger senkrechter Vektor existiert.")

    return vektor_normieren(kreuz)

def einheitsvektor_aus_winkeln(azimut: float, elevation: float) -> Vec3:
    """
    Erstellt einen Einheitsvektor aus Azimut- und Elevationswinkel (in Grad).

    Parameter
    ---------
    azimut : float
        Der Azimutwinkel in Grad (0° = x-Achse, 90° = y-Achse).
    elevation : float
        Der Elevationswinkel in Grad (0° = xy-Ebene, 90° = z-Achse).

    Rückgabe
    --------
    Vec3 : Der resultierende Einheitsvektor (x, y, z).
    """
    az_rad = math.radians(azimut)
    el_rad = math.radians(elevation)

    x = math.cos(el_rad) * math.cos(az_rad)
    y = math.cos(el_rad) * math.sin(az_rad)
    z = math.sin(el_rad)

    return (x, y, z)

def konvexe_huelle_xy(punkte: List[Vec3], *, include_Randpunkte: bool = False) -> List[Vec3]:
    """
    Berechnet die konvexe Hülle einer Menge von 3D-Punkten, projiziert auf die XY-Ebene.
    Die Z-Koordinate der Rückgabepunkte entspricht derjenigen des ursprünglichen Punktes.

    Parameter
    ---------
    punkte : Liste von Vec3
        Die Eingabepunkte.
    include_Randpunkte : bool, optional
        Ob Punkte auf dem Rand der konvexen Hülle eingeschlossen werden sollen (Standard: False).

    Rückgabe
    --------
    Liste von Vec3 : Die Punkte der konvexen Hülle in Reihenfolge (CCW, ohne Startpunkt-Duplikat).

    Raises
    ------
    ValueError : falls weniger als 3 Punkte gegeben sind oder alle Punkte kollinear sind
    """
    if len(punkte) < 3:
        raise ValueError("Mindestens 3 Punkte sind erforderlich, um eine konvexe Hülle zu berechnen.")

    # Sortiere Punkte lexikographisch nach (x, y)
    unique_xy = {}
    for x, y, z in punkte:
        unique_xy.setdefault((x, y), (x, y, z))
    punkte = sorted(unique_xy.values(), key=lambda p: (p[0], p[1]))

    def kreuzprodukt_2D(o: Vec3, a: Vec3, b: Vec3) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    untere_huelle: List[Vec3] = []
    for p in punkte:
        while len(untere_huelle) >= 2:
            turn = kreuzprodukt_2D(untere_huelle[-2], untere_huelle[-1], p)
            if include_Randpunkte:
                if turn < -_EPS:
                    untere_huelle.pop()
                else:
                    break
            else:
                if turn <= _EPS:
                    untere_huelle.pop()
                else:
                    break
        untere_huelle.append(p)

    obere_huelle: List[Vec3] = []
    for p in reversed(punkte):
        while len(obere_huelle) >= 2:
            turn = kreuzprodukt_2D(obere_huelle[-2], obere_huelle[-1], p)
            if include_Randpunkte:
                if turn < -_EPS:
                    obere_huelle.pop()
                else:
                    break
            else:
                if turn <= _EPS:
                    obere_huelle.pop()
                else:
                    break
        obere_huelle.append(p)

    # Entferne das letzte Element jeder Hälfte, da es das erste Element der anderen Hälfte ist
    del untere_huelle[-1]
    del obere_huelle[-1]

    konvexe_huelle = untere_huelle +  obere_huelle

    return konvexe_huelle

def moment_einzelkraft_um_achse(achse: Achse, kraft: Vec3, angriffspunkt: Vec3) -> float:
    """
    Berechnet das Moment einer Einzelkraft um eine gegebene Achse.

    Parameter
    ---------
    achse : Achse
        Die Achse, um die das Moment berechnet wird.
    kraft : Vec3
        Der Kraftvektor (x, y, z).
    angriffspunkt : Vec3
        Der Punkt, an dem die Kraft angreift (x, y, z).

    Rückgabe
    --------
    float : Das Moment der Kraft um die Achse (positiv im Sinne der Rechtsschraube).

    Raises
    ------
    ValueError : falls die Achse keinen gültigen Richtungsvektor hat oder einer der Vektoren nicht genau 3 Komponenten hat
    """
    if len(kraft) != 3 or len(angriffspunkt) != 3:
        raise ValueError("kraft und angriffspunkt müssen Vektoren mit genau 3 Komponenten (x, y, z) sein.")
    if vektor_laenge(achse.richtung) == 0:
        raise ValueError("Die Achse muss einen gültigen Richtungsvektor haben.")

    # Vektor vom Achsenpunkt zum Angriffspunkt
    r = vektor_zwischen_punkten(achse.punkt, angriffspunkt)

    # Kreuzprodukt r x F
    moment_vektor = vektor_kreuzprodukt(r, kraft)

    # Projektion des Momentvektors auf den Achsenrichtungsvektor (normiert)
    achsen_richtung_norm = vektor_normieren(achse.richtung)
    moment = vektor_skalarprodukt(moment_vektor, achsen_richtung_norm)

    return moment

def flaecheninhalt_polygon(punkte: Sequence[Vec3]) -> float:
    """
    Berechnet den Flächeninhalt eines ebenen (nicht selbstschneidenden) 3D-Polygons.
    Punkte müssen auf einer Ebene liegen und in Reihenfolge des Randes angegeben sein.

    Parameter
    ---------
    punkte : Sequenz von Vec3
        Die Punkte des Polygons.

    Rückgabe
    --------
    float : Der Flächeninhalt des Polygons.

    Raises
    ------
    ValueError : bei leerer Liste oder kollinearen Punkten
    """
    if punkte is None:
        raise ValueError("punkte darf nicht None sein.")

    n = len(punkte)
    if n < 3:
        raise ValueError("flaecheninhalt_polygon erwartet mindestens drei Punkte.")

    # --- Newell-Normale berechnen (robust, auch für konkave Polygone) ---
    Nx = Ny = Nz = 0.0
    for i in range(n):
        j = (i + 1) % n
        xi, yi, zi = map(float, punkte[i])
        xj, yj, zj = map(float, punkte[j])
        # einfachste Newell-Variante: Summe der Kreuzprodukte Pi x Pj
        cx, cy, cz = vektor_kreuzprodukt((xi, yi, zi), (xj, yj, zj))
        Nx += cx; Ny += cy; Nz += cz
    N = (Nx, Ny, Nz)
    # Normale normieren (wirft bei Länge 0 eine Exception)
    try:
        n_hat = vektor_normieren(N)
    except ValueError:
        # Kollinear / degeneriert
        raise ValueError("Degeneriertes Polygon: Normale hat Länge 0 (Punkte evtl. kollinear).")
    # --- Triangulation um P0 ---
    P0 = tuple(map(float, punkte[0]))
    A_sum = 0.0
    for i in range(1, n - 1):
        Pi = tuple(map(float, punkte[i]))
        Pj = tuple(map(float, punkte[i+1]))

        # v1 = Pi - P0, v2 = Pj - P0
        v1 = vektor_zwischen_punkten(P0, Pi)
        v2 = vektor_zwischen_punkten(P0, Pj)

        # vorzeichenbehaftete Teilfläche: 0.5 * ( (v1 x v2) · n_hat )
        cx, cy, cz = vektor_kreuzprodukt(v1, v2)
        area_i = 0.5 * vektor_skalarprodukt((cx, cy, cz), n_hat)

        A_sum += area_i
    return abs(A_sum)

def is_senkrecht(methode: str, vecs: Optional[Sequence[Vec3]] = None, punkte: Optional[Sequence[Vec3]] = None) -> bool:
    """
    Prüft, ob die gegebenen Punkte senkrecht zueinander stehen.

    Parameter
    ---------
    methode : str
        Was wird geprüft: aktuell nur 'vecs' (beleibig viele Vektoren).
    vecs : Sequenz von Vec3
        Die Vektoren, die geprüft werden sollen.
    punkte : Sequenz von Vec3
        Eckpunkte von Ebenen (derzeit nicht verwendet).

    Rückgabe
    --------
    bool : True, wenn die Vektoren senkrecht zueinander stehen, sonst False.

    Raises
    ------
    ValueError : falls die Methode ungültig ist oder einer der Punkte nicht genau 3 Komponenten hat
    """
    if methode not in ('vecs'):
        raise ValueError("Ungültige Methode. Erlaubt ist 'vecs'.")

    n = len(vecs)
    for i in range(n):
        for j in range(i + 1, n):
            a = vecs[i]
            b = vecs[j]
            if len(a) != 3 or len(b) != 3:
                raise ValueError("is_senkrecht erwartet Vektoren mit genau 3 Komponenten (x, y, z).")
            if abs(vektor_skalarprodukt(a, b)) > _EPS:
                return False
    return True

def is_parallel(methode: str, vecs: Optional[Sequence[Vec3]] = None, punkte: Optional[Sequence[Vec3]] = None) -> bool:
    """
    Prüft, ob die gegebenen Punkte parallel zueinander stehen.

    Parameter
    ---------
    methode : str
        Was wird geprüft: 'vecs' (beleibig viele Vektoren), 'vecs/ebene' (Vektoren und Ebene).
    vecs : Sequenz von Vec3
        Die Vektoren, die geprüft werden sollen.
    punkte : Sequenz von Vec3
        Eckpunkte von Ebenen (nur bei methode 'vecs/ebene').

    Rückgabe
    --------
    bool : True, wenn die Vektoren parallel zueinander stehen, sonst False.

    Raises
    ------
    ValueError : falls die Methode ungültig ist oder einer der Punkte nicht genau 3 Komponenten hat
    """
    
    if methode == 'vecs':
        n = len(vecs)
        if n < 2:
            return True  # Weniger als 2 Vektoren sind immer parallel

        ref = vecs[0]
        for i in range(1, n):
            v = vecs[i]
            if len(ref) != 3 or len(v) != 3:
                raise ValueError("is_parallel erwartet Vektoren mit genau 3 Komponenten (x, y, z).")
            kreuz = vektor_kreuzprodukt(ref, v)
            if vektor_laenge(kreuz) > _EPS:
                return False
        return True
    
    elif methode == 'vecs/ebene':
        if punkte is None or len(punkte) < 3:
            raise ValueError("Für methode 'vecs/ebene' werden mindestens 3 Punkte für die Ebene benötigt.")

        # Ebene normal berechnen
        v1 = vektor_zwischen_punkten(punkte[0], punkte[1])
        v2 = vektor_zwischen_punkten(punkte[0], punkte[2])
        ebenen_normal = vektor_kreuzprodukt(v1, v2)
        try:
            ebenen_normal = vektor_normieren(ebenen_normal)
        except ValueError:
            raise ValueError("Die Punkte der Ebene sind kollinear; keine gültige Ebene definiert.")

        for v in vecs:
            if len(v) != 3:
                raise ValueError("is_parallel erwartet Vektoren mit genau 3 Komponenten (x, y, z).")
            dot = vektor_skalarprodukt(v, ebenen_normal)
            if abs(dot) > _EPS:
                return False
        return True
    else:
        raise ValueError("Ungültige Methode. Erlaubt sind 'vecs' und 'vecs/ebene'.")
    
def is_ebene(punkte: Sequence[Vec3]) -> bool:
    """
    Prüft, ob die gegebenen Punkte auf einer Ebene liegen.

    Parameter
    ---------
    punkte : Sequenz von Vec3
        Die Punkte, die geprüft werden sollen.

    Rückgabe
    --------
    bool : True, wenn die Punkte auf einer Ebene liegen, sonst False.

    Raises
    ------
    ValueError : falls weniger als drei Punkte gegeben sind oder einer der Punkte nicht genau 3 Komponenten hat
    """
    if len(punkte) < 3:
        raise ValueError("Mindestens drei Punkte sind erforderlich, um eine Ebene zu definieren.")

    v1 = vektor_zwischen_punkten(punkte[0], punkte[1])
    v2 = vektor_zwischen_punkten(punkte[0], punkte[2])
    ebenen_normal = vektor_kreuzprodukt(v1, v2)

    try:
        ebenen_normal = vektor_normieren(ebenen_normal)
    except ValueError:
        return False  # Kollinear / degeneriert

    for i in range(3, len(punkte)):
        pi = punkte[i]
        v = vektor_zwischen_punkten(punkte[0], pi)
        if not is_senkrecht('vecs', vecs=[v, ebenen_normal]):
            return False
    return True
    
def normale_zu_ebene(punkte: Sequence[Vec3]) -> Vec3:
    """
    Berechnet den Normalenvektor einer Ebene, definiert durch mindestens drei Punkte.

    Parameter
    ---------
    punkte : Sequenz von Vec3
        Mindestens drei Punkte, die die Ebene definieren.

    Rückgabe
    --------
    Vec3 : Der normierte Normalenvektor der Ebene.

    Raises
    ------
    ValueError : falls weniger als drei Punkte gegeben sind oder die Punkte kollinear sind
    """
    if len(punkte) < 3:
        raise ValueError("Mindestens drei Punkte sind erforderlich, um eine Ebene zu definieren.")
    if not is_ebene(punkte):
        raise ValueError("Die gegebenen Punkte liegen nicht auf einer Ebene.")

    v1 = vektor_zwischen_punkten(punkte[0], punkte[1])
    v2 = vektor_zwischen_punkten(punkte[0], punkte[2])
    normal = vektor_kreuzprodukt(v1, v2)

    try:
        return vektor_normieren(normal)
    except ValueError:
        raise ValueError("Die gegebenen Punkte sind kollinear; kein gültiger Normalenvektor existiert.")