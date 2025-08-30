from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List

class Norm(str, Enum):
    DIN_EN_1991_1_4_2010_12 = "EN 1991-1-4:2010-12" #Eurocode
    DIN_EN_13814_2005_06 = "DIN EN 13814:2005-06" #Fliegende Bauten
    DIN_EN_17879_2024_08 = "DIN EN 17879:2024-08" #Event-Strukturen
    DEFAULT = "Default"

@dataclass(frozen=True)
class Zwischenergebnis:
    """Allgemeine Struktur für dokumentationsfähige Ergebnisse."""
    wert: float                        # numerischer Wert
    formel: str                        # z.B. "λ = l / h"
    quelle_formel: str                 # Quelle der Formel
    formelzeichen: List[str]           # z.B. ["λ", "l", "h"]
    quelle_formelzeichen: List[str]    # Quelle der Formelzeichen
