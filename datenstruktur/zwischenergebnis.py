from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence
from rechenfunktionen.geom3d import Vec3

@dataclass(frozen=True)
class Zwischenergebnis:
    """Allgemeine Struktur für dokumentationsfähige Ergebnisse."""
    wert: float                        # numerischer Wert
    formel: str                        # z.B. "λ = l / h"
    quelle_formel: str                 # Quelle der Formel
    formelzeichen: List[str]           # z.B. ["λ", "l", "h"]
    quelle_formelzeichen: List[str]    # Quelle der Formelzeichen
    einzelwerte: Optional[List[float]] = None
    quelle_einzelwerte: Optional[List[str]] = None

@dataclass(frozen=True)
class Zwischenergebnis_Vektor:
    """Struktur für dokumentationsfähige Ergebnisse in Vektorform."""
    wert: Vec3                        # Vektorwert
    formel: str                       # z.B. "F = m · a"
    quelle_formel: str                # Quelle der Formel
    formelzeichen: List[str]          # z.B. ["F", "m", "a"]
    quelle_formelzeichen: List[str]   # Quelle der Formelzeichen

@dataclass(frozen=True)
class Zwischenergebnis_Liste:
    """Struktur für dokumentationsfähige Ergebnisse in Listenform."""
    wert: Sequence[float]              # numerischer Werte
    formel: str                        # z.B. "λ = l / h"
    quelle_formel: str                 # Quelle der Formel
    formelzeichen: List[str]           # z.B. ["λ", "l", "h"]
    quelle_formelzeichen: List[str]    # Quelle der Formelzeichen
    einzelwerte: Optional[List[float]] = None
    quelle_einzelwerte: Optional[List[str]] = None
