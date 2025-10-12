import math
from typing import List, Tuple, Optional, Sequence, Iterable, Dict
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektor_zwischen_punkten, vektor_normieren, einheitsvektor_aus_winkeln, konvexe_huelle_xy, moment_einzelkraft_um_achse, vektor_laenge
from windlast_CORE.datenstruktur.objekte3d import Achse
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.enums import Norm, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.zwischenergebnis import Protokoll, merge_kontext, protokolliere_msg, protokolliere_doc, make_docbundle
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from windlast_CORE.datenstruktur.lastpool import LastPool, LastSet
from windlast_CORE.datenstruktur.konstanten import _EPS

def generiere_windrichtungen(
    anzahl: int = 4,
    *,
    startwinkel: float = 0.0,
    winkel: Optional[Sequence[float]] = None,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> List[Tuple[float, Vec3]]:
    base_ctx = merge_kontext(kontext, {"funktion": "generiere_windrichtungen"})
    
    if winkel is not None:
        result = [(w, einheitsvektor_aus_winkeln(w, 0.0)) for w in winkel]
    else:
        if anzahl < 1:
            protokolliere_msg(protokoll, severity=Severity.ERROR,
                code="UTILS/WINDRICHTUNG_ANZAHL",
                text="Anzahl der Windrichtungen muss ≥ 1 sein.",
                kontext=base_ctx
                )
        winkelabstand = 360.0 / anzahl
        result = [(i * winkelabstand + startwinkel, einheitsvektor_aus_winkeln(i * winkelabstand + startwinkel, 0.0)) for i in range(anzahl)]

    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(titel="Windrichtungen (deg)", wert=[w for w, _ in result]),
        kontext=base_ctx,
    )
    return result

def ermittle_kraefte_pro_windrichtung(
    konstruktion,
    norm: Norm,
    windrichtung: Vec3,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Dict[str, List[Kraefte]]:
    base_ctx = merge_kontext(kontext, {
        "funktion": "ermittle_kraefte_pro_windrichtung",
        "norm": getattr(norm, "value", str(norm)),
        "windrichtung": windrichtung,
    })

    # 1)Wind- & Gewichtskräfte aller Bauelemente holen
    kraefte_windrichtung: List[Kraefte] = []

    for idx, elem in enumerate(getattr(konstruktion, "bauelemente", []) or []):
        elem_ctx = merge_kontext(base_ctx, {
            "element_index": idx,
            "element_id": getattr(elem, "element_id_intern", None),
            "objekttyp": getattr(getattr(elem, "objekttyp", None), "value", None),
        })
        # Gewicht
        fn_gewicht = getattr(elem, "gewichtskraefte", None)
        if callable(fn_gewicht):
            try:
                kraefte_gewicht = fn_gewicht(protokoll=protokoll, kontext=elem_ctx)
                if kraefte_gewicht:
                    kraefte_windrichtung.extend(kraefte_gewicht)
            except Exception as e:
                protokolliere_msg(
                    protokoll, severity=Severity.ERROR,
                    code="UTILS/GEWICHT_FAIL",
                    text=f"gewichtskraefte() für Element {idx} fehlgeschlagen: {e}",
                    kontext=elem_ctx,
                )

        # Wind
        fn_wind = getattr(elem, "windkraefte", None)
        if callable(fn_wind):
            try:
                kraefte_wind = fn_wind(
                    norm=norm,
                    windrichtung=windrichtung,
                    staudruecke=staudruecke,
                    obergrenzen=obergrenzen,
                    konst=konst,
                    protokoll=protokoll,
                    kontext=elem_ctx,
                )
                if kraefte_wind:
                    kraefte_windrichtung.extend(kraefte_wind)
            except Exception as e:
                protokolliere_msg(
                    protokoll, severity=Severity.ERROR,
                    code="UTILS/WIND_FAIL",
                    text=f"windkraefte() für Element {idx} fehlgeschlagen: {e}",
                    kontext=elem_ctx,
                )
    
    # 2) Nach Bauelement gruppieren (erwartet: element_id_intern gesetzt)
    kraefte_nach_element: Dict[str, List[Kraefte]] = {}
    for k in kraefte_windrichtung:
        key = k.element_id_intern or f"elem_{id(k)}"  # Fallback, falls ID fehlt
        kraefte_nach_element.setdefault(key, []).append(k)

    return kraefte_nach_element

def _angle_key(winkel_deg: float) -> int:
    return int(round(winkel_deg * 1e4))

def obtain_pool(konstruktion, reset_berechnungen: bool, *, protokoll: Optional[Protokoll]=None, kontext: Optional[dict]=None) -> LastPool:
    base_ctx = merge_kontext(kontext, {"funktion": "obtain_pool"})
    if reset_berechnungen or not hasattr(konstruktion, "_lastpool") or konstruktion._lastpool is None:
        konstruktion._lastpool = LastPool()
        protokolliere_msg(protokoll, severity=Severity.HINT,
                          code="UTILS/POOL_RESET",
                          text="Lastpool neu angelegt/gesetzt (reset_berechnungen=True oder fehlte).",
                          kontext=base_ctx)
    return konstruktion._lastpool


def get_or_create_lastset(
    pool: LastPool,
    konstruktion,
    *,
    winkel_deg: float,
    windrichtung: Vec3,
    norm: Norm,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> LastSet:
    base_ctx = merge_kontext(kontext, {
        "funktion": "get_or_create_lastset",
        "winkel_deg": f"{winkel_deg}°",
        "windrichtung": windrichtung,
    })

    key = _angle_key(winkel_deg)
    ls = pool.nach_winkel.get(key)
    if ls is None:
        kbe = ermittle_kraefte_pro_windrichtung(
            konstruktion,
            norm=norm,
            windrichtung=windrichtung,
            staudruecke=staudruecke,
            obergrenzen=obergrenzen,
            konst=konst,
            protokoll=protokoll,
            kontext=base_ctx,
        )
        ls = LastSet(winkel_deg=winkel_deg, windrichtung=windrichtung, kraefte_nach_element=kbe)
        pool.nach_winkel[key] = ls

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="LastSet erstellt", wert={"winkel_deg": winkel_deg, "anzahl_elemente": len(kbe)}),
            kontext=base_ctx,
        )
    return ls

