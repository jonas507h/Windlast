# datenstruktur/standsicherheit.py — Staudrücke+Nachweise klar getrennt

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Any, List, Dict, Literal
from enum import Enum
from dataclasses import asdict, is_dataclass
import json

from windlast_CORE.datenstruktur.enums import (
    Norm, Windzone, Betriebszustand, Schutzmassnahmen,
    RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben,
    VereinfachungKonstruktion, Nachweis, Severity, ValueSource, NormStatus,
)
from windlast_CORE.datenstruktur.zeit import Dauer
from windlast_CORE.datenstruktur.standsicherheit_ergebnis import (
    StandsicherheitErgebnis, NormErgebnis, SafetyValue, Message, Meta,
)
from windlast_CORE.rechenfunktionen.staudruecke import staudruecke  # type: ignore
from windlast_CORE.datenstruktur.zwischenergebnis import make_protokoll, collect_messages, merge_kontext, Protokoll

def dataclass_to_json(obj):
    """
    Wandelt verschachtelte Dataclasses in dicts um und ersetzt Enum-Werte durch .value.
    """
    if is_dataclass(obj):
        return {k: dataclass_to_json(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {dataclass_to_json(k): dataclass_to_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [dataclass_to_json(v) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    return obj

def save_ergebnis_to_file(ergebnis, pfad="ergebnis_dump.json"):
    from pathlib import Path
    import json
    Path(pfad).write_text(
        json.dumps(dataclass_to_json(ergebnis), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"✅ Ergebnis gespeichert unter: {Path(pfad).resolve()}")

# -----------------------------
# 1) Staudruck-Ermittlung
# -----------------------------
# Ein Szenario beschreibt „wie“ wir q/z holen (inkl. Label fürs UI/Output).
@dataclass(frozen=True)
class StaudruckSzenario:
    label: str                   # z.B. "AUSSER_BETRIEB", "IN_BETRIEB", "1991_ALTVERFAHREN"
    norm: Norm
    modus: Literal["betrieb", "schutz"]  # Auswahl der Parametrisierung
    betriebszustand: Optional[Betriebszustand] = None
    schutz: Optional[Schutzmassnahmen] = None
    windzone: Optional[Windzone] = None

def _ermittle_staudruecke(
    konstruktion: Any,
    s: StaudruckSzenario,
    *,
    aufstelldauer: Optional[Dauer],
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Tuple[Optional[List[float]], Optional[List[float]], List[Message]]:
    """
    Liefert (z, q, reasons). Kapselt staudruecke(...) inkl. robustem Fehlermanagement.
    z = Obergrenzen, q = Staudrücke, beide als List[float].
    """
    reasons: List[Message] = []
    base_ctx = merge_kontext(kontext, {"szenario": s.label, "norm": s.norm.name})
    try:
        if s.modus == "betrieb":
            zl1, zl2 = staudruecke(s.norm, konstruktion, s.betriebszustand, aufstelldauer=aufstelldauer, windzone=None, protokoll=protokoll, kontext=base_ctx)
        else:  # "schutz"
            zl1, zl2 = staudruecke(s.norm, konstruktion, s.schutz,           aufstelldauer=aufstelldauer, windzone=s.windzone, protokoll=protokoll, kontext=base_ctx)
        z = list(zl1.wert)  # Obergrenzen
        q = list(zl2.wert)  # Staudrücke
        return z, q, reasons
    except Exception as e:
        # Einheitliche Fehlercodes/Texte pro Normfamilie
        code = "STAUDRUECKE_FAILED" if s.label != "IN_BETRIEB" else "STAUDRUECKE_IN_BETRIEB_FAILED"
        sev  = Severity.ERROR if s.label not in ("IN_BETRIEB",) else Severity.WARN
        txt  = ("Geschwindigkeitsdruck/Obergrenze" if s.norm == Norm.DIN_EN_1991_1_4_2010_12
                else "Staudrücke/Obergrenzen")
        reasons.append(Message(
            code=code, severity=sev,
            text=f"{txt} ({s.norm.name}, {s.label}) fehlgeschlagen: {e}",
            context={},
        ))
        return None, None, reasons


# -----------------------------
# 2) Drei Nachweise + Ballast
# -----------------------------
def _rechne_drei_nachweise(
    konstruktion: Any,
    norm: Norm,
    q: List[float], z: List[float],
    *,
    konst: Optional[Any],
    meth_kipp: RechenmethodeKippen,
    meth_gleit: RechenmethodeGleiten,
    meth_abhebe: RechenmethodeAbheben,
    vereinfachung_konstruktion: VereinfachungKonstruktion,
    anzahl_windrichtungen: int,
    reasons: List[Message],
    norm_label: str,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Tuple[Dict[Nachweis, SafetyValue], Tuple[Optional[float], Optional[float], Optional[float]]]:
    base_ctx = merge_kontext(kontext, {"funktion": "_rechne_drei_nachweise", "norm": norm.name, "norm_label": norm_label})

    """
    Führt Kipp/Gleit/Abhebe durch (inkl. Fehlermeldungen im gleichen Stil wie bisher)
    und liefert SafetyValues + die drei Rohwerte (für Fallback-Trigger).
    """
    out: Dict[Nachweis, SafetyValue] = {}
    v_kipp = v_gleit = v_abhebe = None
    b_kipp = b_gleit = b_abhebe = None

    # Kipp
    try:
        r = konstruktion.berechne_kippsicherheit(
            norm, q, z, konst=konst, reset_berechnungen=True,
            methode=meth_kipp, vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            kontext=base_ctx,
        )
        v_kipp = float(r[0].wert); b_kipp = float(r[1].wert)
        out[Nachweis.KIPP] = SafetyValue(v_kipp, meth_kipp, ValueSource.COMPUTED, [])
    except Exception as e:
        reasons.append(Message(code="KIPP_FAILED", severity=Severity.ERROR,
                               text=f"Kippsicherheit ({norm_label}) fehlgeschlagen: {e}", context={}))
        out[Nachweis.KIPP] = SafetyValue(None, meth_kipp, ValueSource.ERROR, [])

    # Gleit
    try:
        r = konstruktion.berechne_gleitsicherheit(
            norm, q, z, konst=konst, reset_berechnungen=False,
            methode=meth_gleit, vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            kontext=base_ctx,
        )
        v_gleit = float(r[0].wert); b_gleit = float(r[1].wert)
        out[Nachweis.GLEIT] = SafetyValue(v_gleit, meth_gleit, ValueSource.COMPUTED, [])
    except Exception as e:
        reasons.append(Message(code="GLEIT_FAILED", severity=Severity.ERROR,
                               text=f"Gleitsicherheit ({norm_label}) fehlgeschlagen: {e}", context={}))
        out[Nachweis.GLEIT] = SafetyValue(None, meth_gleit, ValueSource.ERROR, [])

    # Abhebe
    try:
        r = konstruktion.berechne_abhebesicherheit(
            norm, q, z, konst=konst, reset_berechnungen=False,
            methode=meth_abhebe, vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            kontext=base_ctx,
        )
        v_abhebe = float(r[0].wert); b_abhebe = float(r[1].wert)
        out[Nachweis.ABHEBE] = SafetyValue(v_abhebe, meth_abhebe, ValueSource.COMPUTED, [])
    except Exception as e:
        reasons.append(Message(code="ABHEBE_FAILED", severity=Severity.ERROR,
                               text=f"Abhebesicherheit ({norm_label}) fehlgeschlagen: {e}", context={}))
        out[Nachweis.ABHEBE] = SafetyValue(None, meth_abhebe, ValueSource.ERROR, [])

    # Max-Ballast bilden
    ballast_vals = [b for b in (b_kipp, b_gleit, b_abhebe) if b is not None]
    out[Nachweis.BALLAST] = SafetyValue(
        wert=(max(ballast_vals) if ballast_vals else None),
        methode="MAX_BALLAST_KIPP_GLEIT_ABHEBE",
        source=ValueSource.COMPUTED if ballast_vals else ValueSource.ERROR,
        messages=[],
    )
    return out, (v_kipp, v_gleit, v_abhebe)


# -----------------------------
# 3) Top-Level Orchestrierung
# -----------------------------
def standsicherheit(
    konstruktion: Any,
    *,
    aufstelldauer: Optional[Dauer],
    windzone: Windzone,
    konst: Optional[Any] = None,
    methode: Optional[Tuple[RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben]] = None,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
) -> StandsicherheitErgebnis:
    """
    Rechnet Kipp-/Gleit-/Abhebesicherheit je Norm. Staudrücke/Alternativen laufen über Szenarien.
    """
    if methode is None:
        methode = (
            RechenmethodeKippen.STANDARD,
            RechenmethodeGleiten.MIN_REIBWERT,
            RechenmethodeAbheben.STANDARD,
        )
    meth_kipp, meth_gleit, meth_abhebe = methode

    meta = Meta(
        version="core-dev",
        inputs={
            "konstruktion_typ": konstruktion.__class__.__name__,
            "windzone": windzone.name,
            "aufstelldauer": (
                {"wert": aufstelldauer.wert, "einheit": aufstelldauer.einheit.name}
                if aufstelldauer is not None else None
            ),
        },
        methoden={Nachweis.KIPP: meth_kipp, Nachweis.GLEIT: meth_gleit, Nachweis.ABHEBE: meth_abhebe},
        vereinfachung_konstruktion=vereinfachung_konstruktion,
        anzahl_windrichtungen=anzahl_windrichtungen,
        konst_overrides={} if konst is None else {"custom": True},
    )

    normen: Dict[Norm, NormErgebnis] = {}

    # Helper zum Ausführen einer Norm mit beliebig vielen Szenarien
    def _rechne_norm(
        szenarien: List[StaudruckSzenario],
        *,
        normtitel: str,
    ) -> NormErgebnis:
        # Primär-Szenario ist szenarien[0]; alle weiteren werden als alternativen[...] abgelegt
        reasons_all: List[Message] = []
        prot = make_protokoll()

        # Primär
        s_primary = szenarien[0]
        z, q, reasons = _ermittle_staudruecke(konstruktion, s_primary, aufstelldauer=aufstelldauer, protokoll=prot, kontext={})
        reasons_all.extend(reasons)
        if z is None or q is None:
            # Ohne q/z: ERROR + Platzhalterwerte wie bisher
            return NormErgebnis(
                status=NormStatus.ERROR,
                reasons=reasons_all,
                werte={
                    Nachweis.KIPP:   SafetyValue(None, meth_kipp, ValueSource.ERROR, []),
                    Nachweis.GLEIT:  SafetyValue(None, meth_gleit, ValueSource.ERROR, []),
                    Nachweis.ABHEBE: SafetyValue(None, meth_abhebe, ValueSource.ERROR, []),
                    Nachweis.BALLAST: SafetyValue(None, "MAX_BALLAST_KIPP_GLEIT_ABHEBE", ValueSource.ERROR, []),
                },
            )

        werte, (v_kipp, v_gleit, v_abhebe) = _rechne_drei_nachweise(
            konstruktion, szenarien[0].norm, q, z,
            konst=konst, meth_kipp=meth_kipp, meth_gleit=meth_gleit, meth_abhebe=meth_abhebe,
            vereinfachung_konstruktion=vereinfachung_konstruktion, anzahl_windrichtungen=anzahl_windrichtungen,
            reasons=reasons_all, norm_label=normtitel,
            protokoll=prot, kontext={"szenario": s_primary.label},
        )

        alternativen: Dict[str, Dict[Nachweis, SafetyValue]] = {}
        # Fallback nur versuchen, wenn eine Sicherheit < 1 oder wenn man sie immer anbieten will
        need_fallback = any(v is not None and v < 1.0 for v in (v_kipp, v_gleit, v_abhebe))

        if need_fallback and len(szenarien) > 1:
            for s in szenarien[1:]:
                z_b, q_b, reasons_b = _ermittle_staudruecke(konstruktion, s, aufstelldauer=aufstelldauer, protokoll=prot, kontext={})
                reasons_all.extend(reasons_b)
                if z_b is None or q_b is None:
                    # Wenn Staudrücke fürs Fallback nicht verfügbar, einfach überspringen (Reasons sind geloggt)
                    continue
                vals_b, _ = _rechne_drei_nachweise(
                    konstruktion, s.norm, q_b, z_b,
                    konst=konst, meth_kipp=meth_kipp, meth_gleit=meth_gleit, meth_abhebe=meth_abhebe,
                    vereinfachung_konstruktion=vereinfachung_konstruktion, anzahl_windrichtungen=anzahl_windrichtungen,
                    reasons=reasons_all, norm_label=f"{s.norm.name} ({s.label})",
                    protokoll=prot, kontext={"szenario": s.label},
                )
                alternativen[s.label] = vals_b

        try:
            reasons_all.extend(collect_messages(prot))
        except Exception:
            pass

        status = NormStatus.ERROR if any(m.severity == Severity.ERROR for m in reasons_all) else NormStatus.CALCULATED
        return NormErgebnis(status=status, reasons=reasons_all, werte=werte, alternativen=alternativen)

    # --------------------------
    # DIN EN 13814:2005-06
    # --------------------------
    normen[Norm.DIN_EN_13814_2005_06] = _rechne_norm(
        [
            StaudruckSzenario("AUSSER_BETRIEB", Norm.DIN_EN_13814_2005_06, modus="betrieb",
                            betriebszustand=Betriebszustand.AUSSER_BETRIEB),
            StaudruckSzenario("IN_BETRIEB",     Norm.DIN_EN_13814_2005_06, modus="betrieb",
                            betriebszustand=Betriebszustand.IN_BETRIEB),
        ],
        normtitel="DIN EN 13814:2005-06",
    )

    # --------------------------
    # DIN EN 17879:2024-08
    # --------------------------
    normen[Norm.DIN_EN_17879_2024_08] = _rechne_norm(
        [
            StaudruckSzenario("AUSSER_BETRIEB", Norm.DIN_EN_17879_2024_08, modus="betrieb",
                            betriebszustand=Betriebszustand.AUSSER_BETRIEB),
            StaudruckSzenario("IN_BETRIEB",     Norm.DIN_EN_17879_2024_08, modus="betrieb",
                            betriebszustand=Betriebszustand.IN_BETRIEB),
        ],
        normtitel="DIN EN 17879:2024-08",
    )

    # --------------------------
    # DIN EN 1991-1-4:2010-12
    # --------------------------
    normen[Norm.DIN_EN_1991_1_4_2010_12] = _rechne_norm(
        [
            StaudruckSzenario("STANDARD", Norm.DIN_EN_1991_1_4_2010_12, modus="schutz",
                            schutz=Schutzmassnahmen.KEINE, windzone=windzone),
            # weitere Fallback-Verfahren hier einfach anhängen:
            # StaudruckSzenario("ALTVERFAHREN_XYZ", Norm.DIN_EN_1991_1_4_2010_12, modus="schutz",
            #                   schutz=Schutzmassnahmen.KEINE, windzone=windzone),
        ],
        normtitel="DIN EN 1991-1-4:2010-12",
    )

    # Ergebnis speichern (Debug)
    # save_ergebnis_to_file(StandsicherheitErgebnis(normen=normen, messages=[], meta=meta))

    return StandsicherheitErgebnis(normen=normen, messages=[], meta=meta)
