# rechenfunktionen/gleitsicherheit.py
from __future__ import annotations
from math import inf
from typing import Dict, Callable, Sequence, List, Optional
from collections.abc import Sequence as _SeqABC

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_kontext, protokolliere_msg, protokolliere_doc, make_docbundle, make_protokoll, merge_protokoll, collect_docs
from windlast_CORE.datenstruktur.enums import Norm, RechenmethodeGleiten, VereinfachungKonstruktion, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.konstanten import _EPS, aktuelle_konstanten
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from windlast_CORE.datenstruktur.kraefte import Kraefte

from windlast_CORE.rechenfunktionen.standsicherheit_utils import (
    generiere_windrichtungen,
    obtain_pool,
    get_or_create_lastset,
    ermittle_min_reibwert,
    gleit_envelope_pro_bauelement,
)
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektoren_addieren, vektor_laenge

def _emit_docs_with_role(*, dst_protokoll, docs, base_ctx: dict, role: str, extra_ctx: dict | None = None):
    for bundle, ctx in docs:
        ktx = merge_kontext(base_ctx, ctx or {})
        ktx["rolle"] = role
        if extra_ctx:
            ktx.update(extra_ctx)
        protokolliere_doc(dst_protokoll, bundle=bundle, kontext=ktx)

def _validate_inputs(
    konstruktion,
    *,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst=None,  # bewusst ignoriert, aber Teil der Signatur
    reset_berechnungen: bool,
    methode: RechenmethodeGleiten,
    vereinfachung_konstruktion: VereinfachungKonstruktion,
    anzahl_windrichtungen: int,
) -> None:
    # konstruktion: hat bauelemente?
    if not hasattr(konstruktion, "bauelemente"):
        raise AttributeError("konstruktion muss ein Attribut 'bauelemente' besitzen.")
    if not isinstance(konstruktion.bauelemente, (list, tuple)) or len(konstruktion.bauelemente) == 0:
        raise ValueError("'bauelemente' muss eine nicht-leere Liste/Tuple sein.")

    # norm: vom Typ Norm und existent
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

    # methode: RechenmethodeGleiten und existent
    if not isinstance(methode, RechenmethodeGleiten):
        raise TypeError("methode muss vom Typ RechenmethodeGleiten sein.")

    # vereinfachung_konstruktion: VereinfachungKonstruktion und existent
    if not isinstance(vereinfachung_konstruktion, VereinfachungKonstruktion):
        raise TypeError("vereinfachung_konstruktion muss vom Typ VereinfachungKonstruktion sein.")

    # anzahl_windrichtungen: int >= 1?
    if not isinstance(anzahl_windrichtungen, int) or anzahl_windrichtungen < 1:
        raise ValueError("anzahl_windrichtungen muss ein int ≥ 1 sein.")
    
