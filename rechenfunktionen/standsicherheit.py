from math import inf
from typing import List, Tuple, Dict
from rechenfunktionen.standsicherheit_utils import generiere_windrichtungen, kippachsen_aus_eckpunkten, bewerte_lastfall_fuer_achse, kipp_envelope_pro_bauelement
from rechenfunktionen.geom3d import Vec3
from datenstruktur.kraefte import Kraefte
from datenstruktur.enums import Norm

_EPS = 1e-12
_anzahl_windrichtungen_standard = 4

def kippsicherheit(konstruktion) -> float:
    # 1) Eckpunkte sammeln → Kippachsen bestimmen
    eckpunkte: List[Vec3] = []

    for obj in getattr(konstruktion, "bauelemente", []):
        ep = getattr(obj, "eckpunkte", None)
        if callable(ep):
            punkte = ep()
            if punkte:
                eckpunkte.extend(punkte)

    achsen = kippachsen_aus_eckpunkten(eckpunkte, include_Randpunkte=False)

    # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
    sicherheit_min_global = inf

    for winkel, richtung in generiere_windrichtungen(anzahl=_anzahl_windrichtungen_standard):
        # 2a) Für diese Richtung: Wind- & Gewichtskräfte aller Bauelemente holen
        kraefte_windrichtung: List[Kraefte] = []

        for elem in (getattr(konstruktion, "bauelemente", None) or []):
            # Gewicht
            fn_gewicht = getattr(elem, "gewichtskraefte", None)
            if callable(fn_gewicht):
                kraefte_gewicht = fn_gewicht()  # -> List[Kraefte]
                if kraefte_gewicht:
                    kraefte_windrichtung.extend(kraefte_gewicht)

            # Wind
            fn_wind = getattr(elem, "windkraefte", None)
            if callable(fn_wind):
                kraefte_wind = fn_wind(
                    norm=Norm.DEFAULT,              # Platzhalter
                    windrichtung=richtung,
                    staudruecke=[350.0],          # Platzhalter
                    obergrenzen=[float("inf")],   # Platzhalter
                    konst=None,
                )  # -> List[Kraefte]
                if kraefte_wind:
                    kraefte_windrichtung.extend(kraefte_wind)
    
        # 2b) Nach Bauelement gruppieren (erwartet: element_id_intern gesetzt)
        kraefte_nach_element: Dict[str, List[Kraefte]] = {}
        for k in kraefte_windrichtung:
            key = k.element_id_intern or f"elem_{id(k)}"  # Fallback, falls ID fehlt
            kraefte_nach_element.setdefault(key, []).append(k)

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
