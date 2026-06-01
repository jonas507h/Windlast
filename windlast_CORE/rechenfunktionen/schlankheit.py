# rechenfunktionen/schlankheit.py
from __future__ import annotations
from typing import Dict, Callable, Optional, Sequence, Mapping, Any, Callable
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis
from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import Vec3, abstand_punkte
from windlast_CORE.rechenfunktionen.interpolation import interpol_2D
from windlast_CORE.datenstruktur.konstanten import _EPS
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner

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
    elif objekttyp == ObjektTyp.ROHR:
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
            raise ValueError("Für ROHR werden [start, ende] erwartet.")
        if abstand_punkte(punkte[0], punkte[1]) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
        if not objekt_name_intern:
            raise ValueError("Für ROHR ist objekt_name_intern erforderlich.")
    else:
        # Für andere Objekttypen noch unklar → Platzhalter
        raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

def _schlankheit_DinEn1991_1_4_2010_12(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "schlankheit_DinEn1991_1_4_2010_12",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
    }

    if objekttyp == ObjektTyp.TRAVERSE:
        start, ende = punkte[0], punkte[1]
        laenge = abstand_punkte(start, ende)

        traverse = catalog.get_traverse(objekt_name_intern)
        hoehe = min(traverse.A_hoehe, traverse.B_hoehe)  # TODO: Abhängig von Ausrichtung machen
        if hoehe is None or hoehe <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="SCHLANKHEIT/CATALOG_MISSING",
                text=f"Traverse '{objekt_name_intern}': ungültige Höhe ({hoehe}m).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="schlankheit",
                wert=float("nan"),
                label="math.schlankheit_traverse.label",
                formelzeichen="math.schlankheit_traverse.symbol",
                priority=20,
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        faktor = interpol_2D([15.0, 50.0], [2.0, 1.4], laenge)

        rechenwert = faktor * (laenge / hoehe)
        wert = min(rechenwert, 70.0)

        # if wert < rechenwert:
        #     protokolliere_msg(
        #         protokoll,
        #         severity=Severity.INFO,
        #         code="SCHLANKHEIT/CLAMP_70",
        #         text=f"Schlankheit auf 70 gekappt (Rechenwert {rechenwert:.3f}).",
        #         breadcrumb=base_bc,
        #         meta=base_meta,
        #     )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="schlankheit",
            wert=wert,
            label="math.schlankheit_traverse.label",
            formelzeichen="math.schlankheit_traverse.symbol",
            formel="math.schlankheit_traverse.formula",
            priority=20,
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.ROHR:
        start, ende = punkte[0], punkte[1]
        laenge = abstand_punkte(start, ende)

        rohr = catalog.get_rohr(objekt_name_intern)
        d_aussen = rohr.d_aussen
        if d_aussen is None or d_aussen <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="SCHLANKHEIT/CATALOG_MISSING",
                text=f"Rohr '{objekt_name_intern}': ungültiger Außendurchmesser ({d_aussen}).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="schlankheit",
                wert=float("nan"),
                label="math.schlankheit_rohr.label",
                formelzeichen="math.schlankheit_rohr.symbol",
                priority=20,
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        faktor = interpol_2D([15.0, 50.0], [1.0, 0.7], laenge)

        rechenwert = faktor * (laenge / d_aussen)
        wert = min(rechenwert, 70.0)

        # if wert < rechenwert:
        #     protokolliere_msg(
        #         protokoll,
        #         severity=Severity.INFO,
        #         code="SCHLANKHEIT/CLAMP_70",
        #         text=f"Schlankheit auf 70 gekappt (Rechenwert {rechenwert:.3f}).",
        #         breadcrumb=base_bc,
        #         meta=base_meta,
        #     )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="schlankheit",
            wert=wert,
            label="math.schlankheit_rohr.label",
            formelzeichen="math.schlankheit_rohr.symbol",
            formel="math.schlankheit_rohr.formula",
            priority=20,
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)

    # Andere Objekttypen:
    raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _schlankheit_DinEn1991_1_4_2010_12,
    Norm.DIN_EN_1991_1_4_2010_12: _schlankheit_DinEn1991_1_4_2010_12,
}

def schlankheit(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],           # TRAVERSE, ROHR: [start, ende]
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "schlankheit",
    }

    # Eingaben prüfen: fachliche Fehler -> Message + NaN statt harter Exception
    try:
        _validate_inputs(objekttyp, objekt_name_intern, punkte)  # deine bestehende Prüflogik
    except NotImplementedError:
        # programmatischer Zustand: weiterhin nach oben geben
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="SCHLANKHEIT/INPUT_INVALID",
            text=str(e),
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="schlankheit",
            wert=float("nan"),
            label="math.schlankheit.label",
            formelzeichen="math.schlankheit.symbol",
            priority=20,
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte,
        protokoll=protokoll, breadcrumb=base_bc
    )
