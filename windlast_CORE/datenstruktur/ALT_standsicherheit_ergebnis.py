from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple, Any

# Import der Enums aus deinem Projekt
from windlast_CORE.datenstruktur.enums import (
    Norm, Nachweis, Severity, NormStatus, ValueSource
)


# ---------- Nachrichten / Meta ----------

@dataclass
class Message:
    """
    Strukturierte Nachricht (maschinenlesbar + Text).
    Beispiel: code="NORM_NOT_APPLICABLE", severity=Severity.INFO
    """
    code: str
    severity: Severity
    text: str
    context: Mapping[str, str] = field(default_factory=dict)


@dataclass
class Meta:
    """
    Metadaten/Echo zur Berechnung (für Nachvollziehbarkeit).
    - methoden: Mapping je Nachweis auf die verwendete Rechenmethode (Enum-Instanzen erlaubt)
    - vereinfachung_konstruktion: deine Enum-Instanz (z.B. VereinfachungKonstruktion.KEINE)
    - konst_overrides: falls physikalische Konstanten überschrieben wurden
    """
    version: str
    inputs: Mapping[str, object] = field(default_factory=dict)
    methoden: Mapping[Nachweis, object] = field(default_factory=dict)
    vereinfachung_konstruktion: object = None
    anzahl_windrichtungen: int = 0
    konst_overrides: Mapping[str, object] = field(default_factory=dict)


# ---------- Werte / Details pro Nachweis ----------

@dataclass
class SafetyValue:
    """
    Ergebnis eines einzelnen Nachweises.
    - wert: None, wenn nicht anwendbar/Fehler
    - methode: z.B. RechenmethodeKippen.STANDARD (Typ bewusst 'object' für Flexibilität)
    - source: Herkunft (berechnet/angenommen/…)
    - messages: lokale Hinweise (z.B. 'Reibwert auf Mindestwert gesetzt')
    """
    wert: Optional[float]
    methode: object
    source: ValueSource
    messages: List[Message] = field(default_factory=list)


@dataclass
class WindrichtungErgebnis:
    """
    Optional: Detailwerte je Windrichtung (nur wenn aktiviert).
    """
    winkel_deg: float
    kipp: Optional[float] = None
    gleit: Optional[float] = None
    abhebe: Optional[float] = None


@dataclass
class NormDetails:
    """
    Optionale Debug-/Detaildaten für eine Norm.
    """
    windrichtungen: List[WindrichtungErgebnis] = field(default_factory=list)
    notes: List[Message] = field(default_factory=list)
    docs: List[tuple] = field(default_factory=list)  # List[Tuple[Any, dict]]


# ---------- Norm-Ergebnis / Gesamtergebnis ----------

@dataclass
class AlternativeErgebnis:
    """
    Ergebnis für ein alternatives Staudruck-Szenario.
    - key: technischer Szenario-Key (z.B. "AUSSER_BETRIEB")
    - anzeigename: UI-Label (z.B. "Außer Betrieb")
    - werte: Nachweis-Werte für dieses Szenario
    """
    anzeigename: str
    werte: Dict[Nachweis, SafetyValue] = field(default_factory=dict)

@dataclass
class NormErgebnis:
    """
    Ergebnis für eine einzelne Norm.
    - status: Gesamtstatus (berechnet/nicht anwendbar/Fehler)
    - reasons: Begründungen für not_applicable/error
    - werte: die drei Nachweise (Nachweis -> SafetyValue)
    - alternativen: z.B. {"evakuierung": {Nachweis.KIPP: 1.12, ...}, "gummimatte": {...}}
    - details: optionaler Debug-Block
    """
    status: NormStatus
    reasons: List[Message] = field(default_factory=list)
    werte: Dict[Nachweis, SafetyValue] = field(default_factory=dict)
    alternativen: Dict[str, AlternativeErgebnis] = field(default_factory=dict)
    details: Optional[NormDetails] = None


@dataclass
class StandsicherheitErgebnis:
    """
    Top-Level-Ergebnis der Funktion 'standsicherheit(...)'.
    - normen: Norm -> NormErgebnis
    - messages: normübergreifende Hinweise
    - meta: Metadaten/Echo
    """
    normen: Dict[Norm, NormErgebnis]
    messages: List[Message]
    meta: Meta
