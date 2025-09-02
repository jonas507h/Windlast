# rechenfunktionen/schlankheit.py
from __future__ import annotations
from typing import Dict, Callable, Optional, Sequence
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, ObjektTyp
from materialdaten.catalog import catalog
from rechenfunktionen.geom3d import Vec3, abstand_punkte
from rechenfunktionen.interpolation import interpol_2D

_EPS = 1e-9

def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],  # TRAVERSE: [start, ende]
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if objekttyp == ObjektTyp.TRAVERSE:
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
            raise ValueError("Für TRAVERSE werden [start, ende] erwartet.")
        if abstand_punkte(punkte[0], punkte[1]) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
        if not objekt_name_intern:
            raise ValueError("Für TRAVERSE ist objekt_name_intern erforderlich.")
    else:
        # Für andere Objekttypen noch unklar → Platzhalter
        raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

def _schlankheit_default(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
) -> Zwischenergebnis:

    if objekttyp == ObjektTyp.TRAVERSE:
        start, ende = punkte[0], punkte[1]
        laenge = abstand_punkte(start, ende)

        traverse = catalog.get_traverse(objekt_name_intern)
        hoehe = traverse.hoehe
        if hoehe is None or hoehe <= 0:
            raise ValueError(f"Traverse '{objekt_name_intern}': ungültige Höhe ({hoehe}).")

        faktor = interpol_2D([15.0, 50.0], [2.0, 1.4], laenge)

        rechenwert = faktor * (laenge / hoehe)
        wert = min(rechenwert, 70.0)

        return Zwischenergebnis(
            wert=wert,
            formel="---",
            quelle_formel="---",
            formelzeichen=["---", "---", "---"],
            quelle_formelzeichen=["---"]
        )

    # Andere Objekttypen:
    raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[[ObjektTyp, Optional[str], Sequence[Vec3]], Zwischenergebnis]] = {
    Norm.DEFAULT: _schlankheit_default,
}

def schlankheit(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],           # TRAVERSE: [start, ende]
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, objekt_name_intern, punkte)
    funktion = _DISPATCH.get(norm, _schlankheit_default)
    return funktion(objekttyp, objekt_name_intern, punkte)
