# rechenfunktionen/abhebesicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional
from collections.abc import Sequence as _SeqABC

from datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_kontext, protokolliere_msg, protokolliere_doc, make_docbundle
from datenstruktur.enums import Norm, RechenmethodeAbheben, VereinfachungKonstruktion, Lasttyp, Variabilitaet, Severity
from datenstruktur.konstanten import _EPS, aktuelle_konstanten
from datenstruktur.kraefte import Kraefte
from rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert

from rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    obtain_pool,
    get_or_create_lastset,
    abhebe_envelope_pro_bauelement,
)

def _validate_inputs(
    konstruktion,
    *,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst=None,  # bewusst ignoriert, aber Teil der Signatur
    reset_berechnungen: bool,
    methode: RechenmethodeAbheben,
    vereinfachung_konstruktion: VereinfachungKonstruktion,
    anzahl_windrichtungen: int,
) -> None:
    # konstruktion: hat bauelemente?
    if not hasattr(konstruktion, "bauelemente"):
        raise AttributeError("konstruktion muss ein Attribut 'bauelemente' besitzen.")
    if not isinstance(konstruktion.bauelemente, (list, tuple)) or len(konstruktion.bauelemente) == 0:
        raise ValueError("'bauelemente' muss eine nicht-leere Liste/Tuple sein.")

    # norm: vom Typ Norm und existent
    if not isinstance(norm, Norm):
        raise TypeError("norm muss vom Typ Norm sein.")

    # staudruecke: Sequence mit mind. 1 Eintrag
    if not isinstance(staudruecke, _SeqABC) or len(staudruecke) == 0:
        raise TypeError("staudruecke muss eine nicht-leere Sequence sein.")

    # obergrenzen: gleiche Länge wie staudruecke
    if not isinstance(obergrenzen, _SeqABC):
        raise TypeError("obergrenzen muss eine Sequence sein.")
    if len(obergrenzen) != len(staudruecke):
        raise ValueError("obergrenzen muss die gleiche Länge wie staudruecke haben.")

    # reset_berechnungen: bool?
    if not isinstance(reset_berechnungen, bool):
        raise TypeError("reset_berechnungen muss vom Typ bool sein.")

    # methode: RechenmethodeAbheben und existent
    if not isinstance(methode, RechenmethodeAbheben):
        raise TypeError("methode muss vom Typ RechenmethodeAbheben sein.")

    # vereinfachung_konstruktion: VereinfachungKonstruktion und existent
    if not isinstance(vereinfachung_konstruktion, VereinfachungKonstruktion):
        raise TypeError("vereinfachung_konstruktion muss vom Typ VereinfachungKonstruktion sein.")

    # anzahl_windrichtungen: int >= 1?
    if not isinstance(anzahl_windrichtungen, int) or anzahl_windrichtungen < 1:
        raise ValueError("anzahl_windrichtungen muss ein int ≥ 1 sein.")

def _abhebesicherheit_DinEn13814_2005_06(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeAbheben = RechenmethodeAbheben.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "_abhebesicherheit",
        "norm": "DIN_EN_13814_2005_06",
        "methode": methode.name,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEB/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeAbheben.STANDARD:
        pool = obtain_pool(konstruktion, reset_berechnungen, protokoll=protokoll, kontext=base_ctx)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, kontext=base_ctx)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, kontext=base_ctx):
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
                protokoll=protokoll,
                kontext=base_ctx,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_normal_down = 0.0
            total_normal_up = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                N_down_b, N_up_b = abhebe_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=protokoll, kontext=base_ctx)
                total_normal_down += N_down_b
                total_normal_up += N_up_b

            sicherheit = inf if total_normal_up <= _EPS else (total_normal_down / total_normal_up)
            if sicherheit < sicherheit_min_global:
                sicherheit_min_global = sicherheit

            if total_normal_up <= _EPS:
                ballastkraft = 0.0
            else:
                ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
            
            if ballastkraft > ballast_erforderlich_max:
                ballast_erforderlich_max = ballastkraft
            
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung  # in N -> in kg

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Abhebesicherheit S",
                wert=sicherheit_min_global,
                formel="S = ΣN_down / ΣN_up",
                formelzeichen=["N_down", "N_up"],
                quelle_formel="---",
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher zusätzlicher Ballast ΔN_down",
                wert=ballast_kg,
                formel="ΔN_down = max(0, ΣN_up − ΣN_down) / γ_g",
                formelzeichen=["N_up", "N_down", "γ_g"],
                quelle_formel="---",
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global),
                Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEB/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

def _abhebesicherheit_DinEn17879_2024_08(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeAbheben = RechenmethodeAbheben.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "_abhebesicherheit",
        "norm": "DIN_EN_13814_2005_06",
        "methode": methode.name,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEB/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeAbheben.STANDARD:
        pool = obtain_pool(konstruktion, reset_berechnungen, protokoll=protokoll, kontext=base_ctx)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, kontext=base_ctx)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, kontext=base_ctx):
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
                protokoll=protokoll,
                kontext=base_ctx,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_normal_down = 0.0
            total_normal_up = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                N_down_b, N_up_b = abhebe_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=protokoll, kontext=base_ctx)
                total_normal_down += N_down_b
                total_normal_up += N_up_b

            sicherheit = inf if total_normal_up <= _EPS else (total_normal_down / total_normal_up)
            if sicherheit < sicherheit_min_global:
                sicherheit_min_global = sicherheit

            if total_normal_up <= _EPS:
                ballastkraft = 0.0
            else:
                ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
            
            if ballastkraft > ballast_erforderlich_max:
                ballast_erforderlich_max = ballastkraft
            
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung  # in N -> in kg

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Abhebesicherheit S",
                wert=sicherheit_min_global,
                formel="S = ΣN_down / ΣN_up",
                formelzeichen=["N_down", "N_up"],
                quelle_formel="---",
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher zusätzlicher Ballast ΔN_down",
                wert=ballast_kg,
                formel="ΔN_down = max(0, ΣN_up − ΣN_down) / γ_g",
                formelzeichen=["N_up", "N_down", "γ_g"],
                quelle_formel="---",
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global),
                Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEB/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

# --- Dispatch ---------------------------------------------------------------

_DISPATCH: Dict[Norm, Callable[..., List[Zwischenergebnis]]] = {
    Norm.DEFAULT: _abhebesicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_13814_2005_06: _abhebesicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_17879_2024_08: _abhebesicherheit_DinEn17879_2024_08,
}

# --- Öffentliche API --------------------------------------------------------

def abhebesicherheit(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeAbheben = RechenmethodeAbheben.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "abhebesicherheit",
        "norm": getattr(norm, "name", str(norm)),
        "anzahl_windrichtungen": anzahl_windrichtungen,
    })
    """
    Norm-dispatchte Abhebe-Sicherheitsbewertung.
    Gibt ein Zwischenergebnis mit der minimalen Sicherheit über alle Windrichtungen zurück.
    """
    try:
        _validate_inputs(
            konstruktion,
            norm=norm,
            staudruecke=staudruecke,
            obergrenzen=obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
        )
    except Exception as e:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEB/INPUT_INVALID",
            text=str(e), kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        konstruktion,
        norm,
        staudruecke,
        obergrenzen,
        konst=konst,
        reset_berechnungen=reset_berechnungen,
        methode=methode,
        vereinfachung_konstruktion=vereinfachung_konstruktion,
        anzahl_windrichtungen=anzahl_windrichtungen,
        protokoll=protokoll,
        kontext=base_ctx,
    )
