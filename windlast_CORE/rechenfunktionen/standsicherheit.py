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
                Nachweis.BALLAST: SafetyValue(None, "MAX_BALLAST_KIPP_GLEIT_ABHEBE", ValueSource.ERROR, []),
            },
        )
    else:
        ballast_kipp = ballast_gleit = ballast_abhebe = None
        v_kipp = v_gleit = v_abhebe = None
        # drei Nachweise
        # Kipp
        try:
            r_kipp = konstruktion.berechne_kippsicherheit(
                Norm.DIN_EN_13814_2005_06, q_13814, z_13814,
                konst=konst, reset_berechnungen=True,
                methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_kipp = float(r_kipp[0].wert)
            ballast_kipp = float(r_kipp[1].wert)
            sv_kipp = SafetyValue(v_kipp, meth_kipp, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_13814.append(Message(
                code="KIPP_FAILED",
                severity=Severity.ERROR,
                text=f"Kippsicherheit (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
                context={},
            ))
            sv_kipp = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])
            ballast_kipp = None

        # Gleit
        try:
            r_gleit = konstruktion.berechne_gleitsicherheit(
                Norm.DIN_EN_13814_2005_06, q_13814, z_13814,
                konst=konst, reset_berechnungen=False,
                methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_gleit = float(r_gleit[0].wert)
            ballast_gleit = float(r_gleit[1].wert)
            sv_gleit = SafetyValue(v_gleit, meth_gleit, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_13814.append(Message(
                code="GLEIT_FAILED",
                severity=Severity.ERROR,
                text=f"Gleitsicherheit (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
                context={},
            ))
            sv_gleit = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])
            ballast_gleit = None

        # Abhebe
        try:
            r_abhebe = konstruktion.berechne_abhebesicherheit(
                Norm.DIN_EN_13814_2005_06, q_13814, z_13814,
                konst=konst, reset_berechnungen=False,
                methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_abhebe = float(r_abhebe[0].wert)
            ballast_abhebe = float(r_abhebe[1].wert)
            sv_abhebe = SafetyValue(v_abhebe, meth_abhebe, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_13814.append(Message(
                code="ABHEBE_FAILED",
                severity=Severity.ERROR,
                text=f"Abhebesicherheit (DIN EN 13814:2005-06) fehlgeschlagen: {e}",
                context={},
            ))
            sv_abhebe = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])
            ballast_abhebe = None

        status_13814 = NormStatus.ERROR if reasons_13814 else NormStatus.CALCULATED

        # max-Ballast (kg) bilden – nur vorhandene Werte berücksichtigen
        ballast_vals = [b for b in (ballast_kipp, ballast_gleit, ballast_abhebe) if b is not None]
        sv_ballast = SafetyValue(
            wert=(max(ballast_vals) if ballast_vals else None),
            methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
            source=ValueSource.COMPUTED if ballast_vals else ValueSource.ERROR,
            messages=[],
        )

        # --- Fallback IN_BETRIEB, falls eine Sicherheit < 1 ---
        alternativen_13814: Dict[str, Dict[Nachweis, SafetyValue]] = {}  # << TYP angepasst
        try_in_betrieb = any((x is not None and x < 1.0) for x in (v_kipp, v_gleit, v_abhebe))

        if try_in_betrieb:
            try:
                zl1_b, zl2_b = staudruecke(
                    Norm.DIN_EN_13814_2005_06,
                    konstruktion,
                    Betriebszustand.IN_BETRIEB,
                    aufstelldauer=aufstelldauer,
                    windzone=None,
                )
                z_b = list(zl1_b.wert)
                q_b = list(zl2_b.wert)

                vals_b: Dict[Nachweis, SafetyValue] = {}  # << TYP angepasst
                b_kipp = b_gleit = b_abhebe = None

                # Kipp (reset True, analog Hauptrechnung)
                try:
                    r = konstruktion.berechne_kippsicherheit(
                        Norm.DIN_EN_13814_2005_06, q_b, z_b,
                        konst=konst, reset_berechnungen=True,
                        methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                        anzahl_windrichtungen=anzahl_windrichtungen,
                    )
                    vals_b[Nachweis.KIPP] = SafetyValue(float(r[0].wert), meth_kipp, ValueSource.COMPUTED, [])
                    b_kipp = float(r[1].wert)
                except Exception as e:
                    reasons_13814.append(Message(
                        code="KIPP_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                        text=f"Kipp (IN_BETRIEB, 13814) fehlgeschlagen: {e}", context={}
                    ))
                    vals_b[Nachweis.KIPP] = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])
                    b_kipp = None

                # Gleit
                try:
                    r = konstruktion.berechne_gleitsicherheit(
                        Norm.DIN_EN_13814_2005_06, q_b, z_b,
                        konst=konst, reset_berechnungen=False,
                        methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                        anzahl_windrichtungen=anzahl_windrichtungen,
                    )
                    vals_b[Nachweis.GLEIT] = SafetyValue(float(r[0].wert), meth_gleit, ValueSource.COMPUTED, [])
                    b_gleit = float(r[1].wert)
                except Exception as e:
                    reasons_13814.append(Message(
                        code="GLEIT_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                        text=f"Gleit (IN_BETRIEB, 13814) fehlgeschlagen: {e}", context={}
                    ))
                    vals_b[Nachweis.GLEIT] = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])
                    b_gleit = None

                # Abhebe
                try:
                    r = konstruktion.berechne_abhebesicherheit(
                        Norm.DIN_EN_13814_2005_06, q_b, z_b,
                        konst=konst, reset_berechnungen=False,
                        methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                        anzahl_windrichtungen=anzahl_windrichtungen,
                    )
                    vals_b[Nachweis.ABHEBE] = SafetyValue(float(r[0].wert), meth_abhebe, ValueSource.COMPUTED, [])
                    b_abhebe = float(r[1].wert)
                except Exception as e:
                    reasons_13814.append(Message(
                        code="ABHEBE_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                        text=f"Abhebe (IN_BETRIEB, 13814) fehlgeschlagen: {e}", context={}
                    ))
                    vals_b[Nachweis.ABHEBE] = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])
                    b_abhebe = None

                # Ballast (kg) für Alternative bilden
                bc = [b for b in (b_kipp, b_gleit, b_abhebe) if b is not None]
                vals_b[Nachweis.BALLAST] = SafetyValue(
                    wert=(max(bc) if bc else None),
                    methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
                    source=ValueSource.COMPUTED if bc else ValueSource.ERROR,
                    messages=[],
                )

                alternativen_13814["IN_BETRIEB"] = vals_b

            except Exception as e:
                reasons_13814.append(Message(
                    code="STAUDRUECKE_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                    text=f"Staudrücke (IN_BETRIEB, 13814) fehlgeschlagen: {e}", context={}
                ))

        normen[Norm.DIN_EN_13814_2005_06] = NormErgebnis(
            status=status_13814,
            reasons=reasons_13814,
            werte={
                Nachweis.KIPP: sv_kipp,
                Nachweis.GLEIT: sv_gleit,
                Nachweis.ABHEBE: sv_abhebe,
                Nachweis.BALLAST: sv_ballast,
            },
            alternativen=alternativen_13814,
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
                Nachweis.BALLAST: SafetyValue(None, "MAX_BALLAST_KIPP_GLEIT_ABHEBE", ValueSource.ERROR, []),
            },
        )
    else:
        ballast_kipp = ballast_gleit = ballast_abhebe = None
        v_kipp = v_gleit = v_abhebe = None
        # drei Nachweise
        # Kipp
        try:
            r_kipp = konstruktion.berechne_kippsicherheit(
                Norm.DIN_EN_17879_2024_08, q_17879, z_17879,
                konst=konst, reset_berechnungen=True,
                methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_kipp = float(r_kipp[0].wert)
            ballast_kipp = float(r_kipp[1].wert)
            sv_kipp = SafetyValue(v_kipp, meth_kipp, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_17879.append(Message(
                code="KIPP_FAILED",
                severity=Severity.ERROR,
                text=f"Kippsicherheit (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
                context={},
            ))
            sv_kipp = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])
            ballast_kipp = None

        # Gleit
        try:
            r_gleit = konstruktion.berechne_gleitsicherheit(
                Norm.DIN_EN_17879_2024_08, q_17879, z_17879,
                konst=konst, reset_berechnungen=False,
                methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_gleit = float(r_gleit[0].wert)
            ballast_gleit = float(r_gleit[1].wert)
            sv_gleit = SafetyValue(v_gleit, meth_gleit, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_17879.append(Message(
                code="GLEIT_FAILED",
                severity=Severity.ERROR,
                text=f"Gleitsicherheit (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
                context={},
            ))
            sv_gleit = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])
            ballast_gleit = None

        # Abhebe
        try:
            r_abhebe = konstruktion.berechne_abhebesicherheit(
                Norm.DIN_EN_17879_2024_08, q_17879, z_17879,
                konst=konst, reset_berechnungen=False,
                methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_abhebe = float(r_abhebe[0].wert)
            ballast_abhebe = float(r_abhebe[1].wert)
            sv_abhebe = SafetyValue(v_abhebe, meth_abhebe, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_17879.append(Message(
                code="ABHEBE_FAILED",
                severity=Severity.ERROR,
                text=f"Abhebesicherheit (DIN EN 17879:2024-08) fehlgeschlagen: {e}",
                context={},
            ))
            sv_abhebe = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])
            ballast_abhebe = None

        status_17879 = NormStatus.ERROR if reasons_17879 else NormStatus.CALCULATED
        # max-Ballast (kg) bilden – nur vorhandene Werte berücksichtigen
        ballast_vals = [b for b in (ballast_kipp, ballast_gleit, ballast_abhebe) if b is not None]
        sv_ballast = SafetyValue(
            wert=(max(ballast_vals) if ballast_vals else None),
            methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
            source=ValueSource.COMPUTED if ballast_vals else ValueSource.ERROR,
            messages=[],
        )

        # --- Fallback IN_BETRIEB, falls eine Sicherheit < 1 ---
        alternativen_17879: Dict[str, Dict[Nachweis, SafetyValue]] = {}  # ← TYP: SafetyValue
        try_in_betrieb = any((x is not None and x < 1.0) for x in (v_kipp, v_gleit, v_abhebe))

        if try_in_betrieb:
            try:
                zl1_b, zl2_b = staudruecke(
                    Norm.DIN_EN_17879_2024_08,
                    konstruktion,
                    Betriebszustand.IN_BETRIEB,
                    aufstelldauer=aufstelldauer,
                    windzone=None,
                )
                z_b = list(zl1_b.wert)
                q_b = list(zl2_b.wert)

                vals_b: Dict[Nachweis, SafetyValue] = {}  # ← TYP: SafetyValue
                b_kipp = b_gleit = b_abhebe = None

                # Kipp
                try:
                    r = konstruktion.berechne_kippsicherheit(
                        Norm.DIN_EN_17879_2024_08, q_b, z_b,
                        konst=konst, reset_berechnungen=True,
                        methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                        anzahl_windrichtungen=anzahl_windrichtungen,
                    )
                    vals_b[Nachweis.KIPP] = SafetyValue(float(r[0].wert), meth_kipp, ValueSource.COMPUTED, [])
                    b_kipp = float(r[1].wert)
                except Exception as e:
                    reasons_17879.append(Message(
                        code="KIPP_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                        text=f"Kipp (IN_BETRIEB, 17879) fehlgeschlagen: {e}", context={}
                    ))
                    vals_b[Nachweis.KIPP] = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])
                    b_kipp = None

                # Gleit
                try:
                    r = konstruktion.berechne_gleitsicherheit(
                        Norm.DIN_EN_17879_2024_08, q_b, z_b,
                        konst=konst, reset_berechnungen=False,
                        methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                        anzahl_windrichtungen=anzahl_windrichtungen,
                    )
                    vals_b[Nachweis.GLEIT] = SafetyValue(float(r[0].wert), meth_gleit, ValueSource.COMPUTED, [])
                    b_gleit = float(r[1].wert)
                except Exception as e:
                    reasons_17879.append(Message(
                        code="GLEIT_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                        text=f"Gleit (IN_BETRIEB, 17879) fehlgeschlagen: {e}", context={}
                    ))
                    vals_b[Nachweis.GLEIT] = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])
                    b_gleit = None

                # Abhebe
                try:
                    r = konstruktion.berechne_abhebesicherheit(
                        Norm.DIN_EN_17879_2024_08, q_b, z_b,
                        konst=konst, reset_berechnungen=False,
                        methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                        anzahl_windrichtungen=anzahl_windrichtungen,
                    )
                    vals_b[Nachweis.ABHEBE] = SafetyValue(float(r[0].wert), meth_abhebe, ValueSource.COMPUTED, [])
                    b_abhebe = float(r[1].wert)
                except Exception as e:
                    reasons_17879.append(Message(
                        code="ABHEBE_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                        text=f"Abhebe (IN_BETRIEB, 17879) fehlgeschlagen: {e}", context={}
                    ))
                    vals_b[Nachweis.ABHEBE] = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])
                    b_abhebe = None

                # Ballast (kg) für Alternative bilden (max über Teil-Ballaste)
                bc = [b for b in (b_kipp, b_gleit, b_abhebe) if b is not None]
                vals_b[Nachweis.BALLAST] = SafetyValue(
                    wert=(max(bc) if bc else None),
                    methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
                    source=ValueSource.COMPUTED if bc else ValueSource.ERROR,
                    messages=[],
                )

                alternativen_17879["IN_BETRIEB"] = vals_b

            except Exception as e:
                reasons_17879.append(Message(
                    code="STAUDRUECKE_IN_BETRIEB_FAILED", severity=Severity.WARNING,
                    text=f"Staudrücke (IN_BETRIEB, 17879) fehlgeschlagen: {e}", context={}
                ))


        normen[Norm.DIN_EN_17879_2024_08] = NormErgebnis(
            status=status_17879,
            reasons=reasons_17879,
            werte={
                Nachweis.KIPP: sv_kipp,
                Nachweis.GLEIT: sv_gleit,
                Nachweis.ABHEBE: sv_abhebe,
                Nachweis.BALLAST: sv_ballast,
            },
            alternativen=alternativen_17879,
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
                Nachweis.BALLAST: SafetyValue(None, "MAX_BALLAST_KIPP_GLEIT_ABHEBE", ValueSource.ERROR, []),
            },
        )
    else:
        ballast_kipp = ballast_gleit = ballast_abhebe = None
        v_kipp = v_gleit = v_abhebe = None
        # drei Nachweise
        # Kipp
        try:
            r_kipp = konstruktion.berechne_kippsicherheit(
                Norm.DIN_EN_1991_1_4_2010_12, q_1991, z_1991,
                konst=konst, reset_berechnungen=True,
                methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_kipp = float(r_kipp[0].wert)
            ballast_kipp = float(r_kipp[1].wert)
            sv_kipp = SafetyValue(v_kipp, meth_kipp, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_1991.append(Message(
                code="KIPP_FAILED",
                severity=Severity.ERROR,
                text=f"Kippsicherheit (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
                context={},
            ))
            sv_kipp = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])
            ballast_kipp = None

        # Gleit
        try:
            r_gleit = konstruktion.berechne_gleitsicherheit(
                Norm.DIN_EN_1991_1_4_2010_12, q_1991, z_1991,
                konst=konst, reset_berechnungen=False,
                methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_gleit = float(r_gleit[0].wert)
            ballast_gleit = float(r_gleit[1].wert)
            sv_gleit = SafetyValue(v_gleit, meth_gleit, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_1991.append(Message(
                code="GLEIT_FAILED",
                severity=Severity.ERROR,
                text=f"Gleitsicherheit (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
                context={},
            ))
            sv_gleit = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])
            ballast_gleit = None

        # Abhebe
        try:
            r_abhebe = konstruktion.berechne_abhebesicherheit(
                Norm.DIN_EN_1991_1_4_2010_12, q_1991, z_1991,
                konst=konst, reset_berechnungen=False,
                methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
                anzahl_windrichtungen=anzahl_windrichtungen,
            )
            v_abhebe = float(r_abhebe[0].wert)
            ballast_abhebe = float(r_abhebe[1].wert)
            sv_abhebe = SafetyValue(v_abhebe, meth_abhebe, ValueSource.COMPUTED, [])
        except Exception as e:
            reasons_1991.append(Message(
                code="ABHEBE_FAILED",
                severity=Severity.ERROR,
                text=f"Abhebesicherheit (DIN EN 1991-1-4:2010-12) fehlgeschlagen: {e}",
                context={},
            ))
            sv_abhebe = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])
            ballast_abhebe = None

        status_1991 = NormStatus.ERROR if reasons_1991 else NormStatus.CALCULATED
        # max-Ballast (kg) bilden – nur vorhandene Werte berücksichtigen
        ballast_vals = [b for b in (ballast_kipp, ballast_gleit, ballast_abhebe) if b is not None]
        sv_ballast = SafetyValue(
            wert=(max(ballast_vals) if ballast_vals else None),
            methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
            source=ValueSource.COMPUTED if ballast_vals else ValueSource.ERROR,
            messages=[],
        )

        normen[Norm.DIN_EN_1991_1_4_2010_12] = NormErgebnis(
            status=status_1991,
            reasons=reasons_1991,
            werte={
                Nachweis.KIPP: sv_kipp,
                Nachweis.GLEIT: sv_gleit,
                Nachweis.ABHEBE: sv_abhebe,
                Nachweis.BALLAST: sv_ballast,
            },
        )

    # Top-Level Ergebnis
    return StandsicherheitErgebnis(
        normen=normen,
        messages=[],
        meta=meta,
    )
