# rechenfunktionen/segmentierung.py
from __future__ import annotations
from typing import Sequence, List, Dict, Tuple, Optional
from rechenfunktionen.geom3d import Vec3, schnittpunkt_strecke_ebene, abstand_punkte

_EPS = 1e-9

def in_intervall(z: float, z_min: float, z_max: float, is_first: bool) -> bool:
    return (z_min + _EPS < z <= (z_max + _EPS)) or (is_first and z_min - _EPS <= z <= z_max + _EPS)

def segmentiere_strecke_nach_hoehenbereichen(
    startpunkt: Vec3,
    endpunkt: Vec3,
    staudruecke: Sequence[float],   # [q1, q2, ...] in N/m²
    obergrenzen: Sequence[float],   # [z1, z2, ...] in m (streng aufsteigend, ab z=0)
    z_unterkante: float = 0.0,      # Unterkante des ersten Bereichs (typisch 0.0 m)
) -> List[Dict]:
    if not obergrenzen:
        raise ValueError("obergrenzen darf nicht leer sein.")
    if any(obergrenzen[i] <= obergrenzen[i-1] for i in range(1, len(obergrenzen))):
        raise ValueError("obergrenzen müssen streng aufsteigend sein.")
    if len(staudruecke) != len(obergrenzen):
        raise ValueError("staudruecke und obergrenzen müssen gleich lang sein.")
    if any(q < 0 for q in staudruecke):
        raise ValueError("staudruecke müssen ≥ 0 sein.")

    z_top = obergrenzen[-1]  # höchste Obergrenze

    # Fehler wenn Konstruktion zu hoch
    if max(startpunkt[2], endpunkt[2]) > z_top + _EPS:
        raise ValueError("Konstruktion zu hoch.")

    # Segmentierung
    segmente: list[dict] = []
    z_min = z_unterkante
    z_start = startpunkt[2]
    z_ende = endpunkt[2]
    ebene_normal: Vec3 = (0.0, 0.0, 1.0)  # Normalenvektor der horizontalen Ebene
    for i, z_max in enumerate(obergrenzen):
        # Prüfen, ob Strecke in Segment liegt
        komplett_oberhalb = (z_start > z_max + _EPS and z_ende > z_max + _EPS)
        komplett_unterhalb = (z_start < z_min - _EPS and z_ende < z_min - _EPS)
        if komplett_oberhalb or komplett_unterhalb:
            z_min = z_max
            continue
        
        ebene_stuetz_min: Vec3 = (0.0, 0.0, z_min)
        ebene_stuetz_max: Vec3 = (0.0, 0.0, z_max)
        is_first = (i == 0)
        # Lokale Start- und Endpunkt bestimmen
        # Start
        if in_intervall(z_start, z_min, z_max, is_first):
            start_lokal = startpunkt
        elif z_start < z_min - _EPS:
            start_lokal = schnittpunkt_strecke_ebene(startpunkt, endpunkt, ebene_stuetz_min, ebene_normal)
        else:
            start_lokal = schnittpunkt_strecke_ebene(startpunkt, endpunkt, ebene_stuetz_max, ebene_normal)

        # Ende
        if in_intervall(z_ende, z_min, z_max, is_first):
            ende_lokal = endpunkt
        elif z_ende < z_min - _EPS:
            ende_lokal = schnittpunkt_strecke_ebene(startpunkt, endpunkt, ebene_stuetz_min, ebene_normal)
        else:
            ende_lokal = schnittpunkt_strecke_ebene(startpunkt, endpunkt, ebene_stuetz_max, ebene_normal)

        if start_lokal is None or ende_lokal is None:
            z_min = z_max
            continue

        if abstand_punkte(start_lokal, ende_lokal) <= _EPS:
            z_min = z_max
            continue

        segmente.append({
            "start_lokal": start_lokal,
            "ende_lokal": ende_lokal,
            "staudruck": staudruecke[i],
        })
        z_min = z_max

    return segmente
