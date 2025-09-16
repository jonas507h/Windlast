from math import inf
from typing import List, Tuple, Dict
from rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    kipp_envelope_pro_bauelement,
    sammle_kippachsen,
    get_or_create_lastset,
)
from rechenfunktionen.geom3d import Vec3
from datenstruktur.kraefte import Kraefte
from datenstruktur.enums import Norm
from datenstruktur.lastpool import LastPool

_EPS = 1e-12
_anzahl_windrichtungen_standard = 4

def kippsicherheit(konstruktion) -> float:
    # 1) Eckpunkte sammeln → Kippachsen bestimmen
    achsen = sammle_kippachsen(konstruktion)

    # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
    sicherheit_min_global = inf

    pool = LastPool()  # NEU: lokaler Cache; später ggf. an konstruktion hängen

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

def gleitsicherheit(konstruktion) -> float:
    return 1.0  # TODO

def abhebesicherheit(konstruktion) -> float:
    return 1.0  # TODO
