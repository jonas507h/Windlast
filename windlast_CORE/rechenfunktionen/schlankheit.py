# rechenfunktionen/schlankheit.py
from __future__ import annotations
from typing import Dict, Callable, Optional, Sequence, Mapping, Any, Callable
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis
from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import Vec3, abstand_punkte
from windlast_CORE.rechenfunktionen.interpolation import interpol_2D
from windlast_CORE.datenstruktur.konstanten import _EPS
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
    Zwischenergebnis,
)

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

def _schlankheit_DinEn1991_1_4_2010_12(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str],
    punkte: Sequence[Vec3],
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:

    if objekttyp == ObjektTyp.TRAVERSE:
        start, ende = punkte[0], punkte[1]
        laenge = abstand_punkte(start, ende)

        traverse = catalog.get_traverse(objekt_name_intern)
        hoehe = traverse.hoehe
        if hoehe is None or hoehe <= 0:
            local_ctx = merge_kontext(kontext, {
                "phase": "Zwischenwerte",
                "metrik": "λ",
                "input_source": "Katalog",
                "laenge": f"{laenge}m",
                "hoehe": f"{hoehe}m",
            })
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="SCHLANKHEIT/CATALOG_MISSING",
                text=f"Traverse '{objekt_name_intern}': ungültige Höhe ({hoehe}m).",
                kontext=local_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Schlankheit λ", wert=float("nan"),
                                      einzelwerte=[laenge, hoehe]),
                kontext=merge_kontext(local_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        faktor = interpol_2D([15.0, 50.0], [2.0, 1.4], laenge)
        if laenge < 15.0 or laenge > 50.0:
            protokolliere_msg(
                protokoll,
                severity=Severity.WARN,
                code="SCHLANKHEIT/EXTRAPOLATION",
                text=f"Faktor via Extrapolation für L={laenge:.3f} außerhalb [15, 50].",
                kontext=merge_kontext(kontext, {"phase": "ZWISCHENWERTE", "bounds": [15.0, 50.0], "laenge": laenge}),
            )

        rechenwert = faktor * (laenge / hoehe)
        wert = min(rechenwert, 70.0)

        if wert < rechenwert:
            protokolliere_msg(
                protokoll,
                severity=Severity.INFO,
                code="SCHLANKHEIT/CLAMP_70",
                text=f"Schlankheit auf 70 gekappt (Rechenwert {rechenwert:.3f}).",
                kontext=merge_kontext(kontext, {"phase": "Zwischenwerte", "rechenwert": rechenwert}),
            )

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Schlankheit λ",
                wert=wert,
                einzelwerte=[laenge, hoehe],
                # Optional: Wenn du Formeln/Quellen an dieser Stelle schon kennst:
                # formel="λ = f(L) * L / h", quelle_formel="DIN EN 1991-1-4:2010-12, Tab ..."
            ),
            kontext=merge_kontext(kontext, {"phase": "Zwischenwerte"}),
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.ROHR:
        start, ende = punkte[0], punkte[1]
        laenge = abstand_punkte(start, ende)

        rohr = catalog.get_rohr(objekt_name_intern)
        d_aussen = rohr.d_aussen
        if d_aussen is None or d_aussen <= 0:
            local_ctx = merge_kontext(kontext, {
                "phase": "Zwischenwerte",
                "metrik": "λ",
                "input_source": "Katalog",
                "laenge": f"{laenge}m",
                "d_aussen": f"{d_aussen}m",
            })
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="SCHLANKHEIT/CATALOG_MISSING",
                text=f"Rohr '{objekt_name_intern}': ungültiger Außendurchmesser ({d_aussen}).",
                kontext=local_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Schlankheit λ", wert=float("nan"),
                                      einzelwerte=[laenge, d_aussen]),
                kontext=merge_kontext(local_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        faktor = interpol_2D([15.0, 50.0], [2.0, 1.4], laenge)

        rechenwert = faktor * (laenge / d_aussen)
        wert = min(rechenwert, 70.0)

        if wert < rechenwert:
            protokolliere_msg(
                protokoll,
                severity=Severity.INFO,
                code="SCHLANKHEIT/CLAMP_70",
                text=f"Schlankheit auf 70 gekappt (Rechenwert {rechenwert:.3f}).",
                kontext=merge_kontext(kontext, {"phase": "Zwischenwerte", "rechenwert": rechenwert}),
            )

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Schlankheit λ",
                wert=wert,
                einzelwerte=[laenge, d_aussen],
            ),
            kontext=merge_kontext(kontext, {"phase": "Zwischenwerte"}),
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
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Schlankheit",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "norm": getattr(norm, "value", str(norm)),
    })

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
            kontext=base_ctx,
        )
        # NaN-Ergebnis zurück und minimal dokumentieren
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Schlankheit λ", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    _validate_inputs(objekttyp, objekt_name_intern, punkte)
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte,
        protokoll=protokoll, kontext=base_ctx
    )
