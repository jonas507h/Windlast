from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List

@dataclass(frozen=True)
class Zwischenergebnis:
    """Allgemeine Struktur für dokumentationsfähige Ergebnisse."""
    wert: float                        # numerischer Wert
    formel: str                        # z.B. "λ = l / h"
    quelle_formel: str                 # Quelle der Formel
    formelzeichen: List[str]           # z.B. ["λ", "l", "h"]
    quelle_formelzeichen: List[str]    # Quelle der Formelzeichen