def _gleitsicherheit_DinEn13814_2005_06(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Gleitsicherheit",
        "norm": "DIN EN 13814:2005-06",
        "methode": methode.value,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(norm,konstruktion, protokoll=protokoll, kontext=base_ctx)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Minimaler Reibwert μ_min",
                wert=reibwert_min,
                formel="μ_min = min(μ_Bauelemente)",
                formelzeichen=["μ_Bauelemente"],
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "min_reibwert"}),
        )

        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, kontext=base_ctx)
        pool = obtain_pool(konstruktion, reset_berechnungen)
        dir_records = []

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

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for element, lastfaelle_elem in kraefte_nach_element.items():
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=sub_prot, kontext=base_ctx)
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Horizontalkraft H",
                        wert=H_vec,
                        einheit="N",
                    ),
                    kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "element_horizontalkraft", "windrichtung_deg": winkel, "element_id": str(element)}),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Normalkraft N_down",
                        wert=N_down,
                        einheit="N",
                    ),
                    kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "element_normalkraft_down", "windrichtung_deg": winkel, "element_id": str(element)}),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Normalkraft N_up",
                        wert=N_up,
                        einheit="N",
                    ),
                    kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "element_normalkraft_up", "windrichtung_deg": winkel, "element_id": str(element)}),
                )
                total_horizontal = vektoren_addieren([total_horizontal, H_vec])
                total_normal_up += N_up
                total_normal_down += N_down

            horizontal_betrag = vektor_laenge(total_horizontal)
            normal_effektiv = max(0.0, total_normal_down - total_normal_up)
            reibkraft = reibwert_min * normal_effektiv

            # === Zwischendocs (Aggregat der Richtung) ===
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Summe Horizontalbetrag |H|",
                    wert=horizontal_betrag,
                    einheit="N",
                    formel="|T| = √(T_x² + T_y² + T_z²)",
                    formelzeichen=["T_x", "T_y", "T_z"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "horizontal_betrag", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Summe Normalkräfte ΣN_down",
                    wert=total_normal_down,
                    einheit="N",
                    formel="ΣN_down = N_{down,Element}",
                    formelzeichen=["N_{down,Element}"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "normal_down", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Summe Normalkräfte ΣN_up",
                    wert=total_normal_up,
                    einheit="N",
                    formel="ΣN_up = N_{up,Element}",
                    formelzeichen=["N_{up,Element}"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "normal_up", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Effektive Normalkraft N_eff",
                    wert=normal_effektiv,
                    einheit="N",
                    formel="N_eff = max(0, ΣN_down − ΣN_up)",
                    formelzeichen=["ΣN_down", "ΣN_up"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "normal_effektiv", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Reibkraft R",
                    wert=reibkraft,
                    einheit="N",
                    formel="R = μ_min · N_eff",
                    formelzeichen=["μ_min", "N_eff"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "reibkraft", "windrichtung_deg": winkel}),
            )

            if horizontal_betrag > _EPS:
                sicherheit = reibkraft / horizontal_betrag
                dir_min_sicherheit = min(dir_min_sicherheit, sicherheit)
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel=f"Richtungs-Sicherheit S_gleit,{int(winkel)}°",
                        wert=sicherheit,
                        formel="S = R / T",
                        formelzeichen=["R", "T"],
                        quelle_formel="---",
                    ),
                    kontext={"nachweis": "GLEIT", "doc_type": "dir_sicherheit", "windrichtung_deg": winkel},
                )

            if reibwert_min <= _EPS:
                if horizontal_betrag > _EPS:
                    ballastkraft = inf
                else:
                    ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
            else:
                ballastkraft = max(0.0, horizontal_betrag / reibwert_min + total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert

            if ballastkraft > dir_ballast_max:
                dir_ballast_max = ballastkraft

            # Ballast-Doc (Richtung)
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel=f"Richtungs-Ballast m_Ballast,gleit,{int(winkel)}°",
                    wert=ballastkraft,
                    formel="Δm_Ballast,gleit = T/μ + ΣN_up − ΣN_down",
                    formelzeichen=["T", "μ", "N_up", "N_down"],
                    quelle_formel="---",
                ),
                kontext={"nachweis": "GLEIT", "doc_type": "dir_ballast", "windrichtung_deg": winkel},
            )

            # Record ablegen (WICHTIG: innerhalb der Schleife!)
            dir_records.append({
                "winkel_deg": winkel,
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
                "docs": collect_docs(sub_prot),
                "sub_prot": sub_prot,
            })

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]

        # Messages: Gewinner alles, Verlierer nur Errors
        for i, rec in enumerate(dir_records):
            if i == winner_idx:
                merge_protokoll(rec["sub_prot"], protokoll, only_errors=False)
            else:
                merge_protokoll(rec["sub_prot"], protokoll, only_errors=True)

        # Docs mit Rollen ausspielen
        for i, rec in enumerate(dir_records):
            role = "entscheidungsrelevant" if i == winner_idx else "irrelevant"
            _emit_docs_with_role(
                dst_protokoll=protokoll,
                docs=rec["docs"],
                base_ctx=merge_kontext(base_ctx, {"nachweis": "GLEIT", "windrichtung_deg": rec["winkel_deg"]}),
                role=role,
            )

        sicherheit_min_global = dir_records[winner_idx]["dir_min_sicherheit"]
        ballast_erforderlich_max = dir_records[winner_idx]["dir_ballast_max"]

        # Endwerte (relevant)
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Gleitsicherheit S_gleit",
                wert=sicherheit_min_global,
                formel="S = R / T",
                formelzeichen=["R", "T"],
                quelle_formel="---",
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "rolle": "relevant"}),
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher Ballast m_Ballast,gleit",
                wert=ballast_kg,
                formel="Δm_Ballast,gleit = T/μ + ΣN_up − ΣN_down",
                formelzeichen=["T", "μ", "N_up", "N_down"],
                quelle_formel="---",
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "rolle": "relevant"}),
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]

    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

