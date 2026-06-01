# rechenfunktionen/kippsicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional, Tuple, Iterable
from collections.abc import Sequence as _SeqABC

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.datenstruktur.enums import Norm, RechenmethodeKippen, VereinfachungKonstruktion, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.konstanten import _EPS, aktuelle_konstanten
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from windlast_CORE.rechenfunktionen.geom3d import flaechenschwerpunkt, moment_einzelkraft_um_achse

from windlast_CORE.rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    sammle_kippachsen,
    obtain_pool,
    get_or_create_lastset,
    kipp_envelope_pro_bauelement,
)

def _validate_inputs(
    konstruktion,
    *,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst=None,  # bewusst ignoriert, aber Teil der Signatur
    reset_berechnungen: bool,
    methode: RechenmethodeKippen,
    vereinfachung_konstruktion: VereinfachungKonstruktion,
    anzahl_windrichtungen: int,
) -> None:
    # konstruktion: hat bauelemente?
    if not hasattr(konstruktion, "bauelemente"):
        raise AttributeError("konstruktion muss ein Attribut 'bauelemente' besitzen.")
    if not isinstance(konstruktion.bauelemente, (list, tuple)) or len(konstruktion.bauelemente) == 0:
        raise ValueError("'bauelemente' muss eine nicht-leere Liste/Tuple sein.")

    # norm: vom Typ Norm und existent (Existenz = gültiges Enum-Mitglied)
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

    # methode: RechenmethodeKippen und existent (Existenz = gültiges Enum-Mitglied)
    if not isinstance(methode, RechenmethodeKippen):
        raise TypeError("methode muss vom Typ RechenmethodeKippen sein.")

    # vereinfachung_konstruktion: VereinfachungKonstruktion und existent
    if not isinstance(vereinfachung_konstruktion, VereinfachungKonstruktion):
        raise TypeError("vereinfachung_konstruktion muss vom Typ VereinfachungKonstruktion sein.")

    # anzahl_windrichtungen: int >= 1?
    if not isinstance(anzahl_windrichtungen, int) or anzahl_windrichtungen < 1:
        raise ValueError("anzahl_windrichtungen muss ein int ≥ 1 sein.")

