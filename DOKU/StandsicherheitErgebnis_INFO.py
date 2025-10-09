# ======================================================================
#  StandsicherheitErgebnis – reine Strukturdefinition (Schema)
#  Ziel: Nur Hierarchie, Feldtypen, zulässige Werte – keine Nutzungshinweise.
#  Quellen: datenstruktur/standsicherheit_ergebnis.py, datenstruktur/enums.py
#  (Verweise an den relevanten Blöcken als Kommentar)
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Mapping, Any

# Enums (aus enums.py) – werden in den Strukturen referenziert. :contentReference[oaicite:0]{index=0}
from ..windlast_CORE.datenstruktur.enums import (
    Nachweis,         # "kipp" | "gleit" | "abhebe" | "ballast"
    Severity,         # "info" | "hint" | "warn" | "error"
    ValueSource,      # "computed" | "assumed" | "not_applicable" | "error"
    NormStatus,       # "calculated" | "not_applicable" | "error"
    Norm,             # z. B. "DIN EN 17879:2024-08"
    VereinfachungKonstruktion,
    RechenmethodeKippen,
    RechenmethodeGleiten,
    RechenmethodeAbheben,
)

# ======================================================================
#  Basiselemente
# ======================================================================

@dataclass
class Message:
    """
    Einzelne Meldung.
      - code: stabiler, maschinenlesbarer Schlüssel
      - severity: Schweregrad (Enum Severity)
      - text: kurzer menschenlesbarer Text
      - context: optionale Zusatzzahlen/-strings, frei erweiterbar
    Quelle: Message-Definition in standsicherheit_ergebnis.py. :contentReference[oaicite:1]{index=1}
    """
    code: str
    severity: Severity
    text: str
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class SafetyValue:
    """
    Ergebniswert je Nachweis.
      - wert: float | None
              Sicherheitszahl bzw. Ballast (je nach Nachweis)
      - methode: Enum-Instanz der verwendeten Rechenmethode ODER kompatibles Objekt/String.
                 (z. B. RechenmethodeKippen.STANDARD, RechenmethodeGleiten.MIN_REIBWERT, ...)
      - source: Herkunft (Enum ValueSource)
      - messages: lokale Meldungen zu diesem Wert (meist leer)
    Quelle: SafetyValue-Definition in standsicherheit_ergebnis.py. :contentReference[oaicite:2]{index=2}
    """
    wert: Optional[float]
    methode: Any
    source: ValueSource
    messages: List[Message] = field(default_factory=list)


# ======================================================================
#  Detaildaten (optional) – für Windrichtungsauflösungen etc.
# ======================================================================

@dataclass
class WindrichtungErgebnis:
    """
    Werte in einer konkreten Windrichtung (optional).
      - winkel_deg: Richtung in Grad
      - kipp/gleit/abhebe: Sicherheitszahlen (None, wenn nicht anwendbar)
    Quelle: WindrichtungErgebnis in standsicherheit_ergebnis.py. :contentReference[oaicite:3]{index=3}
    """
    winkel_deg: float
    kipp: Optional[float] = None
    gleit: Optional[float] = None
    abhebe: Optional[float] = None


@dataclass
class NormDetails:
    """
    Zusätzliche, optionale Detaildaten für eine Norm.
      - windrichtungen: Liste von WindrichtungErgebnis
      - notes: zusätzliche Meldungen/Notizen
    Quelle: NormDetails in standsicherheit_ergebnis.py. :contentReference[oaicite:4]{index=4}
    """
    windrichtungen: List[WindrichtungErgebnis] = field(default_factory=list)
    notes: List[Message] = field(default_factory=list)


# ======================================================================
#  Norm-spezifischer Ergebnisblock
# ======================================================================