def _gleitsicherheit_DinEn17879_2024_08(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Gleitsicherheit",
        "norm": "DIN EN 17879:2024-08",
        "methode": methode.value,
    })

    if vereinfachung_konstruktion is not VereinfachungKonstruktion.KEINE:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/NOT_IMPLEMENTED",
            text=f"Vereinfachung '{vereinfachung_konstruktion.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

    if methode is RechenmethodeGleiten.MIN_REIBWERT:
        reibwert_min = ermittle_min_reibwert(norm,konstruktion, protokoll=protokoll, kontext=base_ctx)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Minimaler Reibwert μ_min",
                wert=reibwert_min,
                formel="μ_min = min(μ_Bauelemente)",
                formelzeichen=["μ_Bauelemente"],
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "min_reibwert"}),
        )

        sicherheit_min_global = inf
        ballast_erforderlich_max = 0.0
        ballastkraft_dummy = Kraefte(
            typ = Lasttyp.GEWICHT,
            variabilitaet = Variabilitaet.STAENDIG,
            Einzelkraefte = [(0.0, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[(0.0, 0.0, 0.0)]],
        )
        sicherheitsbeiwert_ballast = sicherheitsbeiwert(norm, ballastkraft_dummy, ist_guenstig=True, protokoll=protokoll, kontext=base_ctx)
        pool = obtain_pool(konstruktion, reset_berechnungen)
        dir_records = []

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

            total_horizontal: Vec3 = (0.0, 0.0, 0.0)
            total_normal_up = 0.0
            total_normal_down = 0.0

            for element, lastfaelle_elem in kraefte_nach_element.items():
                H_vec, N_down, N_up = gleit_envelope_pro_bauelement(norm, lastfaelle_elem, protokoll=sub_prot, kontext=base_ctx)
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Horizontalkraft H",
                        wert=H_vec,
                        einheit="N",
                    ),
                    kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "element_horizontalkraft", "windrichtung_deg": winkel, "element_id": str(element)}),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Normalkraft N_down",
                        wert=N_down,
                        einheit="N",
                    ),
                    kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "element_normalkraft_down", "windrichtung_deg": winkel, "element_id": str(element)}),
                )
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel="Normalkraft N_up",
                        wert=N_up,
                        einheit="N",
                    ),
                    kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "element_normalkraft_up", "windrichtung_deg": winkel, "element_id": str(element)}),
                )
                total_horizontal = vektoren_addieren([total_horizontal, H_vec])
                total_normal_up += N_up
                total_normal_down += N_down

            horizontal_betrag = vektor_laenge(total_horizontal)
            normal_effektiv = max(0.0, total_normal_down - total_normal_up)
            reibkraft = reibwert_min * normal_effektiv

            # === Zwischendocs (Aggregat der Richtung) ===
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Summe Horizontalbetrag |H|",
                    wert=horizontal_betrag,
                    einheit="N",
                    formel="|T| = √(T_x² + T_y² + T_z²)",
                    formelzeichen=["T_x", "T_y", "T_z"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "horizontal_betrag", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Summe Normalkräfte ΣN_down",
                    wert=total_normal_down,
                    einheit="N",
                    formel="ΣN_down = N_{down,Element}",
                    formelzeichen=["N_{down,Element}"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "normal_down", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Summe Normalkräfte ΣN_up",
                    wert=total_normal_up,
                    einheit="N",
                    formel="ΣN_up = N_{up,Element}",
                    formelzeichen=["N_{up,Element}"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "normal_up", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Effektive Normalkraft N_eff",
                    wert=normal_effektiv,
                    einheit="N",
                    formel="N_eff = max(0, ΣN_down − ΣN_up)",
                    formelzeichen=["ΣN_down", "ΣN_up"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "normal_effektiv", "windrichtung_deg": winkel}),
            )
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel="Reibkraft R",
                    wert=reibkraft,
                    einheit="N",
                    formel="R = μ_min · N_eff",
                    formelzeichen=["μ_min", "N_eff"],
                ),
                kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "doc_type": "reibkraft", "windrichtung_deg": winkel}),
            )

            if horizontal_betrag > _EPS:
                sicherheit = reibkraft / horizontal_betrag
                dir_min_sicherheit = min(dir_min_sicherheit, sicherheit)
                protokolliere_doc(
                    sub_prot,
                    bundle=make_docbundle(
                        titel=f"Richtungs-Sicherheit S_gleit,{int(winkel)}°",
                        wert=sicherheit,
                        formel="S = R / T",
                        formelzeichen=["R", "T"],
                        quelle_formel="---",
                    ),
                    kontext={"nachweis": "GLEIT", "doc_type": "dir_sicherheit", "windrichtung_deg": winkel},
                )

            if reibwert_min <= _EPS:
                if horizontal_betrag > _EPS:
                    ballastkraft = inf
                else:
                    ballastkraft = max(0.0, total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert
            else:
                ballastkraft = max(0.0, horizontal_betrag / reibwert_min + total_normal_up - total_normal_down) / sicherheitsbeiwert_ballast.wert

            if ballastkraft > dir_ballast_max:
                dir_ballast_max = ballastkraft

            # Ballast-Doc (Richtung)
            protokolliere_doc(
                sub_prot,
                bundle=make_docbundle(
                    titel=f"Richtungs-Ballast m_Ballast,gleit,{int(winkel)}°",
                    wert=ballastkraft,
                    formel=f"m_Ballast,gleit,{int(winkel)}° = T/μ + ΣN_up − ΣN_down",
                    formelzeichen=["T", "μ", "N_up", "N_down"],
                    quelle_formel="---",
                ),
                kontext={"nachweis": "GLEIT", "doc_type": "dir_ballast", "windrichtung_deg": winkel},
            )

            # Record ablegen (WICHTIG: innerhalb der Schleife!)
            dir_records.append({
                "winkel_deg": winkel,
                "dir_min_sicherheit": dir_min_sicherheit,
                "dir_ballast_max": dir_ballast_max,
                "docs": collect_docs(sub_prot),
                "sub_prot": sub_prot,
            })

        # --- Globale Entscheidung & Rollenvergabe ---
        if not dir_records:
            return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]

        winner_idx = min(range(len(dir_records)), key=lambda i: dir_records[i]["dir_min_sicherheit"])
        winner = dir_records[winner_idx]

        # Messages: Gewinner alles, Verlierer nur Errors
        for i, rec in enumerate(dir_records):
            if i == winner_idx:
                merge_protokoll(rec["sub_prot"], protokoll, only_errors=False)
            else:
                merge_protokoll(rec["sub_prot"], protokoll, only_errors=True)

        # Docs mit Rollen ausspielen
        for i, rec in enumerate(dir_records):
            role = "entscheidungsrelevant" if i == winner_idx else "irrelevant"
            _emit_docs_with_role(
                dst_protokoll=protokoll,
                docs=rec["docs"],
                base_ctx=merge_kontext(base_ctx, {"nachweis": "GLEIT", "windrichtung_deg": rec["winkel_deg"]}),
                role=role,
            )

        sicherheit_min_global = dir_records[winner_idx]["dir_min_sicherheit"]
        ballast_erforderlich_max = dir_records[winner_idx]["dir_ballast_max"]

        # Endwerte (relevant)
        erdbeschleunigung = aktuelle_konstanten().erdbeschleunigung
        ballast_kg = ballast_erforderlich_max / erdbeschleunigung

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Gleitsicherheit S_gleit",
                wert=sicherheit_min_global,
                formel="S_gleit = R / T",
                formelzeichen=["R", "T"],
                quelle_formel="---",
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "rolle": "relevant"}),
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Erforderlicher Ballast m_Ballast,gleit",
                wert=ballast_kg,
                formel="m_Ballast,gleit = T/μ + ΣN_up − ΣN_down",
                formelzeichen=["T", "μ", "N_up", "N_down"],
                quelle_formel="---",
            ),
            kontext=merge_kontext(base_ctx, {"nachweis": "GLEIT", "rolle": "relevant"}),
        )

        return [Zwischenergebnis(wert=sicherheit_min_global), Zwischenergebnis(wert=ballast_kg)]
    
    else:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="GLEIT/METHOD_NI",
            text=f"Methode '{methode.value}' ({methode.name}) ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        return [Zwischenergebnis(wert=float("nan")), Zwischenergebnis(wert=float("nan"))]
    
_DISPATCH: Dict[Norm, Callable[..., List[Zwischenergebnis]]] = {
    Norm.DEFAULT: _gleitsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_13814_2005_06: _gleitsicherheit_DinEn13814_2005_06,
    Norm.DIN_EN_17879_2024_08: _gleitsicherheit_DinEn17879_2024_08,
}

def gleitsicherheit(
    konstruktion,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    *,
    konst=None,
    reset_berechnungen: bool = False,
    methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
    vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
    anzahl_windrichtungen: int = 4,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Zwischenergebnis]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Gleitsicherheit",
        "norm": getattr(norm, "value", str(norm)),
        "anzahl_windrichtungen": anzahl_windrichtungen,
    })

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
            protokoll, severity=Severity.ERROR, code="GLEIT/INPUT_INVALID",
            text=str(e), kontext=base_ctx,
        )
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
    