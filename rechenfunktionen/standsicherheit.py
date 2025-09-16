from math import inf
from typing import List, Tuple, Dict
from rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    kipp_envelope_pro_bauelement,
    sammle_kippachsen,
    get_or_create_lastset,
    obtain_pool,
    ermittle_min_reibwert,
    gleit_envelope_pro_bauelement,
    abhebe_envelope_pro_bauelement,
)
from rechenfunktionen.geom3d import Vec3, vektoren_addieren, vektor_laenge
from datenstruktur.kraefte import Kraefte
from datenstruktur.enums import Norm
from datenstruktur.lastpool import LastPool

_EPS = 1e-12
_anzahl_windrichtungen_standard = 4

def kippsicherheit(konstruktion, *, reset_berechnungen: bool = True) -> float:
    # 1) Eckpunkte sammeln → Kippachsen bestimmen
    achsen = sammle_kippachsen(konstruktion)

    # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
    sicherheit_min_global = inf

    pool = obtain_pool(konstruktion, reset_berechnungen)

    for winkel, richtung in generiere_windrichtungen(anzahl=_anzahl_windrichtungen_standard):
        lastset = get_or_create_lastset(
            pool,
            konstruktion,
            winkel_deg=winkel,
            windrichtung=richtung,
            norm=Norm.DEFAULT,      # wie bisher: Platzhalter
            staudruecke=[350.0],        # wie bisher: Platzhalter
            obergrenzen=[float("inf")], # wie bisher
            konst=None,
        )
        kraefte_nach_element = lastset.kraefte_nach_element

        # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
        for achse in achsen:
            total_kipp = 0.0
            total_stand = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                kipp_b, stand_b = kipp_envelope_pro_bauelement(Norm.DEFAULT, achse, lastfaelle_elem)
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

def gleitsicherheit(
    konstruktion,
    *,
    reset_berechnungen: bool = False,
    methode: str = "min_reibwert",          # "min_reibwert" | "pro_platte" | "reaktionen" (später)
    anzahl_windrichtungen: int = _anzahl_windrichtungen_standard,
) -> float:
    if methode == "min_reibwert":
        reibwert_min = ermittle_min_reibwert(konstruktion)
        sicherheit_min_global = inf
        pool = obtain_pool(konstruktion, reset_berechnungen)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen):
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=Norm.DEFAULT,      # wie bisher: Platzhalter
                staudruecke=[350.0],        # wie bisher: Platzhalter
                obergrenzen=[float("inf")], # wie bisher
                konst=None,
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for _, lastfaelle_elem in kraefte_nach_element.items():
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(Norm.DEFAULT, lastfaelle_elem)
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
        raise NotImplementedError(f"Methode '{methode}' ist noch nicht implementiert.")

def abhebesicherheit(
    konstruktion,
    *,
    reset_berechnungen: bool = False,
    anzahl_windrichtungen: int = _anzahl_windrichtungen_standard,
) -> float:
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
            norm=Norm.DEFAULT,              # Platzhalter wie gehabt
            staudruecke=[350.0],
            obergrenzen=[float("inf")],
            konst=None,
        )
        kraefte_nach_element = lastset.kraefte_nach_element

        total_normal_down = 0.0
        total_normal_up = 0.0

        for _, lastfaelle_elem in kraefte_nach_element.items():
            N_down_b, N_up_b = abhebe_envelope_pro_bauelement(Norm.DEFAULT, lastfaelle_elem)
            total_normal_down += N_down_b
            total_normal_up += N_up_b

        sicherheit = inf if total_normal_up <= _EPS else (total_normal_down / total_normal_up)
        if sicherheit < sicherheit_min_global:
            sicherheit_min_global = sicherheit

    return sicherheit_min_global
