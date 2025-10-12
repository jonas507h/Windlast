# rechenfunktionen/kippsicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional, Tuple, Iterable
from collections.abc import Sequence as _SeqABC

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_kontext, protokolliere_msg, protokolliere_doc, make_docbundle, merge_protokoll, make_protokoll
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
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "_kippsicherheit",
        "norm": "DIN_EN_13814_2005_06",
        "methode": methode.name,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion, protokoll=protokoll, kontext=base_ctx)
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

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, kontext=base_ctx):
            sub_prot = make_protokoll()
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
                protokoll=sub_prot,
                kontext=base_ctx,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf
            dir_ballast_max = 0.0 

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                total_kipp = 0.0
                total_stand = 0.0

                for _, lastfaelle_elem in kraefte_nach_element.items():
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem, protokoll=sub_prot, kontext=base_ctx)
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                if sicherheit < dir_min_sicherheit:
                    dir_min_sicherheit = sicherheit

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

        # >>> Nach Abschluss der Achsen: Entscheidung & Merge
        if dir_min_sicherheit < sicherheit_min_global:
            # Gewinner-Richtung: komplettes Sub-Protokoll übernehmen
            merge_protokoll(sub_prot, protokoll, only_errors=False)
            sicherheit_min_global = dir_min_sicherheit
            if dir_ballast_max > ballast_erforderlich_max:
                ballast_erforderlich_max = dir_ballast_max
        else:
            # Verworfen: nur Fehler übernehmen
            merge_protokoll(sub_prot, protokoll, only_errors=True)

        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kippsicherheit S",
                wert=sicherheit_min_global,
                formel="S = ΣM_stand / ΣM_kipp",
                quelle_formel="---",
                formelzeichen=["M_stand", "M_kipp"],
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher Ballast ΔW",
                wert=ballast_kg,
                formel="ΔW = max(0, ΣM_kipp − ΣM_stand) / (γ_g · m_stand,1N)",
                quelle_formel="---",
                formelzeichen=["M_kipp", "M_stand", "γ_g", "m_stand,1N", "g"],
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        # (andere Methoden:)
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
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
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "_kippsicherheit",
        "norm": "DIN_EN_13814_2005_06",
        "methode": methode.name,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion)
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

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, kontext=base_ctx):
            sub_prot = make_protokoll()
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
                protokoll=sub_prot,
                kontext=base_ctx,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf           # <<< NEU: kleinstes S dieser Richtung
            dir_ballast_max = 0.0              # <<< NEU: größter Ballast dieser Richtung

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                total_kipp = 0.0
                total_stand = 0.0

                for _, lastfaelle_elem in kraefte_nach_element.items():
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem, protokoll=sub_prot, kontext=base_ctx)
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                # Richtungs-Minimum aktualisieren
                if sicherheit < dir_min_sicherheit:
                    dir_min_sicherheit = sicherheit

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

        # >>> Nach Abschluss der Achsen: Entscheidung & Merge
        if dir_min_sicherheit < sicherheit_min_global:
            # Gewinner-Richtung: komplettes Sub-Protokoll übernehmen
            merge_protokoll(sub_prot, protokoll, only_errors=False)
            sicherheit_min_global = dir_min_sicherheit
            if dir_ballast_max > ballast_erforderlich_max:
                ballast_erforderlich_max = dir_ballast_max
        else:
            # Verworfen: nur Fehler übernehmen
            merge_protokoll(sub_prot, protokoll, only_errors=True)

        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kippsicherheit S",
                wert=sicherheit_min_global,
                formel="S = ΣM_stand / ΣM_kipp",
                quelle_formel="---",
                formelzeichen=["M_stand", "M_kipp"],
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher Ballast ΔW",
                wert=ballast_kg,
                formel="ΔW = max(0, ΣM_kipp − ΣM_stand) / (γ_g · m_stand,1N)",
                quelle_formel="---",
                formelzeichen=["M_kipp", "M_stand", "γ_g", "m_stand,1N", "g"],
                quelle_formelzeichen=["---"],
            ),
            kontext=base_ctx,
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
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
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "kippsicherheit",
        "norm": getattr(norm, "name", str(norm)),
        "anzahl_windrichtungen": anzahl_windrichtungen,
    })
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
            kontext=base_ctx,
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
        kontext=base_ctx,
    )