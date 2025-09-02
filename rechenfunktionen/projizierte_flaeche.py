from typing import Dict, Callable, Optional, Sequence, Tuple
import math
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, TraversenTyp, ObjektTyp
from materialdaten.catalog import catalog
from rechenfunktionen.geom3d import Vec3, vektor_laenge, abstand_punkte

_EPS = 1e-9

def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    windrichtung: Vec3,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    # Windrichtung als Einheitsvektor
    n = vektor_laenge(windrichtung)
    if not (0.999 <= n <= 1.001):
        raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n:.6f}.")

    # Objekt-spezifische Mindestanforderungen
    if objekttyp == ObjektTyp.TRAVERSE:
        if objekt_name_intern is None:
            raise ValueError("Für TRAVERSE wird objekt_name_intern benötigt.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
            raise ValueError("Für TRAVERSE werden mind. Start- und Endpunkt erwartet.")
        if abstand_punkte(punkte[0], punkte[1]) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
    else:
        # Generisch: mind. 1 Punktliste übergeben
        if not isinstance(punkte, (list, tuple)) or len(punkte) == 0:
            raise ValueError("punkte darf nicht leer sein.")

def _projizierte_flaeche_default(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    windrichtung: Vec3,
) -> Zwischenergebnis:

    if objekttyp == ObjektTyp.TRAVERSE:
        # Punkte interpretieren: [start, ende, (optional) orientierung]
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        traverse = catalog.get_traverse(objekt_name_intern)
        try:
            traversentyp = TraversenTyp.from_points(traverse.anzahl_gurtrohre)
        except ValueError as e:
            raise ValueError(f"Ungültige Gurtanzahl für Traverse '{objekt_name_intern}': {e}")

        # Vereinfachter Ansatz nach Ebner
        d_gurt = traverse.d_gurt
        d_diag = traverse.d_diagonalen
        wert = (2.0 * laenge * d_gurt) + (3.2 * laenge * d_diag)

        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )

    elif objekttyp == ObjektTyp.ROHR:
        # TODO: Definition/Quelle (Durchmesser?) noch unklar -> später ergänzen
        raise NotImplementedError("ROHR noch nicht implementiert. Durchmesser-/Modell-Quelle festlegen.")

    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH_PROJ: Dict[Norm, Callable[[ObjektTyp, Optional[str], Sequence[Vec3], Vec3], Zwischenergebnis]] = {
    Norm.DEFAULT: _projizierte_flaeche_default,
}

def projizierte_flaeche(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],          # TRAVERSE: [start, ende, (optional) orientierung]
    windrichtung: Vec3,              # Einheitsvektor
    norm: Norm = Norm.DEFAULT,
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, objekt_name_intern, punkte, windrichtung)
    funktion = _DISPATCH_PROJ.get(norm, _projizierte_flaeche_default)
    return funktion(objekttyp, objekt_name_intern, punkte, windrichtung)
