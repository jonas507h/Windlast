from typing import Dict, Callable, Optional, Sequence
import math
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

def _validate_inputs(
    objekttyp: ObjektTyp,
    objekttyp_name_intern: str,
    staudruck: float,        # N/m²
    zaehigkeit: float,       # m²/s (kinematische Viskosität ν)
    luftdichte: float,       # kg/m³
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if staudruck <= 0:
        raise ValueError("staudruck muss > 0 sein (in N/m²).")
    if zaehigkeit <= 0:
        raise ValueError("zaehigkeit muss > 0 sein (in m²/s).")
    if luftdichte <= 0:
        raise ValueError("luftdichte muss > 0 sein (in kg/m³).")

def _reynoldszahl_DinEn1991_1_4_2010_12(
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    staudruck: float,
    zaehigkeit: float,
    luftdichte: float,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "reynoldszahl",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
    })

    if objekttyp == ObjektTyp.TRAVERSE:
        traverse = catalog.get_traverse(objekt_name_intern)
        charak_Laenge = traverse.d_gurt  # charakteristische Länge (hier: Durchmesser Gurt)
        
        if not charak_Laenge or charak_Laenge <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="REYNOLDS/CATALOG_MISSING",
                text=f"Traverse '{objekt_name_intern}': ungültiger Gurt-Durchmesser ({charak_Laenge}).",
                kontext=merge_kontext(base_ctx, {"input_source": "catalog"}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Reynoldszahl Re",
                    wert=float("nan"),
                    einzelwerte=[staudruck, luftdichte, geschwindigkeit, charak_Laenge, zaehigkeit],
                    formel="Re = v·L/ν; v = √(2·q/ρ)",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))
        
        geschwindigkeit = math.sqrt(2.0 * staudruck / luftdichte)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Strömungsgeschwindigkeit v",
                wert=geschwindigkeit,
                einzelwerte=[staudruck, luftdichte],
                formel="v = √(2·q/ρ)",
                einheit="m/s",
            ),
            kontext=base_ctx,
        )

        wert = geschwindigkeit * charak_Laenge / zaehigkeit

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Reynoldszahl Re",
                wert=wert,
                einzelwerte=[staudruck, luftdichte, geschwindigkeit, charak_Laenge, zaehigkeit],
                formel="Re = v·L/ν; v = √(2·q/ρ)",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.ROHR:
        geschwindigkeit = math.sqrt(2.0 * staudruck / luftdichte)
        rohr = catalog.get_rohr(objekt_name_intern)
        charak_Laenge = rohr.d_aussen  # charakteristische Länge (hier: Außendurchmesser)

        if not charak_Laenge or charak_Laenge <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="REYNOLDS/CATALOG_MISSING",
                text=f"Rohr '{objekt_name_intern}': ungültiger Außendurchmesser ({charak_Laenge}).",
                kontext=merge_kontext(base_ctx, {"input_source": "catalog"}),
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Reynoldszahl Re",
                    wert=float("nan"),
                    einzelwerte=[staudruck, luftdichte, geschwindigkeit, charak_Laenge, zaehigkeit],
                    formel="Re = v·L/ν; v = √(2·q/ρ)",
                ),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = geschwindigkeit * charak_Laenge / zaehigkeit

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Reynoldszahl Re",
                wert=wert,
                einzelwerte=[staudruck, luftdichte, geschwindigkeit, charak_Laenge, zaehigkeit],
                formel="Re = v·L/ν; v = √(2·q/ρ)",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)
    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _reynoldszahl_DinEn1991_1_4_2010_12,
    Norm.DIN_EN_1991_1_4_2010_12: _reynoldszahl_DinEn1991_1_4_2010_12,
}

def reynoldszahl(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    staudruck: float,       # N/m²
    zaehigkeit: float,      # m²/s
    luftdichte: float,      # kg/m³
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "reynoldszahl",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs(objekttyp, objekt_name_intern, staudruck, zaehigkeit, luftdichte)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="REYNOLDS/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Reynoldszahl Re", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))

    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, staudruck, zaehigkeit, luftdichte,
        protokoll=protokoll, kontext=base_ctx,
    )