# Kippsicherheit Utils --------------------------------------------

def sammle_kippachsen(konstruktion, *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None) -> List[Achse]:
    base_ctx = merge_kontext(kontext, {"funktion": "sammle_kippachsen"})
    eckpunkte: List[Vec3] = []

    for idx, obj in enumerate(getattr(konstruktion, "bauelemente", [])):
        ep = getattr(obj, "eckpunkte", None)
        if callable(ep):
            try:
                punkte = ep(protokoll=protokoll, kontext=merge_kontext(base_ctx, {"element_index": idx}))
            except TypeError:
                # alte Signatur ohne protokoll/kontext
                punkte = ep()
            if punkte:
                eckpunkte.extend(punkte)

    if len(eckpunkte) < 3:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NO_POINTS",
            text="Zu wenige Eckpunkte für die Bestimmung von Kippachsen (min. 3).",
            kontext=merge_kontext(base_ctx, {"anzahl_punkte": len(eckpunkte)}),
        )
        return []

    achsen = kippachsen_aus_eckpunkten(eckpunkte, include_Randpunkte=False)
    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(titel="Anzahl Kippachsen", wert=len(achsen)),
        kontext=base_ctx,
    )
    return achsen

def kippachsen_aus_eckpunkten(
    punkte: List[Vec3], *, include_Randpunkte: bool = False,
    protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> List[Achse]:
    base_ctx = merge_kontext(kontext, {"funktion": "kippachsen_aus_eckpunkten"})

    if len(punkte) < 3:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/POINTS_LT3",
            text="Mindestens 3 Punkte erforderlich, um Kippachsen zu bestimmen.",
            kontext=merge_kontext(base_ctx, {"anzahl_punkte": len(punkte)}),
        )
        return []
    
    huelle = konvexe_huelle_xy(punkte)

    if len(huelle) < 2:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/HULL_LT2",
            text="Konvexe Hülle enthält weniger als 2 Eckpunkte.",
            kontext=merge_kontext(base_ctx, {"anzahl_huelle": len(huelle)}),
        )
        return []
    
    kippachsen: List[Achse] = []
    for i in range(len(huelle)):
        p1 = huelle[i]
        p2 = huelle[(i + 1) % len(huelle)]

        richtung = vektor_zwischen_punkten(p1, p2)
        richtung_norm = vektor_normieren(richtung)
        if richtung_norm == (0.0, 0.0, 0.0):
            continue
        kippachsen.append(Achse(punkt=p1, richtung=richtung_norm))
    
    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(titel="Konvexe Hülle (Eckpunkte)", wert=huelle),
        kontext=base_ctx,
    )
    return kippachsen

