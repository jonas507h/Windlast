# rechenfunktionen/gleitsicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional
from collections.abc import Sequence as _SeqABC

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.datenstruktur.enums import Norm, RechenmethodeGleiten, VereinfachungKonstruktion, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.konstanten import _EPS, aktuelle_konstanten
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from windlast_CORE.datenstruktur.kraefte import Kraefte

from windlast_CORE.rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    obtain_pool,
    get_or_create_lastset,
    ermittle_min_reibwert,
    gleit_envelope_pro_bauelement,
)
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektoren_addieren, vektor_laenge

def _validate_inputs(
    konstruktion,
    *,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst=None,  # bewusst ignoriert, aber Teil der Signatur
    reset_berechnungen: bool,
    methode: RechenmethodeGleiten,
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

    # methode: RechenmethodeGleiten und existent
    if not isinstance(methode, RechenmethodeGleiten):
        raise TypeError("methode muss vom Typ RechenmethodeGleiten sein.")

    # vereinfachung_konstruktion: VereinfachungKonstruktion und existent
    if not isinstance(vereinfachung_konstruktion, VereinfachungKonstruktion):
        raise TypeError("vereinfachung_konstruktion muss vom Typ VereinfachungKonstruktion sein.")

    # anzahl_windrichtungen: int >= 1?
    if not isinstance(anzahl_windrichtungen, int) or anzahl_windrichtungen < 1:
        raise ValueError("anzahl_windrichtungen muss ein int ≥ 1 sein.")
    
def _gleitsicherheit_DinEn13814_2005_06(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "gleitsicherheit_DinEn13814_2005_06",
    }

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(norm,konstruktion, protokoll=protokoll, breadcrumb=base_bc)

        protokolliere_ergebnis(
            protokoll,
            breadcrumb = base_bc,
            name="min_reibwert",
            wert=reibwert_min,
            label="Minimaler Reibwert μ_min",
            formelzeichen="μ_min",
            formel="μ_min = min(μ_Bauelemente)",
            meta=base_meta,
        )

        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, breadcrumb=base_bc)
        pool = obtain_pool(konstruktion, reset_berechnungen)
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
                breadcrumb=richtung_bc
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf
            dir_ballast_max = 0.0

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for element, lastfaelle_elem in kraefte_nach_element.items():
                element_bc = merge_breadcrumb(richtung_bc, [bc_step("element_id", str(element), ebene_label="Bauelement")])
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=protokoll, breadcrumb=element_bc)
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="horizontalkraft",
                    wert=H_vec,
                    label="Horizontalkraft H",
                    formelzeichen="H",
                    einheit="N",
                    priority=10,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="normalkraft_down",
                    wert=N_down,
                    label="Normalkraft N_down",
                    formelzeichen="N_down",
                    einheit="N",
                    priority=10,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="normalkraft_up",
                    wert=N_up,
                    label="Normalkraft N_up",
                    formelzeichen="N_up",
                    einheit="N",
                    priority=10,
                    meta=base_meta,
                )
                total_horizontal = vektoren_addieren([total_horizontal, H_vec])
                total_normal_up += N_up
                total_normal_down += N_down

            horizontal_betrag = vektor_laenge(total_horizontal)
            normal_effektiv = max(0.0, total_normal_down - total_normal_up)
            reibkraft = reibwert_min * normal_effektiv

            # === Zwischendocs (Aggregat der Richtung) ===
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="horizontal_betrag",
                wert=horizontal_betrag,
                label="Summe Horizontalbetrag |H|",
                formelzeichen="|H|",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="normal_down",
                wert=total_normal_down,
                label="Summe Normalkräfte ΣN_down",
                formelzeichen="ΣN_down",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="normal_up",
                wert=total_normal_up,
                label="Summe Normalkräfte ΣN_up",
                formelzeichen="ΣN_up",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="normal_effektiv",
                wert=normal_effektiv,
                label="Effektive Normalkraft N_eff",
                formelzeichen="N_eff",
                formel="N_eff = max(0, ΣN_down − ΣN_up)",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="reibkraft",
                wert=reibkraft,
                label="Reibkraft R",
                formelzeichen="R",
                formel="R = μ_min · N_eff",
                einheit="N",
                priority=7,
                meta=base_meta,
            )

            if horizontal_betrag > _EPS:
                sicherheit = reibkraft / horizontal_betrag
                dir_min_sicherheit = min(dir_min_sicherheit, sicherheit)
                
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_sicherheit_gleit",
                wert=sicherheit,
                label=f"Richtungs-Sicherheit S_gleit,{int(winkel)}°",
                formelzeichen=f"S_gleit,{int(winkel)}°",
                priority=10,
                meta=base_meta,
            )

            if reibwert_min <= _EPS:
                if horizontal_betrag > _EPS:
                    ballastkraft = inf
                else:
                    # ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
                    ballastkraft = 0.0
            else:
                ballastkraft = max(0.0, horizontal_betrag / reibwert_min + total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert

            if ballastkraft > dir_ballast_max:
                dir_ballast_max = ballastkraft

            # Ballast-Doc (Richtung)
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_ballast_gleit",
                wert=ballastkraft,
                label=f"Richtungs-Ballast m_Ballast,gleit,{int(winkel)}°",
                formelzeichen=f"m_Ballast,gleit,{int(winkel)}°",
                einheit="N",
                priority=10,
                meta=base_meta,
            )

            # Record ablegen (WICHTIG: innerhalb der Schleife!)
            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
            })

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", winner["windrichtung_deg"])]))

        sicherheit_min_global = dir_records[winner_idx]["dir_min_sicherheit"]
        ballast_erforderlich_max = dir_records[winner_idx]["dir_ballast_max"]

        # Endwerte (relevant)
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="sicherheit_gleit",
            wert=sicherheit_min_global,
            label="Gleitsicherheit S_gleit",
            formelzeichen="S_gleit",
            priority=10,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="ballast_gleit",
            wert=ballast_kg,
            label="Erforderlicher Ballast m_Ballast,gleit",
            formelzeichen="m_Ballast,gleit",
            einheit="kg",
            priority=10,
            meta=base_meta,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

