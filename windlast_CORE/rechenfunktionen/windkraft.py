# rechenfunktionen/windkraft.py
from __future__ import annotations
from typing import Dict, Callable, Optional
import math

from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity, senkrechteFlaecheTyp
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)

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
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    if objekttyp == ObjektTyp.TRAVERSE:
        wert = kraftbeiwert * staudruck * projizierte_flaeche

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft F_w",
                wert=wert,
                einzelwerte=[kraftbeiwert, staudruck, projizierte_flaeche],
                formel="F_W = c_f · q · A",
                quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 5.3",
                einheit="N",
            ),
            kontext=merge_kontext(kontext, {
                "funktion": "Windkraft",
                "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
            }),
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.ROHR:
        wert = kraftbeiwert * staudruck * projizierte_flaeche

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft F_w",
                wert=wert,
                einzelwerte=[kraftbeiwert, staudruck, projizierte_flaeche],
                formel="F_W = c_f · q · A",
                quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 5.3",
                einheit="N",
            ),
            kontext=merge_kontext(kontext, {
                "funktion": "Windkraft",
                "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
            }),
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        if senkrechte_flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            wert = kraftbeiwert * staudruck * projizierte_flaeche

            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Windkraft F_w",
                    wert=wert,
                    einzelwerte=[kraftbeiwert, staudruck, projizierte_flaeche],
                    formel="F_W = c_f · q · A",
                    quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 5.3",
                    einheit="N",
                ),
                kontext=merge_kontext(kontext, {
                    "funktion": "Windkraft",
                    "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
                }),
            )
            return Zwischenergebnis(wert=wert)
        elif senkrechte_flaeche_typ == senkrechteFlaecheTyp.WAND:
            wert = float("nan")
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="WINDKRAFT/WAND_NOT_IMPLEMENTED",
                text="Windkraft für senkrechte Flächen des Typs 'WAND' ist noch nicht implementiert.",
                kontext=kontext,
            )
        else:
            wert = float("nan")
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="WINDKRAFT/UNKNOWN_SENKRECHTEFLAECHE_TYP",
                text=f"Unbekannter Typ für senkrechte Fläche: '{senkrechte_flaeche_typ.name}'.",
                kontext=kontext,
            )
    
    else:
        # Andere Objekttypen:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDKRAFT/NOT_IMPLEMENTED",
            text=f"Windkraft für Objekttyp '{objekttyp.value}' ist noch nicht implementiert.",
            kontext=kontext,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Windkraft F_w", wert=float("nan")),
            kontext=kontext,
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
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Windkraft",
        "objekttyp": getattr(objekttyp, "value", str(objekttyp)),
        "norm": getattr(norm, "value", str(norm)),
    })

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
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Windkraft F_w", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, kraftbeiwert, staudruck, projizierte_flaeche, senkrechte_flaeche_typ,
        protokoll=protokoll, kontext=base_ctx,
    )
