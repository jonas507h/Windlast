from typing import Dict, Callable, Sequence, Optional
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import Vec3, abstand_punkte
from windlast_CORE.datenstruktur.konstanten import _EPS

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
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "eingeschlossene_flaeche_default",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
    }

    if objekttyp == ObjektTyp.TRAVERSE:
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        traverse = catalog.get_traverse(objekt_name_intern)
        hoehe = traverse.hoehe

        if hoehe is None or hoehe <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="EINGESCHL/CATALOG_MISSING",
                text=f"Traverse '{objekt_name_intern}': ungültige Höhe ({hoehe}).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="eingeschlossene_flaeche",
                wert=float("nan"),
                label="math.eingeschlossene_flaeche_traverse.label",
                formelzeichen="math.eingeschlossene_flaeche_traverse.symbol",
                priority=20,
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = laenge * hoehe

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="eingeschlossene_flaeche",
            wert=wert,
            label="math.eingeschlossene_flaeche_traverse.label",
            formelzeichen="math.eingeschlossene_flaeche_traverse.symbol",
            formel="math.eingeschlossene_flaeche_traverse.formula",
            priority=20,
            einheit="m²",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)

# Rohr wird nicht mehr genutzt
    elif objekttyp == ObjektTyp.ROHR:
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        rohr = catalog.get_rohr(objekt_name_intern)
        d_aussen = rohr.d_aussen

        if d_aussen is None or d_aussen <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="EINGESCHL/CATALOG_MISSING",
                text=f"Rohr '{objekt_name_intern}': ungültiger Außendurchmesser ({d_aussen}).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="eingeschlossene_flaeche",
                wert=float("nan"),
                label="Eingeschlossene Fläche A_C",
                formelzeichen="A_C",
                formel="A_C = L · d_aussen",
                einheit="m²",
                priority=20,
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = laenge * d_aussen

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="eingeschlossene_flaeche",
            wert=wert,
            label="Eingeschlossene Fläche A_C",
            formelzeichen="A_C",
            formel="A_C = L · d_aussen",
            einheit="m²",
            priority=20,
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)

    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _eingeschlossene_flaeche_default,
}

def eingeschlossene_flaeche(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    punkte: Sequence[Vec3],
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "eingeschlossene_flaeche",
    }

    try:
        _validate_inputs(objekttyp, objekt_name_intern, punkte)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="EINGESCHL/INPUT_INVALID",
            text=str(e),
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="eingeschlossene_flaeche",
            wert=float("nan"),
            label="math.eingeschlossene_flaeche.label",
            formelzeichen="math.eingeschlossene_flaeche.symbol",
            einheit="m²",
            priority=20,
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte,
        protokoll=protokoll, breadcrumb=base_bc,
    )
