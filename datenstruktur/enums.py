from __future__ import annotations
from enum import Enum

class TraversenTyp(str, Enum):
    ZWEI_PUNKT = "2-Punkt"
    DREI_PUNKT = "3-Punkt"
    VIER_PUNKT = "4-Punkt"

    @classmethod
    def from_points(cls, n: int) -> "TraversenTyp":
        """Bequemer Konstruktor aus 2/3/4."""
        mapping = {2: cls.ZWEI_PUNKT, 3: cls.DREI_PUNKT, 4: cls.VIER_PUNKT}
        try:
            return mapping[n]
        except KeyError:
            raise ValueError(f"Ungültige Anzahl Punkte: {n}. Erlaubt: 2, 3, 4.")
        
class Lasttyp(str, Enum):
    WIND = "wind"
    GEWICHT = "gewicht"
    REIBUNG = "reibung"

class Variabilitaet(str, Enum):
    STAENDIG = "staendig"
    VERAENDERLICH = "veraenderlich"

class Norm(str, Enum):
    DIN_EN_1991_1_4_2010_12 = "EN 1991-1-4:2010-12" #Eurocode
    DIN_EN_13814_2005_06 = "DIN EN 13814:2005-06" #Fliegende Bauten
    DIN_EN_17879_2024_08 = "DIN EN 17879:2024-08" #Event-Strukturen
    DEFAULT = "Default"

class ObjektTyp(str, Enum):
    TRAVERSE = "traverse"
    ROHR = "rohr"
    BODENPLATTE = "bodenplatte"

class MaterialTyp(str, Enum):
    HOLZ = "holz"
    STAHL = "stahl"
    BETON = "beton"
    TON = "ton"
    LEHM = "lehm"
    SAND = "sand"
    KIES = "kies"
    GUMMI = "gummi"

class FormTyp(str, Enum):
    RECHTECK = "rechteck"
    KREIS = "kreis"
    DREIECK = "dreieck"

class RechenmethodeKippen(str, Enum):
    STANDARD = "Standard"

class RechenmethodeGleiten(str, Enum):
    MIN_REIBWERT = "Minimaler Reibwert"
    PRO_PLATTE = "Pro Platte"
    REAKTIONEN = "Reaktionen"

class RechenmethodeAbheben(str, Enum):
    STANDARD = "Standard"