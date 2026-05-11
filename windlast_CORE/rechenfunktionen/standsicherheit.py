# datenstruktur/standsicherheit.py

from dataclasses import dataclass, asdict, is_dataclass
from typing import Optional, Tuple, Any, List, Literal
from enum import Enum
import json

from windlast_CORE.datenstruktur.enums import (
    Norm, Windzone, Betriebszustand, Schutzmassnahmen,
    RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben,
    VereinfachungKonstruktion, Nachweis, Severity, Zeitfaktor
)
from windlast_CORE.datenstruktur.zeit import Dauer, convert_dauer
from windlast_CORE.rechenfunktionen.staudruecke import staudruecke
from windlast_CORE.datenstruktur.zwischenergebnis import (
    make_protokoll,
    collect_tree,
    merge_breadcrumb,
    bc_step,
    Protokoll,
    ErgebnisBaum,
    protokolliere_ergebnis,
    protokolliere_msg,
    set_winner,
)

from windlast_CORE.rechenfunktionen.DEBUG_ergebnisobjekt import debug_tree

# def _tree_to_jsonable(obj):
#     if is_dataclass(obj):
#         return {k: _tree_to_jsonable(v) for k, v in asdict(obj).items()}
#     if isinstance(obj, Enum):
#         return obj.value
#     if isinstance(obj, dict):
#         return {
#             str(_tree_to_jsonable(k)): _tree_to_jsonable(v)
#             for k, v in obj.items()
#         }
#     if isinstance(obj, (list, tuple)):
#         return [_tree_to_jsonable(v) for v in obj]
#     return obj


# def save_tree_to_file(tree: ErgebnisBaum, pfad: str = "ergebnisbaum_dump.json") -> None:
#     from pathlib import Path

#     Path(pfad).write_text(
#         json.dumps(_tree_to_jsonable(tree), indent=2, ensure_ascii=False),
#         encoding="utf-8",
#     )
#     print(f"✅ Ergebnisbaum gespeichert unter: {Path(pfad).resolve()}")

# -----------------------------
# 1) Staudruck-Ermittlung
# -----------------------------
# Ein Szenario beschreibt „wie“ wir q/z holen (inkl. Label fürs UI/Output).
@dataclass(frozen=True)
class StaudruckSzenario:
    label: str                   # z.B. "AUSSER_BETRIEB", "IN_BETRIEB", "1991_ALTVERFAHREN"
    anzeigename: str
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
    breadcrumb: Optional[list] = None,
) -> Tuple[Optional[List[float]], Optional[List[float]]]:

    loads_bc = merge_breadcrumb(
        breadcrumb,
        [bc_step("kraefte", "windkraefte", ebene_label="Kräfte", gruppe_label="Windkräfte")]
    )

    try:
        # TODO: Warum??? was ist s.modus?
        if s.modus == "betrieb":
            zl1, zl2 = staudruecke(
                s.norm, konstruktion, s.betriebszustand,
                aufstelldauer=aufstelldauer,
                windzone=s.windzone,
                protokoll=protokoll,
                breadcrumb=loads_bc,
            )
        else:
            zl1, zl2 = staudruecke(
                s.norm, konstruktion, s.schutz,
                aufstelldauer=aufstelldauer,
                windzone=s.windzone,
                protokoll=protokoll,
                breadcrumb=loads_bc,
            )

        z = list(zl1.wert)
        q = list(zl2.wert)

        if any(isinstance(v, float) and v != v for v in z + q):
            protokolliere_msg(
                protokoll,
                breadcrumb=loads_bc,
                severity=Severity.ERROR,
                code="STAUDRUECKE_NAN",
                text=f"Staudrücke/Obergrenzen ({s.norm.name}, {s.label}) enthalten NaN.",
            )
            return None, None

        return z, q

    except Exception as e:
        code = "STAUDRUECKE_FAILED" if s.label != "IN_BETRIEB" else "STAUDRUECKE_IN_BETRIEB_FAILED"
        sev = Severity.ERROR if s.label != "IN_BETRIEB" else Severity.WARN

        protokolliere_msg(
            protokoll,
            breadcrumb=loads_bc,
            severity=sev,
            code=code,
            text=f"Staudrücke/Obergrenzen ({s.norm.name}, {s.label}) fehlgeschlagen: {e}",
        )
        return None, None


