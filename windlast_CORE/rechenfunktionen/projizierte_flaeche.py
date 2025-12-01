from typing import Dict, Callable, Optional, Sequence, Tuple
import math
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.datenstruktur.enums import Norm, TraversenTyp, ObjektTyp, Severity
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektor_laenge, abstand_punkte, flaecheninhalt_polygon

_EPS = 1e-9

def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    windrichtung: Optional[Vec3] = None,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    # Windrichtung als Einheitsvektor
    

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
    else:
        # Generisch: mind. 1 Punktliste übergeben
        if not isinstance(punkte, (list, tuple)) or len(punkte) == 0:
            raise ValueError("punkte darf nicht leer sein.")

def _projizierte_flaeche_default(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    windrichtung: Optional[Vec3] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "projizierte_flaeche",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "windrichtung": windrichtung,
    })

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
                kontext=merge_kontext(base_ctx, {"input_source": "catalog"}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Projizierte Fläche A",
                    wert=float("nan"),
                    formel="A = 2·L·d_gurt + 3,2·L·d_diag (Ebner-Vereinfachung)",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
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
                kontext=merge_kontext(base_ctx, {"input_source": "catalog"}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Projizierte Fläche A",
                    wert=float("nan"),
                    formel="A = 2·L·d_gurt + 3,2·L·d_diag",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))
        
        # Vereinfachter Ansatz nach Ebner
        wert = (2.0 * laenge * d_gurt) + (3.2 * laenge * d_diag)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Projizierte Fläche A",
                wert=wert,
                einheit="m²",
                formel="A = 2·L·d_gurt + 3,2·L·d_diag",
            ),
            kontext=base_ctx,
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
                kontext=merge_kontext(base_ctx, {"input_source": "catalog"}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Projizierte Fläche A",
                    wert=float("nan"),
                    formel="A = L·d_aussen",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = laenge * d_aussen

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Projizierte Fläche A",
                wert=wert,
                einheit="m²",
                formel="A = L·d_aussen",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        wert = flaecheninhalt_polygon(punkte)
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Bezugsfläche A",
                wert=wert,
                einheit="m²",
                formel="A_rel = b · h",
                quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 7.4.3",
            ),
            kontext=base_ctx,
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
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],   # TRAVERSE: [start, ende, (optional) orientierung]
    windrichtung: Optional[Vec3] = None,       # Einheitsvektor
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "projizierte_flaeche",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "norm": getattr(norm, "name", str(norm)),
        "windrichtung": windrichtung,
    })

    try:
        _validate_inputs(objekttyp, objekt_name_intern, punkte, windrichtung)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="PROJ/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Projizierte Fläche A_p", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))

    funktion = _DISPATCH_PROJ.get(norm, _DISPATCH_PROJ[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte, windrichtung,
        protokoll=protokoll, kontext=base_ctx,
    )