def bewerte_lastfall_fuer_achse(
    norm: Norm, achse: Achse, lastfall: Kraefte,
    *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> Tuple[float, float]:
    """
    Aggregiert das Moment eines Lastfalls (Objekt 'Kraefte') um die gegebene Achse.

    Pro Einzelkraft i:
      1) m_sign = u · ((r_i - p) × F_i)
      2) m_kipp = -m_sign  (>0 = kippend/ungünstig, <=0 = stabilisierend/günstig)
      3) γ = Sicherheitsbeiwert(norm, lastfall, ist_guenstig=(m_kipp <= 0))
      4) Summen:
           kipp_sum  += γ * max(m_kipp, 0)
           stand_sum += γ * max(-m_kipp, 0)

    Rückgabe:
      (kipp_sum, stand_sum) für diesen Lastfall.
    """

    base_ctx = merge_kontext(kontext, {
        "funktion": "bewerte_lastfall_fuer_achse",
        "lasttyp": getattr(lastfall, "typ", None),
    })

    Einzelkraefte: Sequence[Vec3] = lastfall.Einzelkraefte
    Angriffspunkte: Sequence[Vec3] = lastfall.Angriffspunkte_Einzelkraefte

    if Angriffspunkte is None or len(Angriffspunkte) != len(Einzelkraefte):
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NO_ATTACK_POINTS",
            text="Angriffspunkte der Einzelkräfte fehlen oder ungleich lang.",
            kontext=merge_kontext(base_ctx, {
                "anzahl_kraefte": len(Einzelkraefte),
                "anzahl_punkte": 0 if Angriffspunkte is None else len(Angriffspunkte),
            }),
        )
        return 0.0, 0.0
    
    kipp_sum = 0.0
    stand_sum = 0.0

    for Kraft, Punkt in zip(Einzelkraefte, Angriffspunkte):
        # 1) Moment um die Achse (Skalar, Rechtsschraube) …
        m_kipp = moment_einzelkraft_um_achse(achse, Kraft, Punkt)

        # 2) Sicherheitsbeiwert nach Günstigkeit bestimmen
        ist_guenstig = (m_kipp <= _EPS)
        gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig).wert

        # 3) Aufteilen in kippend vs. stabilisierend
        if m_kipp > _EPS:
            kipp_sum += gamma * m_kipp
        else:
            # (-m_kipp) ist der Betrag des stabilisierenden Moments
            stand_sum += gamma * (-m_kipp)

    return kipp_sum, stand_sum


