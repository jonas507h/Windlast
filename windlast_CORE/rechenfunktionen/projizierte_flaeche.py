from typing import Dict, Callable, Optional, Sequence, Tuple
import math
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.datenstruktur.enums import Norm, TraversenTyp, ObjektTyp, Severity, senkrechteFlaecheTyp
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektor_laenge, abstand_punkte, flaecheninhalt_polygon
from windlast_CORE.datenstruktur.konstanten import _EPS

def _validate_inputs(
    objekttyp: ObjektTyp,
    punkte: Sequence[Vec3],
    objekt_name_intern: Optional[str] = None,
    windrichtung: Optional[Vec3] = None,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    # Objekt-spezifische Mindestanforderungen
    if objekttyp == ObjektTyp.TRAVERSE:
        if windrichtung is None:
            raise ValueError("Für TRAVERSE wird windrichtung benötigt.")
        n = vektor_laenge(windrichtung)
        if not (0.999 <= n <= 1.001):
            raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n:.6f}.")
        if objekt_name_intern is None:
            raise ValueError("Für TRAVERSE wird objekt_name_intern benötigt.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
            raise ValueError("Für TRAVERSE werden mind. Start- und Endpunkt erwartet.")
        if abstand_punkte(punkte[0], punkte[1]) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
    elif objekttyp == ObjektTyp.ROHR:
        if objekt_name_intern is None:
            raise ValueError("Für ROHR wird objekt_name_intern benötigt.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
            raise ValueError("Für ROHR werden mind. Start- und Endpunkt erwartet.")
        if abstand_punkte(punkte[0], punkte[1]) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        if not isinstance(punkte, (list, tuple)) or len(punkte) != 4:
            raise ValueError("Für SENKRECHTE_FLAECHE werden genau 4 Eckpunkte erwartet.")
        if senkrechte_flaeche_typ is None:
            raise ValueError("Für SENKRECHTE_FLAECHE wird senkrechte_flaeche_typ benötigt.")
    else:
        # Generisch: mind. 1 Punktliste übergeben
        if not isinstance(punkte, (list, tuple)) or len(punkte) == 0:
            raise ValueError("punkte darf nicht leer sein.")

def _projizierte_flaeche_default(
    objekttyp: ObjektTyp,
    punkte: Sequence[Vec3],
    objekt_name_intern: Optional[str] = None,
    windrichtung: Optional[Vec3] = None,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "projizierte_flaeche_default",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
    }

    if objekttyp == ObjektTyp.TRAVERSE:
        # Punkte interpretieren: [start, ende, (optional) orientierung]
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        traverse = catalog.get_traverse(objekt_name_intern)
        try:
            _ = TraversenTyp.from_points(traverse.anzahl_gurtrohre)
        except ValueError as e:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="PROJ/TRAVERSENTYP_INVALID",
                text=f"Traverse '{objekt_name_intern}': ungültige Gurtanzahl – {e}",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="projizierte_flaeche",
                wert=float("nan"),
                label="math.bezugsflaeche_traverse.label",
                formelzeichen="math.bezugsflaeche_traverse.symbol",
                einheit="m²",
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        d_gurt = traverse.d_gurt
        d_diag = traverse.d_diagonalen

        if not d_gurt or d_gurt <= 0 or not d_diag or d_diag <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="PROJ/CATALOG_MISSING",
                text=f"Traverse '{objekt_name_intern}': ungültige Durchmesser (d_gurt={d_gurt}, d_diag={d_diag}).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="projizierte_flaeche",
                wert=float("nan"),
                label="math.bezugsflaeche_traverse.label",
                formelzeichen="math.bezugsflaeche_traverse.symbol",
                einheit="m²",
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))
        
        # Vereinfachter Ansatz nach Ebner
        wert = (2.0 * laenge * d_gurt) + (3.2 * laenge * d_diag)

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="projizierte_flaeche",
            wert=wert,
            label="math.bezugsflaeche_traverse.label",
            formelzeichen="math.bezugsflaeche_traverse.symbol",
            formel="math.bezugsflaeche_traverse.formula",
            einheit="m²",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)

    elif objekttyp == ObjektTyp.ROHR:
        startpunkt, endpunkt = punkte[0], punkte[1]
        laenge = abstand_punkte(startpunkt, endpunkt)

        rohr = catalog.get_rohr(objekt_name_intern)
        d_aussen = rohr.d_aussen

        if not d_aussen or d_aussen <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="PROJ/CATALOG_MISSING",
                text=f"Rohr '{objekt_name_intern}': ungültiger Außendurchmesser ({d_aussen}).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="projizierte_flaeche",
                wert=float("nan"),
                label="math.bezugsflaeche_rohr.label",
                formelzeichen="math.bezugsflaeche_rohr.symbol",
                einheit="m²",
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = laenge * d_aussen

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="projizierte_flaeche",
            wert=wert,
            label="math.bezugsflaeche_rohr.label",
            formelzeichen="math.bezugsflaeche_rohr.symbol",
            formel="math.bezugsflaeche_rohr.formula",
            einheit="m²",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        wert = flaecheninhalt_polygon(punkte)

        if senkrechte_flaeche_typ == senkrechteFlaecheTyp.WAND:
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="projizierte_flaeche",
                wert=wert,
                label="math.bezugsflaeche_wand.label",
                formelzeichen="math.bezugsflaeche_wand.symbol",
                einheit="m²",
                meta=base_meta,
            )
        elif senkrechte_flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="projizierte_flaeche",
                wert=wert,
                label="math.bezugsflaeche_anzeigetafel.label",
                formelzeichen="math.bezugsflaeche_anzeigetafel.symbol",
                einheit="m²",
                meta=base_meta,
             )
        return Zwischenergebnis(wert=wert)

    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH_PROJ: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _projizierte_flaeche_default,
}

def projizierte_flaeche(
    norm: Norm,
    objekttyp: ObjektTyp,
    punkte: Sequence[Vec3],   # TRAVERSE: [start, ende, (optional) orientierung]
    objekt_name_intern: Optional[str] = None,
    windrichtung: Optional[Vec3] = None,       # Einheitsvektor
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "projizierte_flaeche",
    }

    try:
        _validate_inputs(objekttyp, punkte, objekt_name_intern, windrichtung, senkrechte_flaeche_typ)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="PROJ/INPUT_INVALID",
            text=str(e),
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="projizierte_flaeche",
            wert=float("nan"),
            label="math.bezugsflaeche.label",
            formelzeichen="math.bezugsflaeche.symbol",
            einheit="m²",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))

    funktion = _DISPATCH_PROJ.get(norm, _DISPATCH_PROJ[Norm.DEFAULT])
    return funktion(
        objekttyp, punkte, objekt_name_intern, windrichtung, senkrechte_flaeche_typ,
        protokoll=protokoll, breadcrumb=base_bc,
    )