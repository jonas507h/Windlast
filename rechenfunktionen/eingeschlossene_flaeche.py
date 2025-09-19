from typing import Dict, Callable, Sequence
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, ObjektTyp
from materialdaten.catalog import catalog
from rechenfunktionen.geom3d import Vec3, abstand_punkte

_EPS = 1e-9  # numerische Toleranz für Längen

def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    punkte: Sequence[Vec3],
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
        raise ValueError("punkte muss eine Sequenz aus mindestens 2 Punkten sein.")
    if objekttyp == ObjektTyp.TRAVERSE or objekttyp == ObjektTyp.ROHR:
        if len(punkte) != 2:
            raise ValueError(f"Für {objekttyp.name} werden genau 2 Punkte (Start- und Endpunkt) erwartet.")
        if abstand_punkte(punkte[0], punkte[1]) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")

def _eingeschlossene_flaeche_default(
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    punkte: Sequence[Vec3],
) -> Zwischenergebnis:
    if objekttyp == ObjektTyp.TRAVERSE:
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        traverse = catalog.get_traverse(objekt_name_intern)
        hoehe = traverse.hoehe
        wert = laenge * hoehe

        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )
    
    elif objekttyp == ObjektTyp.ROHR:
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        rohr = catalog.get_rohr(objekt_name_intern)
        d_aussen = rohr.d_aussen
        wert = laenge * d_aussen

        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )

    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH: Dict[Norm, Callable[[ObjektTyp, str, Sequence[Vec3]], Zwischenergebnis]] = {
    Norm.DEFAULT: _eingeschlossene_flaeche_default,
}

def eingeschlossene_flaeche(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    punkte: Sequence[Vec3],
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, objekt_name_intern, punkte)
    funktion = _DISPATCH.get(norm, _eingeschlossene_flaeche_default)
    return funktion(objekttyp, objekt_name_intern, punkte)
