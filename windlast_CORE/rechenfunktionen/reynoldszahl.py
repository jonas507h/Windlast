from typing import Dict, Callable, Optional, Sequence
import math
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
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
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "reynoldszahl_DinEn1991_1_4_2010_12",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
    }

    if objekttyp == ObjektTyp.TRAVERSE:
        traverse = catalog.get_traverse(objekt_name_intern)
        charak_Laenge = traverse.d_gurt  # charakteristische Länge (hier: Durchmesser Gurt)
        
        if not charak_Laenge or charak_Laenge <= 0:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="REYNOLDS/CATALOG_MISSING",
                text=f"Traverse '{objekt_name_intern}': ungültiger Gurt-Durchmesser ({charak_Laenge}).",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="reynoldszahl",
                wert=float("nan"),
                label="math.reynoldszahl_traverse.label",
                formelzeichen="math.reynoldszahl_traverse.symbol",
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))
        
        geschwindigkeit = math.sqrt(2.0 * staudruck / luftdichte)

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="stroemungsgeschwindigkeit",
            wert=geschwindigkeit,
            label="math.stroemungsgeschwindigkeit.label",
            formelzeichen="math.stroemungsgeschwindigkeit.symbol",
            formel="math.stroemungsgeschwindigkeit.formula",
            einheit="m/s",
            meta=base_meta,
        )

        wert = geschwindigkeit * charak_Laenge / zaehigkeit

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="reynoldszahl",
            wert=wert,
            label="math.reynoldszahl_traverse.label",
            formelzeichen="math.reynoldszahl_traverse.symbol",
            formel="math.reynoldszahl_traverse.formula",
            meta=base_meta,
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
                breadcrumb=base_bc,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="reynoldszahl",
                wert=float("nan"),
                label="math.reynoldszahl_rohr.label",
                formelzeichen="math.reynoldszahl_rohr.symbol",
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))

        wert = (geschwindigkeit * charak_Laenge) / zaehigkeit

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="stroemungsgeschwindigkeit",
            wert=geschwindigkeit,
            label="math.stroemungsgeschwindigkeit.label",
            formelzeichen="math.stroemungsgeschwindigkeit.symbol",
            formel="math.stroemungsgeschwindigkeit.formula",
            einheit="m/s",
            meta=base_meta,
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="reynoldszahl",
            wert=wert,
            label="math.reynoldszahl_rohr.label",
            formelzeichen="math.reynoldszahl_rohr.symbol",
            formel="math.reynoldszahl_rohr.formula",
            meta=base_meta,
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
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "reynoldszahl",
    }

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
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="reynoldszahl",
            wert=float("nan"),
            label="math.reynoldszahl.label",
            formelzeichen="math.reynoldszahl.symbol",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))

    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, staudruck, zaehigkeit, luftdichte,
        protokoll=protokoll, breadcrumb=base_bc,
    )

