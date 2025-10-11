from dataclasses import dataclass
from typing import Dict, Tuple
from windlast_CORE.datenstruktur.enums import Zeitfaktor

# === Speicherform für Dauer ===
@dataclass(frozen=True)
class Dauer:
    wert: int            # Eingabe vom Nutzer (z. B. 30)
    einheit: Zeitfaktor  # Einheit (Tag/Monat/Jahr)

# === Paarweises Mapping exakt nach Vorgabe ===
# 30 Tage = 1 Monat; 365 Tage = 1 Jahr; 12 Monate = 1 Jahr
_CONV: Dict[Tuple[Zeitfaktor, Zeitfaktor], float] = {
    # Tage <-> Monate
    (Zeitfaktor.TAG,   Zeitfaktor.MONAT): 1.0/30.0,
    (Zeitfaktor.MONAT, Zeitfaktor.TAG):   30.0,

    # Tage <-> Jahre
    (Zeitfaktor.TAG,   Zeitfaktor.JAHR):  1.0/365.0,
    (Zeitfaktor.JAHR,  Zeitfaktor.TAG):   365.0,

    # Monate <-> Jahre
    (Zeitfaktor.MONAT, Zeitfaktor.JAHR):  1.0/12.0,
    (Zeitfaktor.JAHR,  Zeitfaktor.MONAT): 12.0,
}

def convert_dauer(value: float, src: Zeitfaktor, dst: Zeitfaktor) -> float:
    """
    Zahl, Inputfaktor, gewünschter Outputfaktor -> Zahl (float).
    """
    if src == dst:
        return float(value)
    try:
        factor = _CONV[(src, dst)]
    except KeyError:
        raise ValueError(f"Keine Konvertierung definiert: {src.value} -> {dst.value}")
    return float(value) * factor