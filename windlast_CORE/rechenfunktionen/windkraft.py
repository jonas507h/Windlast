# rechenfunktionen/windkraft.py
from __future__ import annotations
from typing import Dict, Callable, Optional
import math

from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity, senkrechteFlaecheTyp
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner

def _validate_inputs(
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,              # N/m²
    projizierte_flaeche: float,    # m²
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    for name, val, cond in (
        ("kraftbeiwert", kraftbeiwert, kraftbeiwert >= 0),
        ("staudruck", staudruck, staudruck >= 0),
        ("projizierte_flaeche", projizierte_flaeche, projizierte_flaeche >= 0),
    ):
        if not math.isfinite(val):
            raise ValueError(f"{name} muss endlich sein (kein NaN/Inf).")
        if not cond:
            raise ValueError(f"{name} hat unzulässigen Wert ({val}).")
    if objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        if senkrechte_flaeche_typ is None:
            raise ValueError("Für SENKRECHTE_FLAECHE ist senkrechte_flaeche_typ erforderlich.")

def _windkraft_default(
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,
    projizierte_flaeche: float,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "windkraft_default",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
    }
    if objekttyp == ObjektTyp.TRAVERSE:
        wert = kraftbeiwert * staudruck * projizierte_flaeche
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft",
            wert=wert,
            label="math.windkraft_traverse.label",
            formelzeichen="math.windkraft_traverse.symbol",
            formel="math.windkraft_traverse.formula",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.ROHR:
        wert = kraftbeiwert * staudruck * projizierte_flaeche
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft",
            wert=wert,
            label="math.windkraft_rohr.label",
            formelzeichen="math.windkraft_rohr.symbol",
            formel="math.windkraft_rohr.formula",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        flaeche_meta = {
            **base_meta,
            "senkrechte_flaeche_typ": getattr(senkrechte_flaeche_typ, "value", str(senkrechte_flaeche_typ)),
        }
        if senkrechte_flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            wert = kraftbeiwert * staudruck * projizierte_flaeche
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="windkraft",
                wert=wert,
                label="math.windkraft_anzeigetafel.label",
                formelzeichen="math.windkraft_anzeigetafel.symbol",
                formel="math.windkraft_anzeigetafel.formula",
                priority=30,
                einheit="N",
                meta=flaeche_meta,
            )
            return Zwischenergebnis(wert=wert)
        elif senkrechte_flaeche_typ == senkrechteFlaecheTyp.WAND:
            wert = kraftbeiwert * staudruck * projizierte_flaeche
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="windkraft",
                wert=wert,
                label="math.windkraft_wand.label",
                formelzeichen="math.windkraft_wand.symbol",
                formel="math.windkraft_wand.formula",
                priority=30,
                einheit="N",
                meta=flaeche_meta,
            )
            return Zwischenergebnis(wert=wert)
        else:
            wert = float("nan")
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="WINDKRAFT/UNKNOWN_SENKRECHTEFLAECHE_TYP",
                text=f"Unbekannter Typ für senkrechte Fläche: '{senkrechte_flaeche_typ.name}'.",
                breadcrumb=base_bc,
                meta=flaeche_meta,
            )
    
    else:
        # Andere Objekttypen:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDKRAFT/NOT_IMPLEMENTED",
            text=f"Windkraft für Objekttyp '{objekttyp.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft",
            wert=float("nan"),
            label="math.windkraft.label",
            formelzeichen="math.windkraft.symbol",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _windkraft_default,
}

def windkraft(
    norm: Norm,
    objekttyp: ObjektTyp,
    kraftbeiwert: float,
    staudruck: float,
    projizierte_flaeche: float,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,

    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "windkraft",
    }

    try:
        _validate_inputs(objekttyp, kraftbeiwert, staudruck, projizierte_flaeche, senkrechte_flaeche_typ)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDKRAFT/INPUT_INVALID",
            text=str(e),
            breadcrumb=base_bc,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft",
            wert=float("nan"),
            label="math.windkraft.label",
            formelzeichen="math.windkraft.symbol",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, kraftbeiwert, staudruck, projizierte_flaeche, senkrechte_flaeche_typ,
        protokoll=protokoll, breadcrumb=base_bc,
    )
