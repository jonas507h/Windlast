# rechenfunktionen/kippsicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional, Tuple, Iterable
from collections.abc import Sequence as _SeqABC

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_kontext, protokolliere_msg, protokolliere_doc, make_docbundle, merge_protokoll, make_protokoll, collect_docs
from windlast_CORE.datenstruktur.enums import Norm, RechenmethodeKippen, VereinfachungKonstruktion, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.konstanten import _EPS, aktuelle_konstanten
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from windlast_CORE.rechenfunktionen.geom3d import flaechenschwerpunkt, moment_einzelkraft_um_achse

from windlast_CORE.rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    sammle_kippachsen,
    obtain_pool,
    get_or_create_lastset,
    kipp_envelope_pro_bauelement,
)

def _validate_inputs(
    konstruktion,
    *,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst=None,  # bewusst ignoriert, aber Teil der Signatur
    reset_berechnungen: bool,
    methode: RechenmethodeKippen,
    vereinfachung_konstruktion: VereinfachungKonstruktion,
    anzahl_windrichtungen: int,
) -> None:
    # konstruktion: hat bauelemente?
    if not hasattr(konstruktion, "bauelemente"):
        raise AttributeError("konstruktion muss ein Attribut 'bauelemente' besitzen.")
    if not isinstance(konstruktion.bauelemente, (list, tuple)) or len(konstruktion.bauelemente) == 0:
        raise ValueError("'bauelemente' muss eine nicht-leere Liste/Tuple sein.")

    # norm: vom Typ Norm und existent (Existenz = gültiges Enum-Mitglied)
    if not isinstance(norm, Norm):
        raise TypeError("norm muss vom Typ Norm sein.")

    # staudruecke: Sequence mit mind. 1 Eintrag
    if not isinstance(staudruecke, _SeqABC) or len(staudruecke) == 0:
        raise TypeError("staudruecke muss eine nicht-leere Sequence sein.")

    # obergrenzen: gleiche Länge wie staudruecke
    if not isinstance(obergrenzen, _SeqABC):
        raise TypeError("obergrenzen muss eine Sequence sein.")
    if len(obergrenzen) != len(staudruecke):
        raise ValueError("obergrenzen muss die gleiche Länge wie staudruecke haben.")

    # reset_berechnungen: bool?
    if not isinstance(reset_berechnungen, bool):
        raise TypeError("reset_berechnungen muss vom Typ bool sein.")

    # methode: RechenmethodeKippen und existent (Existenz = gültiges Enum-Mitglied)
    if not isinstance(methode, RechenmethodeKippen):
        raise TypeError("methode muss vom Typ RechenmethodeKippen sein.")

    # vereinfachung_konstruktion: VereinfachungKonstruktion und existent
    if not isinstance(vereinfachung_konstruktion, VereinfachungKonstruktion):
        raise TypeError("vereinfachung_konstruktion muss vom Typ VereinfachungKonstruktion sein.")

    # anzahl_windrichtungen: int >= 1?
    if not isinstance(anzahl_windrichtungen, int) or anzahl_windrichtungen < 1:
        raise ValueError("anzahl_windrichtungen muss ein int ≥ 1 sein.")

