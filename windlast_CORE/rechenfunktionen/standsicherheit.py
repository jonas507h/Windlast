# datenstruktur/standsicherheit.py
from __future__ import annotations

from typing import Optional, Sequence, Tuple, Any, List, Dict

# Enums & Ergebnisstrukturen
from datenstruktur.enums import (
    Norm,
    Windzone,
    Betriebszustand,
    Schutzmassnahmen,
    RechenmethodeKippen,
    RechenmethodeGleiten,
    RechenmethodeAbheben,
    VereinfachungKonstruktion,
    Nachweis,
    Severity,
    ValueSource,
    NormStatus,
)
from datenstruktur.zeit import Dauer
from datenstruktur.standsicherheit_ergebnis import (
    StandsicherheitErgebnis,
    NormErgebnis,
    SafetyValue,
    Message,
    Meta,
)
from rechenfunktionen.staudruecke import staudruecke  # type: ignore


def standsicherheit(
    konstruktion: Any,
    *,
    aufstelldauer: Optional[Dauer],
    windzone: Windzone,
    konst: Optional[Any] = None,
    methode: Optional[
        Tuple[RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben]
    ] = None,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
) -> StandsicherheitErgebnis:
    """
    Rechnet die drei Nachweise (Kipp/Gleit/Abhebe) je Norm explizit (ohne Schleife).
    Erwartet, dass konstruktion die Methoden:
      - berechne_kippsicherheit(...)
      - berechne_gleitsicherheit(...)
      - berechne_abhebesicherheit(...)
    mit der Signatur (norm, staudruecke, obergrenzen, *, konst=..., reset_berechnungen=True,
                      methode=..., vereinfachung_konstruktion=..., anzahl_windrichtungen=...)
    bereitstellt und jeweils ein Objekt mit Attribut '.wert' zurückliefert.
    """

    # Default-Rechenmethoden
    if methode is None:
        methode = (
            RechenmethodeKippen.STANDARD,
            RechenmethodeGleiten.MIN_REIBWERT,
            RechenmethodeAbheben.STANDARD,
        )
    meth_kipp, meth_gleit, meth_abhebe = methode

    # Meta vorbereiten
    meta = Meta(
        version="core-dev",
        inputs={
            "konstruktion_typ": konstruktion.__class__.__name__,
            "windzone": windzone.name,
            "aufstelldauer": {"wert": aufstelldauer.wert, "einheit": aufstelldauer.einheit.name}
            if aufstelldauer is not None
            else None,
        },
        methoden={
            Nachweis.KIPP: meth_kipp,
            Nachweis.GLEIT: meth_gleit,
            Nachweis.ABHEBE: meth_abhebe,
        },
        vereinfachung_konstruktion=vereinfachung_konstruktion,
        anzahl_windrichtungen=anzahl_windrichtungen,
        konst_overrides={} if konst is None else {"custom": True},
    )

    normen: Dict[Norm, NormErgebnis] = {}

    # --------------------------
    # DIN EN 13814:2005-06
    # --------------------------
    reasons_13814: List[Message] = []
    try:
        zl1, zl2 = staudruecke(
            Norm.DIN_EN_13814_2005_06,
            konstruktion,
            Betriebszustand.AUSSER_BETRIEB,
            aufstelldauer=aufstelldauer,
            windzone=None,
        )
        z_13814 = list(zl1.wert)  # Obergrenzen
        q_13814 = list(zl2.wert)  # Staudrücke  
    except Exception as e:
        # harte Vorstufe — ohne q/z keine weitere Rechnung möglich
        msg = Message(
            code="STAUDRUECKE_FAILED",
            severity=Severity.ERROR,
            text=f"Staudrücke/Obergrenzen (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
            context={},
        )
        normen[Norm.DIN_EN_13814_2005_06] = NormErgebnis(
            status=NormStatus.ERROR,
            reasons=[msg],
            werte={
                Nachweis.KIPP:   SafetyValue(None, meth_kipp, ValueSource.ERROR, []),
                Nachweis.GLEIT:  SafetyValue(None, meth_gleit, ValueSource.ERROR, []),
                Nachweis.ABHEBE: SafetyValue(None, meth_abhebe, ValueSource.ERROR, []),
            },
        )
    else:
        # drei Nachweise
        # Kipp
        try:
            r_kipp = konstruktion.berechne_kippsicherheit(
                Norm.DIN_EN_13814_2005_06, q_13814, z_13814,
                konst=konst, reset_berechnungen=True,
                methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_kipp = float(r_kipp.wert)
            sv_kipp = SafetyValue(v_kipp, meth_kipp, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_13814.append(Message(
                code="KIPP_FAILED",
                severity=Severity.ERROR,
                text=f"Kippsicherheit (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
                context={},
            ))
            sv_kipp = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])

        # Gleit
        try:
            r_gleit = konstruktion.berechne_gleitsicherheit(
                Norm.DIN_EN_13814_2005_06, q_13814, z_13814,
                konst=konst, reset_berechnungen=True,
                methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_gleit = float(r_gleit.wert)
            sv_gleit = SafetyValue(v_gleit, meth_gleit, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_13814.append(Message(
                code="GLEIT_FAILED",
                severity=Severity.ERROR,
                text=f"Gleitsicherheit (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
                context={},
            ))
            sv_gleit = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])

        # Abhebe
        try:
            r_abhebe = konstruktion.berechne_abhebesicherheit(
                Norm.DIN_EN_13814_2005_06, q_13814, z_13814,
                konst=konst, reset_berechnungen=True,
                methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_abhebe = float(r_abhebe.wert)
            sv_abhebe = SafetyValue(v_abhebe, meth_abhebe, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_13814.append(Message(
                code="ABHEBE_FAILED",
                severity=Severity.ERROR,
                text=f"Abhebesicherheit (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
                context={},
            ))
            sv_abhebe = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])

        status_13814 = NormStatus.ERROR if reasons_13814 else NormStatus.CALCULATED
        normen[Norm.DIN_EN_13814_2005_06] = NormErgebnis(
            status=status_13814,
            reasons=reasons_13814,
            werte={
                Nachweis.KIPP: sv_kipp,
                Nachweis.GLEIT: sv_gleit,
                Nachweis.ABHEBE: sv_abhebe,
            },
        )

    # --------------------------
    # DIN EN 17879:2024-08
    # --------------------------
    reasons_17879: List[Message] = []
    try:
        zl1, zl2 = staudruecke(
            Norm.DIN_EN_17879_2024_08,
            konstruktion,
            Betriebszustand.AUSSER_BETRIEB,
            aufstelldauer=aufstelldauer,
            windzone=None,
        )
        z_17879 = list(zl1.wert)  # Obergrenzen
        q_17879 = list(zl2.wert)  # Staudrücke
    except Exception as e:
        msg = Message(
            code="STAUDRUECKE_FAILED",
            severity=Severity.ERROR,
            text=f"Staudrücke/Obergrenzen (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
            context={},
        )
        normen[Norm.DIN_EN_17879_2024_08] = NormErgebnis(
            status=NormStatus.ERROR,
            reasons=[msg],
            werte={
                Nachweis.KIPP:   SafetyValue(None, meth_kipp, ValueSource.ERROR, []),
                Nachweis.GLEIT:  SafetyValue(None, meth_gleit, ValueSource.ERROR, []),
                Nachweis.ABHEBE: SafetyValue(None, meth_abhebe, ValueSource.ERROR, []),
            },
        )
    else:
        # Kipp
        try:
            r_kipp = konstruktion.berechne_kippsicherheit(
                Norm.DIN_EN_17879_2024_08, q_17879, z_17879,
                konst=konst, reset_berechnungen=True,
                methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            sv_kipp = SafetyValue(float(r_kipp.wert), meth_kipp, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_17879.append(Message(
                code="KIPP_FAILED",
                severity=Severity.ERROR,
                text=f"Kippsicherheit (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
                context={},
            ))
            sv_kipp = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])

        # Gleit
        try:
            r_gleit = konstruktion.berechne_gleitsicherheit(
                Norm.DIN_EN_17879_2024_08, q_17879, z_17879,
                konst=konst, reset_berechnungen=True,
                methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            sv_gleit = SafetyValue(float(r_gleit.wert), meth_gleit, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_17879.append(Message(
                code="GLEIT_FAILED",
                severity=Severity.ERROR,
                text=f"Gleitsicherheit (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
                context={},
            ))
            sv_gleit = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])

        # Abhebe
        try:
            r_abhebe = konstruktion.berechne_abhebesicherheit(
                Norm.DIN_EN_17879_2024_08, q_17879, z_17879,
                konst=konst, reset_berechnungen=True,
                methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            sv_abhebe = SafetyValue(float(r_abhebe.wert), meth_abhebe, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_17879.append(Message(
                code="ABHEBE_FAILED",
                severity=Severity.ERROR,
                text=f"Abhebesicherheit (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
                context={},
            ))
            sv_abhebe = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])

        status_17879 = NormStatus.ERROR if reasons_17879 else NormStatus.CALCULATED
        normen[Norm.DIN_EN_17879_2024_08] = NormErgebnis(
            status=status_17879,
            reasons=reasons_17879,
            werte={
                Nachweis.KIPP: sv_kipp,
                Nachweis.GLEIT: sv_gleit,
                Nachweis.ABHEBE: sv_abhebe,
            },
        )

    # --------------------------
    # DIN EN 1991-1-4:2010-12
    # --------------------------
    reasons_1991: List[Message] = []
    try:
        zl1, zl2 = staudruecke(
            Norm.DIN_EN_1991_1_4_2010_12,
            konstruktion,
            Schutzmassnahmen.KEINE,
            aufstelldauer=aufstelldauer,
            windzone=windzone,
        )
        z_1991 = list(zl1.wert)  # Obergrenzen
        q_1991 = list(zl2.wert)  # Staudrücke
    except Exception as e:
        msg = Message(
            code="STAUDRUECKE_FAILED",
            severity=Severity.ERROR,
            text=f"Geschwindigkeitsdruck/Obergrenze (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
            context={},
        )
        normen[Norm.DIN_EN_1991_1_4_2010_12] = NormErgebnis(
            status=NormStatus.ERROR,
            reasons=[msg],
            werte={
                Nachweis.KIPP:   SafetyValue(None, meth_kipp, ValueSource.ERROR, []),
                Nachweis.GLEIT:  SafetyValue(None, meth_gleit, ValueSource.ERROR, []),
                Nachweis.ABHEBE: SafetyValue(None, meth_abhebe, ValueSource.ERROR, []),
            },
        )
    else:
        # Kipp
        try:
            r_kipp = konstruktion.berechne_kippsicherheit(
                Norm.DIN_EN_1991_1_4_2010_12, q_1991, z_1991,
                konst=konst, reset_berechnungen=True,
                methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            sv_kipp = SafetyValue(float(r_kipp.wert), meth_kipp, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_1991.append(Message(
                code="KIPP_FAILED",
                severity=Severity.ERROR,
                text=f"Kippsicherheit (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
                context={},
            ))
            sv_kipp = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])

        # Gleit
        try:
            r_gleit = konstruktion.berechne_gleitsicherheit(
                Norm.DIN_EN_1991_1_4_2010_12, q_1991, z_1991,
                konst=konst, reset_berechnungen=True,
                methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            sv_gleit = SafetyValue(float(r_gleit.wert), meth_gleit, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_1991.append(Message(
                code="GLEIT_FAILED",
                severity=Severity.ERROR,
                text=f"Gleitsicherheit (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
                context={},
            ))
            sv_gleit = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])

        # Abhebe
        try:
            r_abhebe = konstruktion.berechne_abhebesicherheit(
                Norm.DIN_EN_1991_1_4_2010_12, q_1991, z_1991,
                konst=konst, reset_berechnungen=True,
                methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            sv_abhebe = SafetyValue(float(r_abhebe.wert), meth_abhebe, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_1991.append(Message(
                code="ABHEBE_FAILED",
                severity=Severity.ERROR,
                text=f"Abhebesicherheit (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
                context={},
            ))
            sv_abhebe = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])

        status_1991 = NormStatus.ERROR if reasons_1991 else NormStatus.CALCULATED
        normen[Norm.DIN_EN_1991_1_4_2010_12] = NormErgebnis(
            status=status_1991,
            reasons=reasons_1991,
            werte={
                Nachweis.KIPP: sv_kipp,
                Nachweis.GLEIT: sv_gleit,
                Nachweis.ABHEBE: sv_abhebe,
            },
        )

    # Top-Level Ergebnis
    return StandsicherheitErgebnis(
        normen=normen,
        messages=[],
        meta=meta,
    )
