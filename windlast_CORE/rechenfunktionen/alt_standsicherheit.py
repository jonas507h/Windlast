from math import inf
from typing import List, Tuple, Dict, Sequence
from windlast_CORE.rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    kipp_envelope_pro_bauelement,
    sammle_kippachsen,
    get_or_create_lastset,
    obtain_pool,
    ermittle_min_reibwert,
    gleit_envelope_pro_bauelement,
    abhebe_envelope_pro_bauelement,
)
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektoren_addieren, vektor_laenge
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.enums import Norm, RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben, VereinfachungKonstruktion
from windlast_CORE.datenstruktur.lastpool import LastPool
from windlast_CORE.datenstruktur.konstanten import _EPS

_anzahl_windrichtungen_standard = 4

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
    anzahl_windrichtungen: int = _anzahl_windrichtungen_standard,
) -> float:
    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        raise NotImplementedError(f"Vereinfachung '{vereinfachung_konstruktion.value}' ({vereinfachung_konstruktion.name}) ist noch nicht implementiert.")

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion)

        # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
        sicherheit_min_global = inf

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

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                total_kipp = 0.0
                total_stand = 0.0

                for _, lastfaelle_elem in kraefte_nach_element.items():
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem)
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                if sicherheit < sicherheit_min_global:
                    sicherheit_min_global = sicherheit

        return sicherheit_min_global
    
    else:
        raise NotImplementedError(f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.")

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
    anzahl_windrichtungen: int = _anzahl_windrichtungen_standard,
) -> float:
    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        raise NotImplementedError(f"Vereinfachung '{vereinfachung_konstruktion.value}' ({vereinfachung_konstruktion.name}) ist noch nicht implementiert.")

    if methode == RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(konstruktion)
        sicherheit_min_global = inf
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
        
        return sicherheit_min_global
    
    else:
        raise NotImplementedError(f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.")

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
    anzahl_windrichtungen: int = _anzahl_windrichtungen_standard,
) -> float:
    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        raise NotImplementedError(f"Vereinfachung '{vereinfachung_konstruktion.value}' ({vereinfachung_konstruktion.name}) ist noch nicht implementiert.")

    if methode == RechenmethodeAbheben.STANDARD:
        """
        Sicherheitszahl gegen Abheben:
        η = Summe(N_down) / Summe(N_up), Minimum über alle Windrichtungen.
        - N_down: nur GEWICHT (günstig), mit γ_günstig
        - N_up:   alle aufwärts gerichteten Beiträge (ungünstig), mit γ_ungünstig
        """
        sicherheit_min_global = inf
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

            total_normal_down = 0.0
            total_normal_up = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                N_down_b, N_up_b = abhebe_envelope_pro_bauelement(norm, lastfaelle_elem)
                total_normal_down += N_down_b
                total_normal_up += N_up_b

            sicherheit = inf if total_normal_up <= _EPS else (total_normal_down / total_normal_up)
            if sicherheit < sicherheit_min_global:
                sicherheit_min_global = sicherheit

        return sicherheit_min_global
    
    else:
        raise NotImplementedError(f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.")