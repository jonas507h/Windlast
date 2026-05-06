# rechenfunktionen/abhebesicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional
from collections.abc import Sequence as _SeqABC

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.datenstruktur.enums import Norm, RechenmethodeAbheben, VereinfachungKonstruktion, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.konstanten import _EPS, aktuelle_konstanten
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert

from windlast_CORE.rechenfunktionen.standsicherheit_utils import (
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
    breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEBE/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeAbheben.STANDARD:
        pool = obtain_pool(konstruktion, reset_berechnungen, protokoll=protokoll, breadcrumb=base_bc)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, breadcrumb=base_bc)
        dir_records = []

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, breadcrumb=base_bc):
            richtung_bc = merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", f"{winkel}°", ebene_label="Windrichtung")])
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
                kontext=richtung_bc
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_normal_down = 0.0
            total_normal_up = 0.0

            for element, lastfaelle_elem in kraefte_nach_element.items():
                element_bc = merge_breadcrumb(richtung_bc, [bc_step("element_id", str(element), ebene_label="Bauelement")])
                N_down_b, N_up_b = abhebe_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=protokoll, breadcrumb=element_bc)
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="element_normalkraft_down",
                    wert=N_down_b,
                    label=f"Normalkraft N_down",
                    einheit="N",
                    priority=10
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="element_normalkraft_up",
                    wert=N_up_b,
                    label=f"Normalkraft N_up",
                    einheit="N",
                    priority=10
                )
                total_normal_down += N_down_b
                total_normal_up += N_up_b

            # Richtungs-Aggregate dokumentieren
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="summe_normalkraft_down",
                wert=total_normal_down,
                label="Summe Normalkräfte ΣN_down",
                einheit="N",
                priority=7
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="summe_normalkraft_up",
                wert=total_normal_up,
                label="Summe Normalkräfte ΣN_up",
                einheit="N",
                priority=7
            )

            sicherheit = inf if total_normal_up <= _EPS else (total_normal_down / total_normal_up)
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_sicherheit_abheben",
                label=f"Richtungs-Sicherheit S_abheb,{int(winkel)}°",
                formelzeichen=f"S_abheb,{int(winkel)}°",
                wert=sicherheit,
                formel="S = ΣN_down / ΣN_up",
                priority=10,
            )

            if total_normal_up <= _EPS:
                ballastkraft = 0.0
            else:
                ballastkraft = max(0.0, (total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert)

            if ballastkraft > ballast_erforderlich_max:
                ballast_erforderlich_max = ballastkraft

            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_ballast_abheben",
                label=f"Richtungs-Ballast m_Ballast,abheb,{int(winkel)}°",
                formelzeichen=f"m_Ballast,abheb,{int(winkel)}°",
                wert=ballastkraft,
                einheit="N",
                formel="ΔN_down,erf = max(0, ΣN_up − ΣN_down) / γ_g",
                priority=10,
            )

            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": sicherheit,        # (hier ist S_dir für diese Richtung bereits die relevante Größe)
                "dir_ballast_max": ballastkraft,
            })
            
        if not dir_records:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", dir_records[winner_idx]["windrichtung_deg"])]))

        sicherheit_min_global = winner["dir_min_sicherheit"]
        ballast_erforderlich_max = max(r["dir_ballast_max"] for r in dir_records)

        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        # Endwerte
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="abhebesicherheit",
            label="Abhebesicherheit",
            formelzeichen="S_abhebe",
            wert=sicherheit_min_global,
            formel="S_abhebe = ΣN_down / ΣN_up",
            priority=10,
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="ballast_abhebe",
            label="Erforderlicher Ballast aus Abheben",
            formelzeichen="m_Ballast,abhebe",
            wert=ballast_kg,
            einheit="kg",
            formel="m_Ballast,abhebe = max(0, ΣN_up − ΣN_down) / γ_g",
            priority=10,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEBE/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            breadcrumb=base_bc,
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
    breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEBE/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeAbheben.STANDARD:
        pool = obtain_pool(konstruktion, reset_berechnungen, protokoll=protokoll, breadcrumb=base_bc)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, breadcrumb=base_bc)
        dir_records = []

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, breadcrumb=base_bc):
            richtung_bc = merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", f"{winkel}°", ebene_label="Windrichtung")])
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
                kontext=richtung_bc
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_normal_down = 0.0
            total_normal_up = 0.0

            for element, lastfaelle_elem in kraefte_nach_element.items():
                element_bc = merge_breadcrumb(richtung_bc, [bc_step("element_id", str(element), ebene_label="Bauelement")])
                N_down_b, N_up_b = abhebe_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=protokoll, breadcrumb=element_bc)
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="element_normalkraft_down",
                    wert=N_down_b,
                    label=f"Normalkraft N_down",
                    einheit="N",
                    priority=10
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="element_normalkraft_up",
                    wert=N_up_b,
                    label=f"Normalkraft N_up",
                    einheit="N",
                    priority=10
                )
                total_normal_down += N_down_b
                total_normal_up += N_up_b

            # Richtungs-Aggregate dokumentieren
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="summe_normalkraft_down",
                wert=total_normal_down,
                label="Summe Normalkräfte ΣN_down",
                einheit="N",
                priority=7
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="summe_normalkraft_up",
                wert=total_normal_up,
                label="Summe Normalkräfte ΣN_up",
                einheit="N",
                priority=7
            )

            sicherheit = inf if total_normal_up <= _EPS else (total_normal_down / total_normal_up)
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_sicherheit_abheben",
                label=f"Richtungs-Sicherheit S_abheb,{int(winkel)}°",
                formelzeichen=f"S_abheb,{int(winkel)}°",
                wert=sicherheit,
                formel="S = ΣN_down / ΣN_up",
                priority=10,
            )

            if total_normal_up <= _EPS:
                ballastkraft = 0.0
            else:
                ballastkraft = max(0.0, (total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert)

            if ballastkraft > ballast_erforderlich_max:
                ballast_erforderlich_max = ballastkraft

            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_ballast_abheben",
                label=f"Richtungs-Ballast m_Ballast,abheb,{int(winkel)}°",
                formelzeichen=f"m_Ballast,abheb,{int(winkel)}°",
                wert=ballastkraft,
                einheit="N",
                formel="ΔN_down,erf = max(0, ΣN_up − ΣN_down) / γ_g",
                priority=10,
            )

            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": sicherheit,        # (hier ist S_dir für diese Richtung bereits die relevante Größe)
                "dir_ballast_max": ballastkraft,
            })
            
        if not dir_records:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", dir_records[winner_idx]["windrichtung_deg"])]))

        sicherheit_min_global = winner["dir_min_sicherheit"]
        ballast_erforderlich_max = max(r["dir_ballast_max"] for r in dir_records)

        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        # Endwerte
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="abhebesicherheit",
            label="Abhebesicherheit",
            formelzeichen="S_abhebe",
            wert=sicherheit_min_global,
            formel="S_abhebe = ΣN_down / ΣN_up",
            priority=10,
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="ballast_abhebe",
            label="Erforderlicher Ballast aus Abheben",
            formelzeichen="m_Ballast,abhebe",
            wert=ballast_kg,
            einheit="kg",
            formel="m_Ballast,abhebe = max(0, ΣN_up − ΣN_down) / γ_g",
            priority=10,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="ABHEBE/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            breadcrumb=base_bc,
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
    breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = merge_breadcrumb(breadcrumb, [bc_step("nachweis", "ABHEBE")])
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
            protokoll, severity=Severity.ERROR, code="ABHEBE/INPUT_INVALID",
            text=str(e), breadcrumb=base_bc,
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
        breadcrumb=base_bc,
    )