def _kippsicherheit_DinEn13814_2005_06(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = True,
    methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "_kippsicherheit",
        "norm": "DIN_EN_13814_2005_06",
        "methode": methode.name,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion, protokoll=protokoll, kontext=base_ctx)
        if not achsen:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
        # 1.1) Grundgrößen für Ballast bestimmen
        ballastkraft_dummy = Kraefte(
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=[(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True)
        huelle_punkte = [a.punkt for a in achsen]
        schwerpunkt_ballast = flaechenschwerpunkt(huelle_punkte)

        # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0

        pool = obtain_pool(konstruktion, reset_berechnungen)
        dir_records = []  # (winkel, richtung, min_sicherheit, ballast_max)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, kontext=base_ctx):
            sub_prot = make_protokoll()
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
                protokoll=sub_prot,
                kontext=merge_kontext(base_ctx, {"nachweis": "LOADS"}),
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf
            dir_ballast_max = 0.0 
            best_achse_idx = None
            achse_idx = -1

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                achse_idx += 1
                total_kipp = 0.0
                total_stand = 0.0

                achse_ctx = merge_kontext(base_ctx, {"achse_index": achse_idx, "windrichtung_deg": f"{winkel}°", "windrichtung": richtung, "nachweis": "KIPP"})

                for element, lastfaelle_elem in kraefte_nach_element.items():
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem, protokoll=sub_prot, kontext=merge_kontext(achse_ctx, {"element_id": str(element)}))
                    protokolliere_doc(
                        sub_prot,
                        bundle=make_docbundle(
                            titel="Kippmoment M_K",
                            wert=kipp_b,
                            einheit="Nm",
                        ),
                        kontext=merge_kontext(base_ctx, {
                            "nachweis": "KIPP",
                            "doc_type": "axis_momente",
                            "achse_index": achse_idx,
                            "element_id": str(element),
                        }),
                    )
                    protokolliere_doc(
                        sub_prot,
                        bundle=make_docbundle(
                            titel="Standmoment M_St",
                            wert=stand_b,
                            einheit="Nm",
                        ),
                        kontext=merge_kontext(base_ctx, {
                            "nachweis": "KIPP",
                            "doc_type": "axis_momente",
                            "achse_index": achse_idx,
                            "element_id": str(element),
                        }),
                    )
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Summe Kippmoment ΣM_K",
                        wert=total_kipp,
                        formel="ΣM_K = ΣM_K,Bauelement",
                        einheit="Nm",
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_momente",
                        "achse_index": achse_idx,
                    }),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Summe Standmoment ΣM_St",
                        wert=total_stand,
                        formel="ΣM_St = ΣM_St,Bauelement",
                        einheit="Nm",
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_momente",
                        "achse_index": achse_idx,
                    }),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel=f"Achs-Sicherheit S_kipp,Achse{achse_idx}",
                        wert=sicherheit,
                        formel=f"S_kipp,Achse{achse_idx} = ΣM_St / ΣM_K",
                        formelzeichen=["M_St", "M_K"],
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_sicherheit",
                        "achse_index": achse_idx,
                    }),
                )

                if sicherheit < dir_min_sicherheit:
                    dir_min_sicherheit = sicherheit
                    best_achse_idx = achse_idx

                moment_defizit = max(0.0, total_kipp - total_stand)

                if moment_defizit > _EPS:
                    ballast_kippmoment_einheit = moment_einzelkraft_um_achse(
                        achse,
                        (0.0, 0.0, -1.0),  # Einheitliche Abwärtskraft
                        schwerpunkt_ballast,
                    )
                    ballast_standmoment_proN = max(0.0, -ballast_kippmoment_einheit)

                    if ballast_standmoment_proN <= _EPS:
                        ballastkraft = inf  # kein Standsicherheitsbeitrag durch Ballast möglich     
                    else:
                        ballastkraft = moment_defizit / (ballast_standmoment_proN * sicherheitsbeiwert_ballast.wert)
                
                else:
                    ballastkraft = 0.0

                if ballastkraft > dir_ballast_max:
                    dir_ballast_max = ballastkraft

                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel=f"Achs-Ballast m_Ballast,kipp,Achse{achse_idx}",
                        wert=ballastkraft / aktuelle_konstanten().erdbeschleunigung,  # kg
                        formel="m_Ballast,kipp,Achse = max(0, ΣM_K − ΣM_St) / (γ_g · m_stand,1N)",
                        formelzeichen=["M_K", "M_St", "γ_g", "m_stand,1N", "g"],
                        einheit="kg",
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_ballast",
                        "achse_index": achse_idx,
                    }),
                )

            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel=f"Richtungs-Sicherheit S_kipp,{winkel}°",
                    wert=dir_min_sicherheit,
                    formel="S_kipp = ΣM_St / ΣM_K",
                    formelzeichen=["M_St", "M_K"],
                ),
                kontext=merge_kontext(base_ctx, {
                    "nachweis": "KIPP",
                    "doc_type": "dir_min_sicherheit",
                    "windrichtung_deg": f"{winkel}°",
                }),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel=f"Richtungs-Ballast m_Ballast,kipp,{winkel}°",
                    wert=dir_ballast_max / aktuelle_konstanten().erdbeschleunigung,
                    einheit="kg",
                    formel="m_Ballast,kipp = max(0, ΣM_K − ΣM_St) / (γ_g · m_stand,1N)",
                    formelzeichen=["M_K", "M_St", "γ_g", "m_stand,1N", "g"],
                ),
                kontext=merge_kontext(base_ctx, {
                    "nachweis": "KIPP",
                    "doc_type": "dir_ballast",
                    "windrichtung_deg": f"{winkel}°",
                }),
            )

            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
                "best_achse_idx": best_achse_idx,
                "docs": collect_docs(sub_prot),   # Liste[(bundle, ctx)]
                "sub_prot": sub_prot,             # nur für Messages
            })

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            # defensive: nichts gerechnet → Exit wie bisher
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        # 1) Gewinner-Richtung finden (minimale Sicherheit)
        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]

        # 2) Messages: wie gehabt – Gewinner komplett, Verlierer nur Errors
        for i, rec in enumerate(dir_records):
            sub_prot = rec["sub_prot"]
            if i == winner_idx:
                merge_protokoll(sub_prot, protokoll, only_errors=False)
            else:
                merge_protokoll(sub_prot, protokoll, only_errors=True)

        # 4) Globale Ergebnis-Docs (beste Richtung) kennzeichnen
        sicherheit_min_global = winner["dir_min_sicherheit"]
        ballast_erforderlich_max = winner["dir_ballast_max"]
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kippsicherheit S_kipp",
                wert=sicherheit_min_global,
                formel="S_kipp = ΣM_St / ΣM_K",
                quelle_formel="---",
                formelzeichen=["M_St", "M_K"],
                quelle_formelzeichen=["---"],
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "KIPP", "rolle": "relevant"}),
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher Ballast m_Ballast,kipp",
                wert=ballast_kg,
                einheit="kg",
                formel="m_Ballast,kipp = max(0, ΣM_K − ΣM_St) / (γ_g · m_stand,1N)",
                quelle_formel="---",
                formelzeichen=["M_K", "M_St", "γ_g", "m_stand,1N", "g"],
                quelle_formelzeichen=["---"],
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "KIPP", "rolle": "relevant"}),
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        # (andere Methoden:)
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
def _kippsicherheit_DinEn17879_2024_08(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = True,
    methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "_kippsicherheit",
        "norm": "DIN_EN_17879_2024_08",
        "methode": methode.name,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode == RechenmethodeKippen.STANDARD:
        # 1) Eckpunkte sammeln → Kippachsen bestimmen
        achsen = sammle_kippachsen(konstruktion, protokoll=protokoll, kontext=base_ctx)
        if not achsen:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
        # 1.1) Grundgrößen für Ballast bestimmen
        ballastkraft_dummy = Kraefte(
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=[(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True)
        huelle_punkte = [a.punkt for a in achsen]
        schwerpunkt_ballast = flaechenschwerpunkt(huelle_punkte)

        # 2) Minimum der Sicherheit über alle (Windrichtung × Achse)
        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0

        pool = obtain_pool(konstruktion, reset_berechnungen)
        dir_records = []  # (winkel, richtung, min_sicherheit, ballast_max)

        for winkel, richtung in generiere_windrichtungen(anzahl=anzahl_windrichtungen, protokoll=protokoll, kontext=base_ctx):
            sub_prot = make_protokoll()
            lastset = get_or_create_lastset(
                pool,
                konstruktion,
                winkel_deg=winkel,
                windrichtung=richtung,
                norm=norm,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
                protokoll=sub_prot,
                kontext=merge_kontext(base_ctx, {"nachweis": "LOADS"}),
            )
            kraefte_nach_element = lastset.kraefte_nach_element

            # Richtungs-lokale Aggregation
            dir_min_sicherheit = inf           # <<< NEU: kleinstes S dieser Richtung
            dir_ballast_max = 0.0              # <<< NEU: größter Ballast dieser Richtung
            best_achse_idx = None
            achse_idx = -1

            # 2c) Für jede Achse: Envelope je Bauelement → summieren → η bilden
            for achse in achsen:
                achse_idx += 1
                total_kipp = 0.0
                total_stand = 0.0

                achse_ctx = merge_kontext(base_ctx, {"achse_index": achse_idx, "windrichtung_deg": f"{winkel}°", "windrichtung": richtung, "nachweis": "KIPP"})

                for element, lastfaelle_elem in kraefte_nach_element.items():
                    kipp_b, stand_b = kipp_envelope_pro_bauelement(norm, achse, lastfaelle_elem, protokoll=sub_prot, kontext=merge_kontext(achse_ctx, {"element_id": str(element)}))
                    protokolliere_doc(
                        sub_prot,
                        bundle=make_docbundle(
                            titel="Kippmoment M_K",
                            wert=kipp_b,
                            einheit="Nm",
                        ),
                        kontext=merge_kontext(base_ctx, {
                            "nachweis": "KIPP",
                            "doc_type": "axis_momente",
                            "achse_index": achse_idx,
                            "element_id": str(element),
                        }),
                    )
                    protokolliere_doc(
                        sub_prot,
                        bundle=make_docbundle(
                            titel="Standmoment M_St",
                            wert=stand_b,
                            einheit="Nm",
                        ),
                        kontext=merge_kontext(base_ctx, {
                            "nachweis": "KIPP",
                            "doc_type": "axis_momente",
                            "achse_index": achse_idx,
                            "element_id": str(element),
                        }),
                    )
                    total_kipp += kipp_b
                    total_stand += stand_b

                # Sicherheit Sicherheit = Stand / Kipp
                if total_kipp <= _EPS:
                    sicherheit = inf  # keine kippende Wirkung → unendlich sicher bzgl. Kippen
                else:
                    sicherheit = total_stand / total_kipp

                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Summe Kippmoment ΣM_K",
                        wert=total_kipp,
                        formel="ΣM_K = ΣM_K,Bauelement",
                        einheit="Nm",
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_momente",
                        "achse_index": achse_idx,
                    }),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Summe Standmoment ΣM_St",
                        wert=total_stand,
                        formel="ΣM_St = ΣM_St,Bauelement",
                        einheit="Nm",
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_momente",
                        "achse_index": achse_idx,
                    }),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel=f"Achs-Sicherheit S_kipp,Achse{achse_idx}",
                        wert=sicherheit,
                        formel=f"S_kipp,Achse{achse_idx} = ΣM_St / ΣM_K",
                        formelzeichen=["M_St", "M_K"],
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_sicherheit",
                        "achse_index": achse_idx,
                    }),
                )

                # Richtungs-Minimum aktualisieren
                if sicherheit < dir_min_sicherheit:
                    dir_min_sicherheit = sicherheit
                    best_achse_idx = achse_idx

                moment_defizit = max(0.0, total_kipp - total_stand)

                if moment_defizit > _EPS:
                    ballast_kippmoment_einheit = moment_einzelkraft_um_achse(
                        achse,
                        (0.0, 0.0, -1.0),  # Einheitliche Abwärtskraft
                        schwerpunkt_ballast,
                    )
                    ballast_standmoment_proN = max(0.0, -ballast_kippmoment_einheit)

                    if ballast_standmoment_proN <= _EPS:
                        ballastkraft = inf  # kein Standsicherheitsbeitrag durch Ballast möglich     
                    else:
                        ballastkraft = moment_defizit / (ballast_standmoment_proN * sicherheitsbeiwert_ballast.wert)
                
                else:
                    ballastkraft = 0.0

                if ballastkraft > dir_ballast_max:
                    dir_ballast_max = ballastkraft

                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel=f"Achs-Ballast m_Ballast,kipp,Achse{achse_idx}",
                        wert=ballastkraft / aktuelle_konstanten().erdbeschleunigung,  # kg
                        einheit= "kg",
                        formel="m_Ballast,kipp,Achse = max(0, ΣM_K − ΣM_St) / (γ_g · m_stand,1N)",
                        formelzeichen=["M_K", "M_St", "γ_g", "m_stand,1N", "g"],
                    ),
                    kontext=merge_kontext(base_ctx, {
                        "nachweis": "KIPP",
                        "doc_type": "axis_ballast",
                        "achse_index": achse_idx,
                    }),
                )

            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel=f"Richtungs-Sicherheit S_kipp,{winkel}°",
                    wert=dir_min_sicherheit,
                    formel="S_kipp = ΣM_St / ΣM_K",
                    formelzeichen=["M_St", "M_K"],
                ),
                kontext=merge_kontext(base_ctx, {
                    "nachweis": "KIPP",
                    "doc_type": "dir_min_sicherheit",
                    "windrichtung_deg": f"{winkel}°",
                }),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel=f"Richtungs-Ballast m_Ballast,kipp,{winkel}°",
                    wert=dir_ballast_max / aktuelle_konstanten().erdbeschleunigung,
                    einheit="kg",
                    formel="m_Ballast,kipp = max(0, ΣM_K − ΣM_St) / (γ_g · m_stand,1N)",
                    formelzeichen=["M_K", "M_St", "γ_g", "m_stand,1N", "g"],
                ),
                kontext=merge_kontext(base_ctx, {
                    "nachweis": "KIPP",
                    "doc_type": "dir_ballast",
                    "windrichtung_deg": f"{winkel}°",
                }),
            )

            dir_records.append({
                "windrichtung_deg": f"{winkel}°",
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
                "best_achse_idx": best_achse_idx,
                "docs": collect_docs(sub_prot),   # Liste[(bundle, ctx)]
                "sub_prot": sub_prot,             # nur für Messages
            })


        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            # defensive: nichts gerechnet → Exit wie bisher
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        # 1) Gewinner-Richtung finden (minimale Sicherheit)
        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]

        # 2) Messages: wie gehabt – Gewinner komplett, Verlierer nur Errors
        for i, rec in enumerate(dir_records):
            sub_prot = rec["sub_prot"]
            if i == winner_idx:
                merge_protokoll(sub_prot, protokoll, only_errors=False)
            else:
                merge_protokoll(sub_prot, protokoll, only_errors=True)

        # 4) Globale Ergebnis-Docs (beste Richtung) kennzeichnen
        sicherheit_min_global = winner["dir_min_sicherheit"]
        ballast_erforderlich_max = winner["dir_ballast_max"]
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kippsicherheit S_kipp",
                wert=sicherheit_min_global,
                formel="S_kipp = ΣM_St / ΣM_K",
                quelle_formel="---",
                formelzeichen=["M_St", "M_K"],
                quelle_formelzeichen=["---"],
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "KIPP", "rolle": "relevant"}),
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher Ballast m_Ballast,kipp",
                wert=ballast_kg,
                einheit="kg",
                formel="m_Ballast,kipp = max(0, ΣM_K − ΣM_St) / (γ_g · m_stand,1N)",
                quelle_formel="---",
                formelzeichen=["M_K", "M_St", "γ_g", "m_stand,1N", "g"],
                quelle_formelzeichen=["---"],
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "KIPP", "rolle": "relevant"}),
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
_DISPATCH: Dict[Norm, Callable[..., List[Zwischenergebnis]]] = {
    Norm.DEFAULT: _kippsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_13814_2005_06: _kippsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_17879_2024_08: _kippsicherheit_DinEn17879_2024_08,
}

def kippsicherheit(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = True,
    methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "kippsicherheit",
        "norm": getattr(norm, "name", str(norm)),
        "anzahl_windrichtungen": anzahl_windrichtungen,
    })
    """
    Norm-dispatchte Kipp-Sicherheitsbewertung.
    Gibt ein Zwischenergebnis mit der minimalen Sicherheit über alle Windrichtungen/Achsen zurück.
    """
    try:
        _validate_inputs(
            konstruktion,
            norm=norm,
            staudruecke=staudruecke,
            obergrenzen=obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
        )
    except Exception as e:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR,
            code="KIPP/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        # NaN-Placeholder zurück (wie vereinbart: Zwischenergebnis nur mit wert)
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        konstruktion,
        norm,
        staudruecke,
        obergrenzen,
        konst=konst,
        reset_berechnungen=reset_berechnungen,
        methode=methode,
        vereinfachung_konstruktion=vereinfachung_konstruktion,
        anzahl_windrichtungen=anzahl_windrichtungen,
        protokoll=protokoll,
        kontext=base_ctx,
    )