# -----------------------------
# 2) Drei Nachweise + Ballast
# -----------------------------
def _rechne_drei_nachweise(
    konstruktion: Any,
    norm: Norm,
    q: List[float],
    z: List[float],
    *,
    konst: Optional[Any],
    meth_kipp: RechenmethodeKippen,
    meth_gleit: RechenmethodeGleiten,
    meth_abhebe: RechenmethodeAbheben,
    vereinfachung_konstruktion: VereinfachungKonstruktion,
    anzahl_windrichtungen: int,
    norm_label: str,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    
    loads_bc = merge_breadcrumb(
        breadcrumb,
        [bc_step("kraefte", "windkraefte", ebene_label="Kräfte", gruppe_label="Windkräfte")]
    )

    v_kipp = v_gleit = v_abhebe = None
    b_kipp = b_gleit = b_abhebe = None

    kipp_bc = merge_breadcrumb(
        breadcrumb,
        [bc_step("sicherheiten", "KIPP", ebene_label="Sicherheiten", gruppe_label="Kippsicherheit")]
    )
    try:
        r = konstruktion.berechne_kippsicherheit(
            norm, q, z,
            konst=konst,
            reset_berechnungen=True,
            methode=meth_kipp,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            breadcrumb=kipp_bc,
            loads_breadcrumb=loads_bc,
        )
        v_kipp = float(r[0].wert)
        b_kipp = float(r[1].wert)

        # protokolliere_ergebnis(
        #     protokoll,
        #     breadcrumb=kipp_bc,
        #     name="kippsicherheit",
        #     label="Kippsicherheit",
        #     formelzeichen="S_kipp",
        #     wert=v_kipp,
        #     priority=10,
        # )
        # protokolliere_ergebnis(
        #     protokoll,
        #     breadcrumb=kipp_bc,
        #     name="ballast_kipp",
        #     label="Erforderlicher Ballast aus Kippen",
        #     formelzeichen="m_Ballast,kipp",
        #     wert=b_kipp,
        #     einheit="kg",
        #     priority=10,
        # )
    except Exception as e:
        protokolliere_msg(
            protokoll,
            breadcrumb=kipp_bc,
            severity=Severity.ERROR,
            code="KIPP_FAILED",
            text=f"Kippsicherheit ({norm_label}) fehlgeschlagen: {e}",
        )

    gleit_bc = merge_breadcrumb(
        breadcrumb,
        [bc_step("sicherheiten", "GLEIT", ebene_label="Sicherheiten", gruppe_label="Gleitsicherheit")]
    )
    try:
        r = konstruktion.berechne_gleitsicherheit(
            norm, q, z,
            konst=konst,
            reset_berechnungen=False,
            methode=meth_gleit,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            breadcrumb=gleit_bc,
            loads_breadcrumb=loads_bc,
        )
        v_gleit = float(r[0].wert)
        b_gleit = float(r[1].wert)

        # protokolliere_ergebnis(
        #     protokoll,
        #     breadcrumb=gleit_bc,
        #     name="gleitsicherheit",
        #     label="Gleitsicherheit",
        #     formelzeichen="S_gleit",
        #     wert=v_gleit,
        #     priority=10,
        # )
        # protokolliere_ergebnis(
        #     protokoll,
        #     breadcrumb=gleit_bc,
        #     name="ballast_gleit",
        #     label="Erforderlicher Ballast aus Gleiten",
        #     formelzeichen="m_Ballast,gleit",
        #     wert=b_gleit,
        #     einheit="kg",
        #     priority=10,
        # )
    except Exception as e:
        protokolliere_msg(
            protokoll,
            breadcrumb=gleit_bc,
            severity=Severity.ERROR,
            code="GLEIT_FAILED",
            text=f"Gleitsicherheit ({norm_label}) fehlgeschlagen: {e}",
        )

    abhebe_bc = merge_breadcrumb(
        breadcrumb,
        [bc_step("sicherheiten", "ABHEBE", ebene_label="Sicherheiten", gruppe_label="Abhebesicherheit")]
    )
    try:
        r = konstruktion.berechne_abhebesicherheit(
            norm, q, z,
            konst=konst,
            reset_berechnungen=False,
            methode=meth_abhebe,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            breadcrumb=abhebe_bc,
            loads_breadcrumb=loads_bc,
        )
        v_abhebe = float(r[0].wert)
        b_abhebe = float(r[1].wert)

        # protokolliere_ergebnis(
        #     protokoll,
        #     breadcrumb=abhebe_bc,
        #     name="abhebesicherheit",
        #     label="Abhebesicherheit",
        #     formelzeichen="S_abhebe",
        #     wert=v_abhebe,
        #     priority=10,
        # )
        # protokolliere_ergebnis(
        #     protokoll,
        #     breadcrumb=abhebe_bc,
        #     name="ballast_abhebe",
        #     label="Erforderlicher Ballast aus Abheben",
        #     formelzeichen="m_Ballast,abhebe",
        #     wert=b_abhebe,
        #     einheit="kg",
        #     priority=10,
        # )
    except Exception as e:
        protokolliere_msg(
            protokoll,
            breadcrumb=abhebe_bc,
            severity=Severity.ERROR,
            code="ABHEBE_FAILED",
            text=f"Abhebesicherheit ({norm_label}) fehlgeschlagen: {e}",
        )

    ballast_pairs: list[tuple[Nachweis, float]] = []
    if b_kipp is not None:
        ballast_pairs.append((Nachweis.KIPP, b_kipp))
    if b_gleit is not None:
        ballast_pairs.append((Nachweis.GLEIT, b_gleit))
    if b_abhebe is not None:
        ballast_pairs.append((Nachweis.ABHEBE, b_abhebe))

    ballast_bc = breadcrumb

    if ballast_pairs:
        ballast_quelle, ballast_wert = max(ballast_pairs, key=lambda p: p[1])

        if ballast_quelle.name == "KIPP":
            ballast_winner_bc = kipp_bc
        elif ballast_quelle.name == "GLEIT":
            ballast_winner_bc = gleit_bc
        elif ballast_quelle.name == "ABHEBE":
            ballast_winner_bc = abhebe_bc

        # for quelle, wert in ballast_pairs:
        #     quelle_bc = merge_breadcrumb(
        #         ballast_bc,
        #         [bc_step("quelle_nachweis", quelle.name, ebene_label="Quelle Nachweis", gruppe_label=quelle.name)]
        #     )
        #     protokolliere_ergebnis(
        #         protokoll,
        #         breadcrumb=quelle_bc,
        #         name="ballast_kandidat",
        #         label=f"Ballast-Kandidat {quelle.name}",
        #         formelzeichen=f"m_Ballast,{quelle.name.lower()}",
        #         wert=wert,
        #         einheit="kg",
        #         priority=5,
        #     )

        set_winner(
            protokoll,
            ballast_winner_bc,
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=ballast_bc,
            name="ballast_max",
            label="Erforderlicher Ballast",
            formelzeichen="m_Ballast,max",
            wert=ballast_wert,
            einheit="kg",
            formel="m_Ballast,max = max(m_Ballast,kipp, m_Ballast,gleit, m_Ballast,abheb)",
            priority=10,
        )

    return v_kipp, v_gleit, v_abhebe


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
    anzahl_windrichtungen: int = 8,
) -> ErgebnisBaum:
    """
    Rechnet Kipp-/Gleit-/Abhebesicherheit je Norm. Staudrücke/Alternativen laufen über Szenarien.
    """
    prot = make_protokoll()
    if methode is None:
        methode = (
            RechenmethodeKippen.STANDARD,
            RechenmethodeGleiten.MIN_REIBWERT,
            RechenmethodeAbheben.STANDARD,
        )
    meth_kipp, meth_gleit, meth_abhebe = methode

    # Helper zum Ausführen einer Norm mit beliebig vielen Szenarien
    def _rechne_norm(
        szenarien: List[StaudruckSzenario],
        *,
        normtitel: str,
        allow_alternativen: bool = True,
    ) -> None:
        # Primär
        s_primary = szenarien[0]

        primary_bc = [
            bc_step("norm", s_primary.norm.name, ebene_label="Norm", gruppe_label=normtitel),
            bc_step("szenario", s_primary.label, ebene_label="Szenario", gruppe_label=s_primary.anzeigename),
        ]

        z, q = _ermittle_staudruecke(
            konstruktion,
            s_primary,
            aufstelldauer=aufstelldauer,
            protokoll=prot,
            breadcrumb=primary_bc,
        )

        if z is None or q is None:
            protokolliere_msg(
                prot,
                breadcrumb=primary_bc,
                severity=Severity.ERROR,
                code="NORM_FAILED",
                text=f"{normtitel}: Berechnung abgebrochen, weil Staudrücke/Obergrenzen fehlen.",
            )
            return

        v_kipp, v_gleit, v_abhebe = _rechne_drei_nachweise(
            konstruktion,
            s_primary.norm,
            q,
            z,
            konst=konst,
            meth_kipp=meth_kipp,
            meth_gleit=meth_gleit,
            meth_abhebe=meth_abhebe,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            norm_label=normtitel,
            protokoll=prot,
            breadcrumb=primary_bc,
        )

        need_fallback = any(v is not None and v < 1.0 for v in (v_kipp, v_gleit, v_abhebe))

        if need_fallback and len(szenarien) > 1 and allow_alternativen:
            for s in szenarien[1:]:
                alt_bc = [
                    bc_step("norm", s.norm.name, ebene_label="Norm", gruppe_label=normtitel),
                    bc_step("szenario", s.label, ebene_label="Szenario", gruppe_label=s.anzeigename),
                ]

                z_b, q_b = _ermittle_staudruecke(
                    konstruktion,
                    s,
                    aufstelldauer=aufstelldauer,
                    protokoll=prot,
                    breadcrumb=alt_bc,
                )

                if z_b is None or q_b is None:
                    protokolliere_msg(
                        prot,
                        breadcrumb=alt_bc,
                        severity=Severity.WARN,
                        code="ALTERNATIVE_SKIPPED",
                        text=f"Alternative {s.anzeigename} übersprungen, weil Staudrücke/Obergrenzen fehlen.",
                    )
                    continue

                _rechne_drei_nachweise(
                    konstruktion,
                    s.norm,
                    q_b,
                    z_b,
                    konst=konst,
                    meth_kipp=meth_kipp,
                    meth_gleit=meth_gleit,
                    meth_abhebe=meth_abhebe,
                    vereinfachung_konstruktion=vereinfachung_konstruktion,
                    anzahl_windrichtungen=anzahl_windrichtungen,
                    norm_label=f"{s.norm.name} ({s.label})",
                    protokoll=prot,
                    breadcrumb=alt_bc,
                )
        return
    
    aufstelldauer_monate = convert_dauer(aufstelldauer.wert, aufstelldauer.einheit, Zeitfaktor.MONAT) if aufstelldauer else None
    allow_alternativen_1991 = (aufstelldauer_monate is not None and aufstelldauer_monate <= 24.0)

    # --------------------------
    # DIN EN 13814:2005-06
    # --------------------------
    _rechne_norm(
        [
            StaudruckSzenario("AUSSER_BETRIEB", "Außer Betrieb", Norm.DIN_EN_13814_2005_06, modus="betrieb",
                            betriebszustand=Betriebszustand.AUSSER_BETRIEB, windzone=windzone),
            StaudruckSzenario("IN_BETRIEB",     "mit Schutzmaßnahmen", Norm.DIN_EN_13814_2005_06, modus="betrieb",
                            betriebszustand=Betriebszustand.IN_BETRIEB, windzone=windzone),
        ],
        normtitel="DIN EN 13814:2005-06",
        allow_alternativen=True,
    )

    # --------------------------
    # DIN EN 17879:2024-08
    # --------------------------
    _rechne_norm(
        [
            StaudruckSzenario("AUSSER_BETRIEB", "Außer Betrieb", Norm.DIN_EN_17879_2024_08, modus="betrieb",
                            betriebszustand=Betriebszustand.AUSSER_BETRIEB, windzone=windzone),
            StaudruckSzenario("IN_BETRIEB",     "mit Schutzmaßnahmen", Norm.DIN_EN_17879_2024_08, modus="betrieb",
                            betriebszustand=Betriebszustand.IN_BETRIEB, windzone=windzone),
        ],
        normtitel="DIN EN 17879:2024-08",
        allow_alternativen=True,
    )

    # --------------------------
    # DIN EN 1991-1-4:2010-12
    # --------------------------
    _rechne_norm(
        [
            StaudruckSzenario("STANDARD", "Standard", Norm.DIN_EN_1991_1_4_2010_12, modus="schutz",
                            schutz=Schutzmassnahmen.KEINE, windzone=windzone),
            StaudruckSzenario("VERSTAERKEND", "mit verstärkenden Sicherungsmaßnahmen", Norm.DIN_EN_1991_1_4_2010_12, modus="schutz",
                            schutz=Schutzmassnahmen.VERSTAERKEND, windzone=windzone),
            StaudruckSzenario("SCHUETZEND", "mit schützenden Sicherungsmaßnahmen", Norm.DIN_EN_1991_1_4_2010_12, modus="schutz",
                            schutz=Schutzmassnahmen.SCHUETZEND, windzone=windzone),
        ],
        normtitel="DIN EN 1991-1-4:2010-12",
        allow_alternativen=allow_alternativen_1991,
    )

    tree = collect_tree(prot) or prot.root

    # DEBUG
    debug_tree(tree,output_dir="debug_output")

    return tree