@dataclass
class NormErgebnis:
    """
    Ergebnis einer Norm.
      - status: Gesamtstatus (Enum NormStatus)
      - reasons: zentrale Gründe/Meldungen zum Normlauf
      - werte: maßgebende Ergebnisse je Nachweis → SafetyValue
               Key ist Enum Nachweis (kipp/gleit/abhebe/ballast)
      - alternativen: kompakte Alternativ-Sichten mit reinen Zahlenwerten
                      Mapping[label] -> Mapping[Nachweis] -> float|None
                      (Hier stehen NUR Zahlenwerte, keine SafetyValue-Objekte!)
      - details: optionale Detaildaten (z. B. Windrichtungswerte)
    Quelle: NormErgebnis in standsicherheit_ergebnis.py. :contentReference[oaicite:5]{index=5}
    """
    status: NormStatus
    reasons: List[Message] = field(default_factory=list)
    werte: Dict[Nachweis, SafetyValue] = field(default_factory=dict)
    alternativen: Dict[str, Dict[Nachweis, Optional[float]]] = field(default_factory=dict)
    details: Optional[NormDetails] = None


# ======================================================================
#  Metadaten zum Lauf (Echo-/Konfig-Infos)
# ======================================================================

@dataclass
class Meta:
    """
    Metadaten des Ergebnisobjekts.
      - version: String zur Nachvollziehbarkeit (z. B. Modul-/Schema-Version)
      - inputs: freie Echo-Struktur der Eingangsdaten (normierte Schlüssel empfohlen)
      - methoden: Mapping je Nachweis -> verwendete Methode (Enum-Instanz/Objekt)
      - vereinfachung_konstruktion: ggf. Enum-Instanz (z. B. VereinfachungKonstruktion.KEINE)
      - anzahl_windrichtungen: z. B. 4, 8, ...
      - konst_overrides: Mapping für überschriebenen Konstanten/Parameter
    Quelle: Meta in standsicherheit_ergebnis.py. :contentReference[oaicite:6]{index=6}
    """
    version: str = "n/a"
    inputs: Mapping[str, Any] = field(default_factory=dict)
    methoden: Mapping[Nachweis, Any] = field(default_factory=dict)
    vereinfachung_konstruktion: Any = None
    anzahl_windrichtungen: int = 0
    konst_overrides: Mapping[str, Any] = field(default_factory=dict)


# ======================================================================
#  Top-Level Ergebniscontainer
# ======================================================================

@dataclass
class StandsicherheitErgebnis:
    """
    Gesamtergebnis über alle betrachteten Normen.
      - normen: Mapping[Norm -> NormErgebnis]
                Key ist Enum Norm (z. B. DIN_EN_17879_2024_08, ...),
                im JSON üblicherweise als String repräsentiert.
      - messages: normübergreifende Meldungen (selten genutzt)
      - meta: Metadaten (Kontext, Methoden, Inputs ...)
    Quelle: StandsicherheitErgebnis in standsicherheit_ergebnis.py. :contentReference[oaicite:7]{index=7}
    """
    normen: Dict[Norm, NormErgebnis] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)
    meta: Meta = field(default_factory=Meta)


# ======================================================================
#  Zusammenfassung der zulässigen Enum-Werte (Referenz)
# ======================================================================
#  Nachweis      : Nachweis.KIPP | Nachweis.GLEIT | Nachweis.ABHEBE | Nachweis.BALLAST
#  Severity      : Severity.INFO | Severity.HINT | Severity.WARN | Severity.ERROR
#  ValueSource   : ValueSource.COMPUTED | ValueSource.ASSUMED | ValueSource.NOT_APPLICABLE | ValueSource.ERROR
#  NormStatus    : NormStatus.CALCULATED | NormStatus.NOT_APPLICABLE | NormStatus.ERROR
#  Norm          : z. B. Norm.DIN_EN_17879_2024_08, Norm.DIN_EN_13814_2005_06, ...
#  Methode (Beispiel-Enums, falls verwendet in 'methode' / 'meta.methoden'):
#                  RechenmethodeKippen.STANDARD,
#                  RechenmethodeGleiten.MIN_REIBWERT | PRO_PLATTE | REAKTIONEN,
#                  RechenmethodeAbheben.STANDARD,
#                  usw. (Projekt-spezifische Enums)
#  (Alle Enum-Definitionen siehe enums.py.) :contentReference[oaicite:8]{index=8}