def kipp_envelope_pro_bauelement(
    norm: Norm,
    achse: Achse,
    lastfaelle: Iterable[Kraefte],
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None
) -> Tuple[float, float]:
    base_ctx = merge_kontext(kontext, {"funktion": "kipp_envelope_pro_bauelement"})
    """
    Bildet je Bauelement den ungünstigen „Envelope“ über seine Lastfälle.

    Regeln:
      - WIND:    wähle den Lastfall mit maximalem kippenden Anteil (kipp_sum).
                 (stabilisierende Windanteile haben γ=0 → werden nicht gutgeschrieben)
      - GEWICHT: wähle den Lastfall mit maximalem (kipp_sum - stand_sum)
                 (= „am wenigsten günstig“; berücksichtigt, dass nur günstige & ständige
                    Eigenlast mit γ>0 stabilisierend wirken darf)
      - Sonstiges (z. B. REIBUNG): konservativ wie WIND → max. kipp_sum.

    Rückgabe:
      (kipp_sum_bauteil, stand_sum_bauteil) — die Beiträge des Bauteils zum globalen Nachweis.
    """
    # Sammle bewertete Lastfälle pro Typ
    wind_kipp: List[float] = []
    gewicht_pairs: List[Tuple[float, float]] = []
    other_pairs: List[Tuple[float, float]] = []

    for k in lastfaelle:
        kipp, stand = bewerte_lastfall_fuer_achse(norm, achse, k)
        if k.typ == Lasttyp.WIND:
            wind_kipp.append(kipp)
        elif k.typ == Lasttyp.GEWICHT:
            gewicht_pairs.append((kipp, stand))
        else:
            other_pairs.append((kipp, stand))

    # Envelopebildung je Typ
    best_wind_kipp = max(wind_kipp) if wind_kipp else 0.0

    best_gew_kipp = 0.0
    best_gew_stand = 0.0
    if gewicht_pairs:
        # „ungünstigster“ Gewichts-Lastfall
        best_gew_kipp, best_gew_stand = max(
            gewicht_pairs,
            key=lambda pair: pair[0] - pair[1]
        )

    best_other_kipp = 0.0
    best_other_stand = 0.0
    if other_pairs:
        # konservativ: max kippend
        best_other_kipp, best_other_stand = max(
            other_pairs,
            key=lambda pair: pair[0]
        )

    # Ergebnis für das Bauelement
    kipp_sum_bauteil = best_wind_kipp + best_gew_kipp + best_other_kipp
    stand_sum_bauteil = best_gew_stand + best_other_stand
    return kipp_sum_bauteil, stand_sum_bauteil

# Gleitsicherheit Utils ------------------------------

def ermittle_min_reibwert(
    norm: Norm, konstruktion,
    *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> float:
    base_ctx = merge_kontext(kontext, {"funktion": "ermittle_min_reibwert"})
    """Liest μ aus allen Bodenplatten (Elem hat Methode reibwert()) und gibt das Minimum zurück.
       Falls keine Platte gefunden → 0.0 (konservativ)."""
    mu_werte: List[float] = []
    for idx, elem in enumerate(getattr(konstruktion, "bauelemente", []) or []):
        elem_ctx = merge_kontext(base_ctx, {
            "element_index": idx,
            "element_id": getattr(elem, "element_id_intern", None),
        })

        reib_fn = getattr(elem, "reibwert_effektiv", None)
        if not callable(reib_fn):
            continue

        try:
            mu = reib_fn(norm, protokoll=protokoll, kontext=elem_ctx)
            if mu is not None:
                mu_werte.append(float(mu))
        except Exception as e:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="GLEIT/MU_READ_FAIL",
                text=f"Reibwert-Ermittlung für Element {idx} fehlgeschlagen: {e}",
                kontext=elem_ctx,
            )

    if not mu_werte:
        protokolliere_msg(
            protokoll, severity=Severity.WARN, code="GLEIT/NO_PLATE_MU",
            text="Kein Reibwert gefunden – setze konservativ μ=0.",
            kontext=base_ctx,
        )
        return 0.0

    mu_min = min(mu_werte)
    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(titel="Reibwerte μ (min)", wert={"min": mu_min, "alle": mu_werte}),
        kontext=base_ctx,
    )
    return mu_min

def bewerte_lastfall_fuer_gleiten(
    norm: Norm, lastfall: Kraefte,
    *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> Tuple[Vec3, float, float]:
    base_ctx = merge_kontext(kontext, {"funktion": "bewerte_lastfall_fuer_gleiten",
                                       "lasttyp": getattr(lastfall, "typ", None)})
    """
    Zerlegt einen Lastfall in:
      H_vec (treibend, horizontal, γ_ungünstig),
      N_down (günstig, nur aus GEWICHT mit γ_günstig),
      N_up   (ungünstig, γ_ungünstig).
    Rückgabe: (H_vec, N_down, N_up)
    """

    Einzelkraefte: Sequence[Vec3] = lastfall.Einzelkraefte

    Hx = Hy = Hz = 0.0
    N_down = 0.0
    N_up   = 0.0

    gamma_unguenstig = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False).wert
    gamma_guenstig = sicherheitsbeiwert(norm, lastfall, ist_guenstig=True).wert

    for Kraft in Einzelkraefte:
        fx = Kraft[0]
        fy = Kraft[1]
        fz = Kraft[2]

        Hx += gamma_unguenstig * fx
        Hy += gamma_unguenstig * fy

        if fz > _EPS:
            N_up += gamma_unguenstig * fz
        elif fz < -_EPS:
            N_down += gamma_guenstig * (-fz)
    
    H_vec: Vec3 = (Hx, Hy, Hz)

    return H_vec, N_down, N_up

