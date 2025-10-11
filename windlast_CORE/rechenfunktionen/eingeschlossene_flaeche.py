from typing import Dict, Callable, Sequence, Optional
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import Vec3, abstand_punkte

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
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "eingeschlossene_flaeche",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
    })

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
                kontext=merge_kontext(base_ctx, {"input_source": "catalog", "laenge": laenge, "hoehe": hoehe}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Eingeschlossene Fläche A_e",
                    wert=float("nan"),
                    einzelwerte=[laenge, hoehe],
                    formel="A_e = L · h",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = laenge * hoehe

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Eingeschlossene Fläche A_e",
                wert=wert,
                einzelwerte=[laenge, hoehe],
                formel="A_e = L · h",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)
    
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
                kontext=merge_kontext(base_ctx, {"input_source": "catalog", "laenge": laenge, "d_aussen": d_aussen}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Eingeschlossene Fläche A_e",
                    wert=float("nan"),
                    einzelwerte=[laenge, d_aussen],
                    formel="A_e = L · d_aussen",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = laenge * d_aussen

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Eingeschlossene Fläche A_e",
                wert=wert,
                einzelwerte=[laenge, d_aussen],
                formel="A_e = L · d_aussen",
            ),
            kontext=base_ctx,
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
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "eingeschlossene_flaeche",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "norm": getattr(norm, "name", str(norm)),
    })

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
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Eingeschlossene Fläche A_e", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte,
        protokoll=protokoll, kontext=base_ctx,
    )