# ======================================================================
#  Hinweis zur Kardinalität / Strukturkonstanz
# ======================================================================
#  - StandsicherheitErgebnis.normen: beliebig viele Normen (Key = Enum Norm)
#  - NormErgebnis.werte: bis zu vier Schlüssel (Nachweis) → SafetyValue
#  - NormErgebnis.alternativen: beliebige Labels; je Label Werte je Nachweis (float|None)
#  - Optionale Teile (details, notes, messages) sind entbehrlich, Struktur bleibt stabil.
#  (Konforme Struktur vgl. standsicherheit_ergebnis.py.) :contentReference[oaicite:9]{index=9}

# ---- Meta (Echo der Berechnung) --------------------------------------------
meta = Meta(
    version="core-dev",
    inputs={
        "konstruktion_typ": "Tor",
        "windzone": "I_BINNENLAND",
        "aufstelldauer": None,
    },
    methoden={
        Nachweis.KIPP:   RechenmethodeKippen.STANDARD,
        Nachweis.GLEIT:  RechenmethodeGleiten.MIN_REIBWERT,
        Nachweis.ABHEBE: RechenmethodeAbheben.STANDARD,
    },
    vereinfachung_konstruktion=VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen=4,
    konst_overrides={},
)

# ---- Reason-Log (aus dem Protokoll eingesammelt) ---------------------------
reasons_1991 = [
    Message(
        code="SICHB/CASE",
        severity=Severity.HINT,
        text="Günstig: ständige Eigenlast wird mit γ=1.0 angesetzt.",
        context={"norm": "DIN_EN_1991_1_4_2010_12", "szenario": "STANDARD"},
    ),
    Message(
        code="SICHB/CASE",
        severity=Severity.HINT,
        text="Günstig: variable/sonstige Lasten werden mit γ=0.0 angesetzt.",
        context={"norm": "DIN_EN_1991_1_4_2010_12", "szenario": "STANDARD"},
    ),
]

# ---- Safety-Werte für die Norm (maßgebende Werte) --------------------------
werte_1991 = {
    Nachweis.KIPP:   SafetyValue(
        wert=0.43,
        methode=RechenmethodeKippen.STANDARD,
        source=ValueSource.COMPUTED,
        messages=[],
    ),
    Nachweis.GLEIT:  SafetyValue(
        wert=1.05,
        methode=RechenmethodeGleiten.MIN_REIBWERT,
        source=ValueSource.COMPUTED,
        messages=[],
    ),
    Nachweis.ABHEBE: SafetyValue(
        wert=float("inf"),
        methode=RechenmethodeAbheben.STANDARD,
        source=ValueSource.COMPUTED,
        messages=[],
    ),
    # Für BALLAST wird im Core aktuell eine String-Methode hinterlegt (siehe Code),
    # weil es eine aggregierte Ableitung ist.
    Nachweis.BALLAST: SafetyValue(
        wert=283.48,  # [kg]
        methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
        source=ValueSource.COMPUTED,
        messages=[],
    ),
}

# ---- NormErgebnis bündeln ---------------------------------------------------
norm_1991 = NormErgebnis(
    status=NormStatus.CALCULATED,
    reasons=reasons_1991,
    werte=werte_1991,
    alternativen={},     # ggf. weitere geprüfte Szenarien hier ablegen
    details=None,        # optionaler Debug-Block (Windrichtungen/Notes)
)

# ---- Top-Level Ergebnis -----------------------------------------------------
ergebnis = StandsicherheitErgebnis(
    normen={
        Norm.DIN_EN_1991_1_4_2010_12: norm_1991,
        # weitere Normen könnten hier ergänzt werden …
    },
    messages=[],  # normübergreifende Hinweise (falls vorhanden)
    meta=meta,
)

# 'ergebnis' ist jetzt ein vollwertiges, reales Ergebnisobjekt mit Enums.