def gleit_envelope_pro_bauelement(
    norm: Norm, lastfaelle: Iterable[Kraefte],
    *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> Tuple[Vec3, float, float]:
    base_ctx = merge_kontext(kontext, {"funktion": "gleit_envelope_pro_bauelement"})
    """
    Element-konsistent:
      - Wähle den Lastfall mit maximaler ||H_vec|| ⇒ dessen H_vec und N_up zählen.
      - N_down kommt aus den GEWICHT-Lastfällen: kleinster (ungünstigster) Wert.
    Rückgabe: (H_vec_bauteil, N_down_bauteil, N_up_bauteil)
    """
    best_H_vec: Vec3 = (0.0, 0.0, 0.0)
    best_H_betrag = -1.0
    best_N_down = None
    best_N_up = 0.0

    for k in lastfaelle:
        H_vec, N_down, N_up = bewerte_lastfall_fuer_gleiten(norm, k)
        H_betrag = vektor_laenge(H_vec)
        if k.typ == Lasttyp.WIND:
            if H_betrag > best_H_betrag:
                best_H_betrag = H_betrag
                best_H_vec = H_vec
                best_N_up = N_up

        if k.typ == Lasttyp.GEWICHT:
            best_N_down = N_down if best_N_down is None else min(best_N_down, N_down)

    if best_N_down is None:
        best_N_down = 0.0

    return best_H_vec, best_N_down, best_N_up

# Abhebesicherheit Utils -----------------------------------

def bewerte_lastfall_fuer_abheben(
    norm: Norm, lastfall: Kraefte, *,
    protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> Tuple[float, float]:
    base_ctx = merge_kontext(kontext, {"funktion": "bewerte_lastfall_fuer_abheben",
                                       "lasttyp": getattr(lastfall, "typ", None)})
    """
    Zerlegt einen Lastfall in:
      N_down (günstig, NACH UNTEN; nur aus GEWICHT mit γ_günstig, als positive Größe),
      N_up   (ungünstig, NACH OBEN; aus allen Lastfällen mit γ_ungünstig, als positive Größe).
    Rückgabe: (N_down, N_up)
    """
    N_down = 0.0
    N_up = 0.0

    gamma_unguenstig = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False, protokoll=protokoll, kontext=base_ctx).wert
    gamma_guenstig = sicherheitsbeiwert(norm, lastfall, ist_guenstig=True, protokoll=protokoll, kontext=base_ctx).wert

    for F in lastfall.Einzelkraefte:
        fz = F[2]
        if fz > _EPS:
            # nach oben → ungünstig
            N_up += gamma_unguenstig * fz
        elif fz < -_EPS:
            # nach unten → günstig, positive Magnitude
            N_down += gamma_guenstig * (-fz)

    return N_down, N_up


def abhebe_envelope_pro_bauelement(
    norm: Norm, lastfaelle: Iterable[Kraefte], *,
    protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
) -> Tuple[float, float]:
    base_ctx = merge_kontext(kontext, {"funktion": "abhebe_envelope_pro_bauelement"})
    """
    Element-konsistent:
      - N_up_bauteil = max (Auftrieb) über ALLE Lastfälle.
      - N_down_bauteil = min (Auflast) über GEWICHT-Lastfälle (ungünstig kleinster Wert).
    Rückgabe: (N_down_bauteil, N_up_bauteil)
    """
    best_N_up = 0.0
    best_N_down = None  # min über GEWICHT

    for k in lastfaelle:
        N_down, N_up = bewerte_lastfall_fuer_abheben(norm, k, protokoll=protokoll, kontext=base_ctx)

        if N_up > best_N_up:
            best_N_up = N_up

        if k.typ == Lasttyp.GEWICHT:
            best_N_down = N_down if best_N_down is None else min(best_N_down, N_down)

    if best_N_down is None:
        best_N_down = 0.0

    return best_N_down, best_N_up