def _gleitsicherheit_DinEn17879_2024_08(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "gleitsicherheit_DinEn17879_2024_08",
    }

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(norm,konstruktion, protokoll=protokoll, breadcrumb=base_bc)

        protokolliere_ergebnis(
            protokoll,
            breadcrumb = base_bc,
            name="min_reibwert",
            wert=reibwert_min,
            label="Minimaler Reibwert μ_min",
            formelzeichen="μ_min",
            formel="μ_min = min(μ_Bauelemente)",
            meta=base_meta,
        )

        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, breadcrumb=base_bc)
        pool = obtain_pool(konstruktion, reset_berechnungen)
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
                breadcrumb=richtung_bc
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf
            dir_ballast_max = 0.0

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for element, lastfaelle_elem in kraefte_nach_element.items():
                element_bc = merge_breadcrumb(richtung_bc, [bc_step("element_id", str(element), ebene_label="Bauelement")])
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=protokoll, breadcrumb=element_bc)
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="horizontalkraft",
                    wert=H_vec,
                    label="Horizontalkraft H",
                    formelzeichen="H",
                    einheit="N",
                    priority=10,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="normalkraft_down",
                    wert=N_down,
                    label="Normalkraft N_down",
                    formelzeichen="N_down",
                    einheit="N",
                    priority=10,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=element_bc,
                    name="normalkraft_up",
                    wert=N_up,
                    label="Normalkraft N_up",
                    formelzeichen="N_up",
                    einheit="N",
                    priority=10,
                    meta=base_meta,
                )
                total_horizontal = vektoren_addieren([total_horizontal, H_vec])
                total_normal_up += N_up
                total_normal_down += N_down

            horizontal_betrag = vektor_laenge(total_horizontal)
            normal_effektiv = max(0.0, total_normal_down - total_normal_up)
            reibkraft = reibwert_min * normal_effektiv

            # === Zwischendocs (Aggregat der Richtung) ===
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="horizontal_betrag",
                wert=horizontal_betrag,
                label="Summe Horizontalbetrag |H|",
                formelzeichen="|H|",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="normal_down",
                wert=total_normal_down,
                label="Summe Normalkräfte ΣN_down",
                formelzeichen="ΣN_down",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="normal_up",
                wert=total_normal_up,
                label="Summe Normalkräfte ΣN_up",
                formelzeichen="ΣN_up",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="normal_effektiv",
                wert=normal_effektiv,
                label="Effektive Normalkraft N_eff",
                formelzeichen="N_eff",
                formel="N_eff = max(0, ΣN_down − ΣN_up)",
                einheit="N",
                priority=7,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="reibkraft",
                wert=reibkraft,
                label="Reibkraft R",
                formelzeichen="R",
                formel="R = μ_min · N_eff",
                einheit="N",
                priority=7,
                meta=base_meta,
            )

            if horizontal_betrag > _EPS:
                sicherheit = reibkraft / horizontal_betrag
                dir_min_sicherheit = min(dir_min_sicherheit, sicherheit)
                
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_sicherheit_gleit",
                wert=sicherheit,
                label=f"Richtungs-Sicherheit S_gleit,{int(winkel)}°",
                formelzeichen=f"S_gleit,{int(winkel)}°",
                priority=10,
                meta=base_meta,
            )

            if reibwert_min <= _EPS:
                if horizontal_betrag > _EPS:
                    ballastkraft = inf
                else:
                    # ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
                    ballastkraft = 0.0
            else:
                ballastkraft = max(0.0, horizontal_betrag / reibwert_min + total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert

            if ballastkraft > dir_ballast_max:
                dir_ballast_max = ballastkraft

            # Ballast-Doc (Richtung)
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_ballast_gleit",
                wert=ballastkraft,
                label=f"Richtungs-Ballast m_Ballast,gleit,{int(winkel)}°",
                formelzeichen=f"m_Ballast,gleit,{int(winkel)}°",
                einheit="N",
                priority=10,
                meta=base_meta,
            )

            # Record ablegen (WICHTIG: innerhalb der Schleife!)
            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
            })

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", winner["windrichtung_deg"])]))

        sicherheit_min_global = dir_records[winner_idx]["dir_min_sicherheit"]
        ballast_erforderlich_max = dir_records[winner_idx]["dir_ballast_max"]

        # Endwerte (relevant)
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="sicherheit_gleit",
            wert=sicherheit_min_global,
            label="Gleitsicherheit S_gleit",
            formelzeichen="S_gleit",
            priority=10,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="ballast_gleit",
            wert=ballast_kg,
            label="Erforderlicher Ballast m_Ballast,gleit",
            formelzeichen="m_Ballast,gleit",
            einheit="kg",
            priority=10,
            meta=base_meta,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
_DISPATCH: Dict[Norm, Callable[..., List[Zwischenergebnis]]] = {
    Norm.DEFAULT: _gleitsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_13814_2005_06: _gleitsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_17879_2024_08: _gleitsicherheit_DinEn17879_2024_08,
}

def gleitsicherheit(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "gleitsicherheit",
    }

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
            protokoll, severity=Severity.ERROR, code="GLEIT/INPUT_INVALID",
            text=str(e), breadcrumb=base_bc, meta=base_meta,
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
    