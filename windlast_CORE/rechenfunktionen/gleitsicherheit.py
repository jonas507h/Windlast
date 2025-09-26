# rechenfunktionen/gleitsicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List
from collections.abc import Sequence as _SeqABC

from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, RechenmethodeGleiten, VereinfachungKonstruktion, Lasttyp, Variabilitaet
from datenstruktur.konstanten import _EPS, aktuelle_konstanten
from rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from datenstruktur.kraefte import Kraefte

from rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    obtain_pool,
    get_or_create_lastset,
    ermittle_min_reibwert,
    gleit_envelope_pro_bauelement,
)
from rechenfunktionen.geom3d import Vec3, vektoren_addieren, vektor_laenge

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
) -> List[Zwischenergebnis]:
    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        raise NotImplementedError(
            f"Vereinfachung '{vereinfachung_konstruktion.value}' ({vereinfachung_konstruktion.name}) ist noch nicht implementiert."
        )

    if methode is RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(norm,konstruktion)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True)
        pool = obtain_pool(konstruktion, reset_berechnungen)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen):
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(norm, lastfaelle_elem)
                total_horizontal = vektoren_addieren([total_horizontal, H_vec])
                total_normal_up += N_up
                total_normal_down += N_down

            horizontal_betrag = vektor_laenge(total_horizontal)
            normal_effektiv = max(0.0, total_normal_down - total_normal_up)
            reibkraft = reibwert_min * normal_effektiv

            if horizontal_betrag > _EPS:
                sicherheit = reibkraft / horizontal_betrag
                sicherheit_min_global = min(sicherheit_min_global, sicherheit)

            if reibwert_min <= _EPS:
                if horizontal_betrag > _EPS:
                    ballastkraft = inf
                else:
                    ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
            else:
                ballastkraft = max(0.0, horizontal_betrag / reibwert_min + total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert

            if ballastkraft > ballast_erforderlich_max:
                ballast_erforderlich_max = ballastkraft

        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung  # in N -> in kg

        sicherheit_Z = Zwischenergebnis(
            wert=sicherheit_min_global,
            formel="S = R / T",
            quelle_formel="---",
            formelzeichen=["R", "T"],
            quelle_formelzeichen=["---"],
        )

        ballast_Z = Zwischenergebnis(
            wert=ballast_kg,
            formel="ΔN_down,erf = T/μ + ΣN_up − ΣN_down",
            quelle_formel="---",
            formelzeichen=["T", "μ", "N_up", "N_down"],
            quelle_formelzeichen=["---"],
        )

        return [sicherheit_Z, ballast_Z]

    else:
        raise NotImplementedError(f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.")


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
) -> List[Zwischenergebnis]:
    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        raise NotImplementedError(
            f"Vereinfachung '{vereinfachung_konstruktion.value}' ({vereinfachung_konstruktion.name}) ist noch nicht implementiert."
        )

    if methode is RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(norm,konstruktion)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True)
        pool = obtain_pool(konstruktion, reset_berechnungen)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen):
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(norm, lastfaelle_elem)
                total_horizontal = vektoren_addieren([total_horizontal, H_vec])
                total_normal_up += N_up
                total_normal_down += N_down

            horizontal_betrag = vektor_laenge(total_horizontal)
            normal_effektiv = max(0.0, total_normal_down - total_normal_up)
            reibkraft = reibwert_min * normal_effektiv

            if horizontal_betrag > _EPS:
                sicherheit = reibkraft / horizontal_betrag
                sicherheit_min_global = min(sicherheit_min_global, sicherheit)

            if reibwert_min <= _EPS:
                if horizontal_betrag > _EPS:
                    ballastkraft = inf
                else:
                    ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
            else:
                ballastkraft = max(0.0, horizontal_betrag / reibwert_min + total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert

            if ballastkraft > ballast_erforderlich_max:
                ballast_erforderlich_max = ballastkraft

        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung  # in N -> in kg

        sicherheit_Z = Zwischenergebnis(
            wert=sicherheit_min_global,
            formel="S = R / T",
            quelle_formel="---",
            formelzeichen=["R", "T"],
            quelle_formelzeichen=["---"],
        )

        ballast_Z = Zwischenergebnis(
            wert=ballast_kg,
            formel="ΔN_down,erf = T/μ + ΣN_up − ΣN_down",
            quelle_formel="---",
            formelzeichen=["T", "μ", "N_up", "N_down"],
            quelle_formelzeichen=["---"],
        )

        return [sicherheit_Z, ballast_Z]

    else:
        raise NotImplementedError(f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.")
    
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
) -> List[Zwischenergebnis]:
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
    )
    