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

class VereinfachungKonstruktion(str, Enum):
    KEINE = "keine"

class Betriebszustand(str, Enum):
    IN_BETRIEB = "in Betrieb"
    AUSSER_BETRIEB = "außer Betrieb"

class Windzone(str, Enum):
    I_BINNENLAND = "1 Binnenland"
    II_BINNENLAND = "2 Binnenland"
    II_KUESTE = "2 Küste und Inseln der Ostsee"
    III_Binnenland = "3 Binnenland"
    III_KUESTE = "3 Küste und Inseln der Ostsee"
    IV_BINNENLAND = "4 Binnenland"
    IV_KUESTE = "4 Küste der Nord- und Ostesee; Inseln der Ostsee"
    IV_INSELN = "4 Inseln der Nordsee"

class Schutzmassnahmen(str, Enum):
    KEINE = "keine"
    SCHUETZEND = "schützend"
    VERSTAERKEND = "verstärkend"

class Zeitfaktor(str, Enum):
    TAG = "Tag"
    MONAT = "Monat"
    JAHR = "Jahr"

# --- Ergänzungen für Standsicherheits-Strukturen ---

class Nachweis(str, Enum):
    """Arten der Nachweise, werden auch als Keys verwendet."""
    KIPP = "kipp"
    GLEIT = "gleit"
    ABHEBE = "abhebe"
    BALLAST = "ballast"


class Severity(str, Enum):
    """Schweregrad von Meldungen/Hinweisen."""
    INFO = "info"
    HINT = "hint"
    WARN = "warn"
    ERROR = "error"


class ValueSource(str, Enum):
    """Herkunft eines Safety-Wertes (für Transparenz/Debugging)."""
    COMPUTED = "computed"
    ASSUMED = "assumed"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


class NormStatus(str, Enum):
    """Gesamtstatus der Berechnung für eine Norm."""
    CALCULATED = "calculated"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"

class TraversenOrientierung(str, Enum):
    UP = "up"
    SIDE = "side"
    DOWN = "down"