def _kippsicherheit_DinEn13814_2005_06(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = True,
    methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
    loads_breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "kippsicherheit_DinEn13814_2005_06",
    }
    loads_bc = loads_breadcrumb if loads_breadcrumb is not None else base_bc

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion, protokoll=protokoll, breadcrumb=base_bc)
        if not achsen:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
        # 1.1) Grundgrößen für Ballast bestimmen
        ballastkraft_dummy = Kraefte(
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=[(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True)
        huelle_punkte = [a.punkt for a in achsen]
        schwerpunkt_ballast = flaechenschwerpunkt(huelle_punkte)

        # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0

        pool = obtain_pool(konstruktion, reset_berechnungen)
        dir_records = []  # (winkel, richtung, min_sicherheit, ballast_max)

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
                breadcrumb=loads_bc,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf
            dir_ballast_max = 0.0 
            best_achse_idx = None
            achse_idx = -1

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                achse_idx += 1
                total_kipp = 0.0
                total_stand = 0.0

                achse_bc = merge_breadcrumb(richtung_bc, [bc_step("achse_index", str(achse_idx), ebene_label="Kippachse")])

                for element, lastfaelle_elem in kraefte_nach_element.items():
                    element_bc = merge_breadcrumb(achse_bc, [bc_step("element_id", str(element), ebene_label="Bauelement")])
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem, protokoll=protokoll, breadcrumb=element_bc)
                    protokolliere_ergebnis(
                        protokoll,
                        breadcrumb=element_bc,
                        name="element_kippmoment",
                        wert=kipp_b,
                        label="math.kipp_kippmoment_element.label",
                        formelzeichen="math.kipp_kippmoment_element.symbol",
                        formel="math.kipp_kippmoment_element.formula",
                        einheit="Nm",
                        priority=60,
                        meta=base_meta,
                    )
                    protokolliere_ergebnis(
                        protokoll,
                        breadcrumb=element_bc,
                        name="element_standmoment",
                        wert=stand_b,
                        label="math.kipp_standmoment_element.label",
                        formelzeichen="math.kipp_standmoment_element.symbol",
                        formel="math.kipp_standmoment_element.formula",
                        einheit="Nm",
                        priority=60,
                        meta=base_meta,
                    )
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_kippmoment",
                    wert=total_kipp,
                    label="math.kipp_kippmoment_achse.label",
                    formelzeichen="math.kipp_kippmoment_achse.symbol",
                    formel="math.kipp_kippmoment_achse.formula",
                    einheit="Nm",
                    priority=65,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_standmoment",
                    wert=total_stand,
                    label="math.kipp_standmoment_achse.label",
                    formelzeichen="math.kipp_standmoment_achse.symbol",
                    formel="math.kipp_standmoment_achse.formula",
                    einheit="Nm",
                    priority=65,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_sicherheit_kipp",
                    wert=sicherheit,
                    label="math.kipp_sicherheit_achse.label",
                    formelzeichen="math.kipp_sicherheit_achse.symbol",
                    formel="math.kipp_sicherheit_achse.formula",
                    priority=65,
                    meta=base_meta,
                )

                if sicherheit < dir_min_sicherheit:
                    dir_min_sicherheit = sicherheit
                    best_achse_idx = achse_idx

                moment_defizit = max(0.0, total_kipp - total_stand)

                if moment_defizit > _EPS:
                    ballast_kippmoment_einheit = moment_einzelkraft_um_achse(
                        achse,
                        (0.0, 0.0, -1.0),  # Einheitliche Abwärtskraft
                        schwerpunkt_ballast,
                    )
                    ballast_standmoment_proN = max(0.0, -ballast_kippmoment_einheit)

                    if ballast_standmoment_proN <= _EPS:
                        ballastkraft = inf  # kein Standsicherheitsbeitrag durch Ballast möglich     
                    else:
                        ballastkraft = moment_defizit / (ballast_standmoment_proN * sicherheitsbeiwert_ballast.wert)
                
                else:
                    ballastkraft = 0.0

                if ballastkraft > dir_ballast_max:
                    dir_ballast_max = ballastkraft

                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_ballastkraft_kipp",
                    wert=ballastkraft,
                    label="math.kipp_ballast_achse.label",
                    formelzeichen="math.kipp_ballast_achse.symbol",
                    formel="math.kipp_ballast_achse.formula",
                    einheit="N",
                    priority=65,
                    meta=base_meta,
                )

            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_sicherheit_kipp",
                wert=dir_min_sicherheit,
                label="math.kipp_sicherheit_richtung.label",
                formelzeichen="math.kipp_sicherheit_richtung.symbol",
                formel="math.kipp_sicherheit_richtung.formula",
                priority=70,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_ballast_kipp",
                wert=dir_ballast_max,
                label="math.kipp_ballast_richtung.label",
                formelzeichen="math.kipp_ballast_richtung.symbol",
                formel="math.kipp_ballast_richtung.formula",
                einheit="N",
                priority=70,
                meta=base_meta,
            )

            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
                "best_achse_idx": best_achse_idx,
            })

            set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", f"{winkel}°")]))

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            # defensive: nichts gerechnet → Exit wie bisher
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        # 1) Gewinner-Richtung finden (minimale Sicherheit)
        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]

        # 4) Globale Ergebnis-Docs (beste Richtung) kennzeichnen
        sicherheit_min_global = winner["dir_min_sicherheit"]
        ballast_erforderlich_max = winner["dir_ballast_max"]
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="sicherheit_kipp",
            wert=sicherheit_min_global,
            label="math.kipp_sicherheit.label",
            formelzeichen="math.kipp_sicherheit.symbol",
            formel="math.kipp_sicherheit.formula",
            priority=100,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="ballast_kipp",
            wert=ballast_kg,
            label="math.kipp_ballast.label",
            formelzeichen="math.kipp_ballast.symbol",
            einheit="kg",
            formel="math.kipp_ballast.formula",
            priority=90,
            meta=base_meta,
        )

        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", winner["windrichtung_deg"])]))

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        # (andere Methoden:)
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
def _kippsicherheit_DinEn17879_2024_08(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = True,
    methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
    loads_breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "kippsicherheit_DinEn17879_2024_08",
    }
    loads_bc = loads_breadcrumb if loads_breadcrumb is not None else base_bc

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion, protokoll=protokoll, breadcrumb=base_bc)
        if not achsen:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
        # 1.1) Grundgrößen für Ballast bestimmen
        ballastkraft_dummy = Kraefte(
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=[(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True)
        huelle_punkte = [a.punkt for a in achsen]
        schwerpunkt_ballast = flaechenschwerpunkt(huelle_punkte)

        # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0

        pool = obtain_pool(konstruktion, reset_berechnungen)
        dir_records = []  # (winkel, richtung, min_sicherheit, ballast_max)

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
                breadcrumb=loads_bc,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf
            dir_ballast_max = 0.0 
            best_achse_idx = None
            achse_idx = -1

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                achse_idx += 1
                total_kipp = 0.0
                total_stand = 0.0

                achse_bc = merge_breadcrumb(richtung_bc, [bc_step("achse_index", str(achse_idx), ebene_label="Kippachse")])

                for element, lastfaelle_elem in kraefte_nach_element.items():
                    element_bc = merge_breadcrumb(achse_bc, [bc_step("element_id", str(element), ebene_label="Bauelement")])
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem, protokoll=protokoll, breadcrumb=element_bc)
                    protokolliere_ergebnis(
                        protokoll,
                        breadcrumb=element_bc,
                        name="element_kippmoment",
                        wert=kipp_b,
                        label="math.kipp_kippmoment_element.label",
                        formelzeichen="math.kipp_kippmoment_element.symbol",
                        formel="math.kipp_kippmoment_element.formula",
                        einheit="Nm",
                        priority=60,
                        meta=base_meta,
                    )
                    protokolliere_ergebnis(
                        protokoll,
                        breadcrumb=element_bc,
                        name="element_standmoment",
                        wert=stand_b,
                        label="math.kipp_standmoment_element.label",
                        formelzeichen="math.kipp_standmoment_element.symbol",
                        formel="math.kipp_standmoment_element.formula",
                        einheit="Nm",
                        priority=60,
                        meta=base_meta,
                    )
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_kippmoment",
                    wert=total_kipp,
                    label="math.kipp_kippmoment_achse.label",
                    formelzeichen="math.kipp_kippmoment_achse.symbol",
                    formel="math.kipp_kippmoment_achse.formula",
                    einheit="Nm",
                    priority=65,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_standmoment",
                    wert=total_stand,
                    label="math.kipp_standmoment_achse.label",
                    formelzeichen="math.kipp_standmoment_achse.symbol",
                    formel="math.kipp_standmoment_achse.formula",
                    einheit="Nm",
                    priority=65,
                    meta=base_meta,
                )
                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_sicherheit_kipp",
                    wert=sicherheit,
                    label="math.kipp_sicherheit_achse.label",
                    formelzeichen="math.kipp_sicherheit_achse.symbol",
                    formel="math.kipp_sicherheit_achse.formula",
                    priority=65,
                    meta=base_meta,
                )

                if sicherheit < dir_min_sicherheit:
                    dir_min_sicherheit = sicherheit
                    best_achse_idx = achse_idx

                moment_defizit = max(0.0, total_kipp - total_stand)

                if moment_defizit > _EPS:
                    ballast_kippmoment_einheit = moment_einzelkraft_um_achse(
                        achse,
                        (0.0, 0.0, -1.0),  # Einheitliche Abwärtskraft
                        schwerpunkt_ballast,
                    )
                    ballast_standmoment_proN = max(0.0, -ballast_kippmoment_einheit)

                    if ballast_standmoment_proN <= _EPS:
                        ballastkraft = inf  # kein Standsicherheitsbeitrag durch Ballast möglich     
                    else:
                        ballastkraft = moment_defizit / (ballast_standmoment_proN * sicherheitsbeiwert_ballast.wert)
                
                else:
                    ballastkraft = 0.0

                if ballastkraft > dir_ballast_max:
                    dir_ballast_max = ballastkraft

                protokolliere_ergebnis(
                    protokoll,
                    breadcrumb=achse_bc,
                    name="achse_ballastkraft_kipp",
                    wert=ballastkraft,
                    label="math.kipp_ballast_achse.label",
                    formelzeichen="math.kipp_ballast_achse.symbol",
                    formel="math.kipp_ballast_achse.formula",
                    einheit="N",
                    priority=65,
                    meta=base_meta,
                )

            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_sicherheit_kipp",
                wert=dir_min_sicherheit,
                label="math.kipp_sicherheit_richtung.label",
                formelzeichen="math.kipp_sicherheit_richtung.symbol",
                formel="math.kipp_sicherheit_richtung.formula",
                priority=70,
                meta=base_meta,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=richtung_bc,
                name="richtung_ballast_kipp",
                wert=dir_ballast_max / aktuelle_konstanten().erdbeschleunigung,
                label="math.kipp_ballast_richtung.label",
                formelzeichen="math.kipp_ballast_richtung.symbol",
                formel="math.kipp_ballast_richtung.formula",
                einheit="kg",
                priority=70,
                meta=base_meta,
            )

            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
                "best_achse_idx": best_achse_idx,
            })

            set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", f"{winkel}°")]))

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            # defensive: nichts gerechnet → Exit wie bisher
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        # 1) Gewinner-Richtung finden (minimale Sicherheit)
        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]

        # 4) Globale Ergebnis-Docs (beste Richtung) kennzeichnen
        sicherheit_min_global = winner["dir_min_sicherheit"]
        ballast_erforderlich_max = winner["dir_ballast_max"]
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="sicherheit_kipp",
            wert=sicherheit_min_global,
            label="math.kipp_sicherheit.label",
            formelzeichen="math.kipp_sicherheit.symbol",
            formel="math.kipp_sicherheit.formula",
            priority=100,
            meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="ballast_kipp",
            wert=ballast_kg,
            label="math.kipp_ballast.label",
            formelzeichen="math.kipp_ballast.symbol",
            einheit="kg",
            formel="math.kipp_ballast.formula",
            priority=90,
            meta=base_meta,
        )

        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("windrichtung_deg", winner["windrichtung_deg"])]))

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        # (andere Methoden:)
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
_DISPATCH: Dict[Norm, Callable[..., List[Zwischenergebnis]]] = {
    Norm.DEFAULT: _kippsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_13814_2005_06: _kippsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_17879_2024_08: _kippsicherheit_DinEn17879_2024_08,
}

def kippsicherheit(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = True,
    methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
    loads_breadcrumb: Optional[list] = None,
) -> List[Zwischenergebnis]:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "kippsicherheit",
    }
    """
    Norm-dispatchte Kipp-Sicherheitsbewertung.
    Gibt ein Zwischenergebnis mit der minimalen Sicherheit über alle Windrichtungen/Achsen zurück.
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
            protokoll, severity=Severity.ERROR,
            code="KIPP/INPUT_INVALID",
            text=str(e),
            breadcrumb=base_bc,
            meta=base_meta,
        )
        # NaN-Placeholder zurück (wie vereinbart: Zwischenergebnis nur mit wert)
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
        loads_breadcrumb=loads_breadcrumb,
    )