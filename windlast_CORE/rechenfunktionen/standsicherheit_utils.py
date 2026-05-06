import math
from typing import List, Tuple, Optional, Sequence, Iterable, Dict
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektor_zwischen_punkten, vektor_normieren, einheitsvektor_aus_winkeln, konvexe_huelle_xy, moment_einzelkraft_um_achse, vektor_laenge
from windlast_CORE.datenstruktur.objekte3d import Achse
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.enums import Norm, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.zwischenergebnis import Protokoll, protokolliere_msg, merge_breadcrumb, bc_step, protokolliere_ergebnis, set_winner
from windlast_CORE.rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from windlast_CORE.datenstruktur.lastpool import LastPool, LastSet
from windlast_CORE.datenstruktur.konstanten import _EPS

def generiere_windrichtungen(
    anzahl: int = 4,
    *,
    startwinkel: float = 0.0,
    winkel: Optional[Sequence[float]] = None,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None
) -> List[Tuple[float, Vec3]]:
    base_bc = breadcrumb
    
    if winkel is not None:
        result = [(w, einheitsvektor_aus_winkeln(w, 0.0)) for w in winkel]
    else:
        if anzahl < 1:
            protokolliere_msg(protokoll, severity=Severity.ERROR,
                code="UTILS/WINDRICHTUNG_ANZAHL",
                text="Anzahl der Windrichtungen muss ≥ 1 sein.",
                breadcrumb=base_bc
                )
        winkelabstand = 360.0 / anzahl
        result = [(i * winkelabstand + startwinkel, einheitsvektor_aus_winkeln(i * winkelabstand + startwinkel, 0.0)) for i in range(anzahl)]

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
    breadcrumb: Optional[list] = None
) -> Dict[str, List[Kraefte]]:
    base_bc = merge_breadcrumb(breadcrumb, [bc_step("windrichtung", f"{windrichtung}")])

    # 1)Wind- & Gewichtskräfte aller Bauelemente holen
    kraefte_windrichtung: List[Kraefte] = []

    for idx, elem in enumerate(getattr(konstruktion, "bauelemente", []) or []):
        elem_bc = merge_breadcrumb(base_bc, [bc_step("element_id", f"{getattr(elem, 'element_id_intern', None)}")])
        # Gewicht
        fn_gewicht = getattr(elem, "gewichtskraefte", None)
        if callable(fn_gewicht):
            try:
                kraefte_gewicht = fn_gewicht(protokoll=protokoll, breadcrumb=elem_bc)
                if kraefte_gewicht:
                    kraefte_windrichtung.extend(kraefte_gewicht)
            except Exception as e:
                protokolliere_msg(
                    protokoll, severity=Severity.ERROR,
                    code="UTILS/GEWICHT_FAIL",
                    text=f"gewichtskraefte() für Element {idx} fehlgeschlagen: {e}",
                    breadcrumb=elem_bc,
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
                    breadcrumb=elem_bc,
                )
                if kraefte_wind:
                    kraefte_windrichtung.extend(kraefte_wind)
            except Exception as e:
                protokolliere_msg(
                    protokoll, severity=Severity.ERROR,
                    code="UTILS/WIND_FAIL",
                    text=f"windkraefte() für Element {idx} fehlgeschlagen: {e}",
                    breadcrumb=elem_bc,
                )
    
    # 2) Nach Bauelement gruppieren (erwartet: element_id_intern gesetzt)
    kraefte_nach_element: Dict[str, List[Kraefte]] = {}
    for k in kraefte_windrichtung:
        key = k.element_id_intern or f"elem_{id(k)}"  # Fallback, falls ID fehlt
        kraefte_nach_element.setdefault(key, []).append(k)

    return kraefte_nach_element

def _angle_key(winkel_deg: float) -> int:
    return int(round(winkel_deg * 1e4))

def obtain_pool(konstruktion, reset_berechnungen: bool, *, protokoll: Optional[Protokoll]=None, breadcrumb: Optional[list] = None) -> LastPool:
    base_bc = breadcrumb
    if reset_berechnungen or not hasattr(konstruktion, "_lastpool") or konstruktion._lastpool is None:
        konstruktion._lastpool = LastPool()
        protokolliere_msg(protokoll, severity=Severity.HINT,
                          code="UTILS/POOL_RESET",
                          text="Lastpool neu angelegt/gesetzt (reset_berechnungen=True oder fehlte).",
                          breadcrumb=base_bc)
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
    breadcrumb: Optional[list] = None
) -> LastSet:
    base_bc = merge_breadcrumb(breadcrumb, [bc_step("winkel_deg", f"{winkel_deg}°")])

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
            breadcrumb=base_bc,
        )
        ls = LastSet(winkel_deg=winkel_deg, windrichtung=windrichtung, kraefte_nach_element=kbe)
        pool.nach_winkel[key] = ls
    return ls

# Kippsicherheit Utils --------------------------------------------

def sammle_kippachsen(konstruktion, *, protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None) -> List[Achse]:
    base_bc = breadcrumb
    eckpunkte: List[Vec3] = []

    for idx, obj in enumerate(getattr(konstruktion, "bauelemente", [])):
        ep = getattr(obj, "eckpunkte", None)
        if callable(ep):
            try:
                punkte = ep(protokoll=protokoll, breadcrumb=merge_breadcrumb(base_bc, [bc_step("element_id", f"{getattr(obj, 'element_id_intern', None)}")]))
            except TypeError:
                # alte Signatur ohne protokoll/kontext
                punkte = ep()
            if punkte:
                eckpunkte.extend(punkte)

    if len(eckpunkte) < 3:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NO_POINTS",
            text="Zu wenige Eckpunkte für die Bestimmung von Kippachsen (min. 3).",
            breadcrumb=base_bc,
        )
        return []

    achsen = kippachsen_aus_eckpunkten(eckpunkte, include_Randpunkte=False)
    protokolliere_ergebnis(
        protokoll,
        breadcrumb=base_bc,
        name="anz_kippachsen",
        wert=len(achsen),
        label="Anzahl Kippachsen"
    )
    return achsen

def kippachsen_aus_eckpunkten(
    punkte: List[Vec3], *, include_Randpunkte: bool = False,
    protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
) -> List[Achse]:
    base_bc = breadcrumb

    if len(punkte) < 3:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/POINTS_LT3",
            text="Mindestens 3 Punkte erforderlich, um Kippachsen zu bestimmen.",
            breadcrumb=base_bc,
        )
        return []
    
    huelle = konvexe_huelle_xy(punkte)

    if len(huelle) < 2:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/HULL_LT2",
            text="Konvexe Hülle enthält weniger als 2 Eckpunkte.",
            breadcrumb=base_bc,
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

    return kippachsen

def bewerte_lastfall_fuer_achse(
    norm: Norm, achse: Achse, lastfall: Kraefte,
    *, protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
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

    base_bc = merge_breadcrumb(breadcrumb, [bc_step("lasttyp", f"{getattr(lastfall, 'typ', None)}")])

    Einzelkraefte: Sequence[Vec3] = lastfall.Einzelkraefte
    Angriffspunkte: Sequence[Vec3] = lastfall.Angriffspunkte_Einzelkraefte

    if Angriffspunkte is None or len(Angriffspunkte) != len(Einzelkraefte):
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="KIPP/NO_ATTACK_POINTS",
            text="Angriffspunkte der Einzelkräfte fehlen oder ungleich lang.",
            breadcrumb=base_bc,
        )
        return 0.0, 0.0
    
    kipp_sum = 0.0
    stand_sum = 0.0

    for Kraft, Punkt in zip(Einzelkraefte, Angriffspunkte):
        # 1) Moment um die Achse (Skalar, Rechtsschraube) …
        m_kipp = moment_einzelkraft_um_achse(achse, Kraft, Punkt)

        # 2) Sicherheitsbeiwert nach Günstigkeit bestimmen
        ist_guenstig = (m_kipp <= _EPS)
        gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig, protokoll=protokoll, breadcrumb=base_bc).wert

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
    breadcrumb: Optional[list] = None
) -> Tuple[float, float]:
    base_bc = breadcrumb

    wind_lastfall_index = -1
    best_wind_index = None
    gewicht_lastfall_index = -1
    best_gewicht_index = None
    other_lastfall_index = -1
    best_other_index = None

    best_wind_kipp = -math.inf
    best_wind_stand = 0.0
    best_gew_kipp = -math.inf
    best_gew_stand = 0.0
    best_other_kipp = -math.inf
    best_other_stand = 0.0

    for k in lastfaelle:
        kipp, stand = bewerte_lastfall_fuer_achse(norm, achse, k, protokoll=protokoll, breadcrumb=base_bc)

        if k.typ == Lasttyp.WIND:
            wind_lastfall_index += 1
            if (kipp - stand) > (best_wind_kipp - best_wind_stand):
                best_wind_kipp = kipp
                best_wind_stand = stand
                best_wind_index = wind_lastfall_index
                lasttyp = "WIND"
                lastfall_index = wind_lastfall_index
        elif k.typ == Lasttyp.GEWICHT:
            gewicht_lastfall_index += 1
            if (kipp - stand) > (best_gew_kipp - best_gew_stand):
                best_gew_kipp = kipp
                best_gew_stand = stand
                best_gewicht_index = gewicht_lastfall_index
                lasttyp = "GEWICHT"
                lastfall_index = gewicht_lastfall_index
        else:
            other_lastfall_index += 1
            if (kipp - stand) > (best_other_kipp - best_other_stand):
                best_other_kipp = kipp
                best_other_stand = stand
                best_other_index = other_lastfall_index
                lasttyp = "ANDERE"
                lastfall_index = other_lastfall_index

        lastfall_bc = merge_breadcrumb(base_bc, [bc_step("lasttyp", lasttyp), bc_step("lastfall_index", lastfall_index)])

        # --- Pro Lastfall protokollieren: Kipp/Stand (untergeordnet) ---
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_kippmoment",
            wert=kipp,
            label=f"Kippmoment M_K (Lastfall {lasttyp} #{lastfall_index})",
            einheit="Nm"
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_standmoment",
            wert=stand,
            label=f"Standmoment M_St (Lastfall {lasttyp} #{lastfall_index})",
            einheit="Nm",
        )

    if best_wind_kipp == -math.inf:
        best_wind_kipp, best_wind_stand = 0.0, 0.0
    if best_gew_kipp == -math.inf:
        best_gew_kipp, best_gew_stand = 0.0, 0.0
    if best_other_kipp == -math.inf:
        best_other_kipp, best_other_stand = 0.0, 0.0

    if best_wind_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "WIND"), bc_step("lastfall_index", best_wind_index)]))
    if best_gewicht_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "GEWICHT"), bc_step("lastfall_index", best_gewicht_index)]))
    if best_other_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "ANDERE"), bc_step("lastfall_index", best_other_index)]))

    # Ergebnis für das Bauelement
    kipp_sum_bauteil = best_wind_kipp + best_gew_kipp + best_other_kipp
    stand_sum_bauteil = best_wind_stand + best_gew_stand + best_other_stand
    return kipp_sum_bauteil, stand_sum_bauteil

# Gleitsicherheit Utils ------------------------------

def ermittle_min_reibwert(
    norm: Norm, konstruktion,
    *, protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
) -> float:
    base_bc = breadcrumb
    """Liest μ aus allen Bodenplatten (Elem hat Methode reibwert()) und gibt das Minimum zurück.
       Falls keine Platte gefunden → 0.0 (konservativ)."""
    mu_werte: List[float] = []
    for idx, elem in enumerate(getattr(konstruktion, "bauelemente", []) or []):
        elem_bc = merge_breadcrumb(base_bc, [bc_step("element_id", getattr(elem, "element_id_intern", None))])

        reib_fn = getattr(elem, "reibwert_effektiv", None)
        if not callable(reib_fn):
            continue

        try:
            mu = reib_fn(norm, protokoll=protokoll, breadcrumb=elem_bc)
            if mu is not None:
                mu_werte.append(float(mu))
        except Exception as e:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="GLEIT/MU_READ_FAIL",
                text=f"Reibwert-Ermittlung für Element {idx} fehlgeschlagen: {e}",
                breadcrumb=elem_bc,
            )

    if not mu_werte:
        # protokolliere_msg(
        #     protokoll, severity=Severity.WARN, code="GLEIT/NO_PLATE_MU",
        #     text="Kein Reibwert gefunden – setze konservativ μ=0.",
        #     breadcrumb=base_bc,
        # )
        return 0.0

    mu_min = min(mu_werte)
    return mu_min

def bewerte_lastfall_fuer_gleiten(
    norm: Norm, lastfall: Kraefte,
    *, protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
) -> Tuple[Vec3, float, float]:
    base_bc = breadcrumb
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

    for Kraft in Einzelkraefte:
        fx = Kraft[0]
        fy = Kraft[1]
        fz = Kraft[2]

        gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False, protokoll=protokoll, breadcrumb=base_bc).wert
        Hx += gamma * fx
        gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False, protokoll=protokoll, breadcrumb=base_bc).wert
        Hy += gamma * fy

        if fz > _EPS:
            gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False, protokoll=protokoll, breadcrumb=base_bc).wert
            N_up += gamma * fz
        elif fz < -_EPS:
            gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig=True, protokoll=protokoll, breadcrumb=base_bc).wert
            N_down += gamma * (-fz)

    H_vec: Vec3 = (Hx, Hy, Hz)

    return H_vec, N_down, N_up

def gleit_envelope_pro_bauelement(
    norm: Norm, lastfaelle: Iterable[Kraefte],
    *, protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
) -> Tuple[Vec3, float, float]:
    base_bc = breadcrumb

    wind_lastfall_index = -1
    best_wind_index = None
    gewicht_lastfall_index = -1
    best_gewicht_index = None

    best_H_vec: Vec3 = (0.0, 0.0, 0.0)
    best_H_betrag = -math.inf
    best_N_up = 0.0
    best_N_down = None
    best_Ndown_minus_Nup = None

    for k in lastfaelle:
        H_vec, N_down, N_up = bewerte_lastfall_fuer_gleiten(norm, k, protokoll=protokoll, breadcrumb=base_bc)
        H_betrag = vektor_laenge(H_vec)

        if k.typ == Lasttyp.WIND:
            wind_lastfall_index += 1
            lastfall_index = wind_lastfall_index
            lasttyp = "WIND"

            lastfall_bc = merge_breadcrumb(base_bc, [bc_step("lasttyp", lasttyp), bc_step("lastfall_index", lastfall_index)])

            if H_betrag > best_H_betrag:
                best_H_betrag = H_betrag
                best_H_vec = H_vec
                best_N_up = N_up
                best_wind_index = wind_lastfall_index

        if k.typ == Lasttyp.GEWICHT:
            gewicht_lastfall_index += 1
            lastfall_index = gewicht_lastfall_index
            lasttyp = "GEWICHT"

            lastfall_bc = merge_breadcrumb(base_bc, [bc_step("lasttyp", lasttyp), bc_step("lastfall_index", lastfall_index)])

            n_eff = N_down - N_up
            if best_Ndown_minus_Nup is None or n_eff < best_Ndown_minus_Nup:
                best_Ndown_minus_Nup = n_eff
                best_N_down = N_down
                best_gewicht_index = gewicht_lastfall_index


        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_horizontalkraft_vektor",
            wert=H_vec,
            label="Horizontalkraft-Vektor H",
            einheit="N"
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_horizontalkraft_betrag",
            wert=H_betrag,
            label="Horizontalkraft-Betrag |H|",
            einheit="N"
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_normalkraft_down",
            wert=N_down,
            label="Normalkraft N_down",
            einheit="N"
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_normalkraft_up",
            wert=N_up,
            label="Normalkraft N_up",
            einheit="N"
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_normalkraft_effektiv",
            wert=N_down - N_up,
            label="Effektive Normalkraft N_down - N_up",
            formelzeichen="N_eff",
            formel="N_eff = N_down - N_up",
            einheit="N"
        )

    else:
        pass

    if best_N_down is None:
        best_N_down = 0.0

    if best_wind_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "WIND"), bc_step("lastfall_index", best_wind_index)]))
    if best_gewicht_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "GEWICHT"), bc_step("lastfall_index", best_gewicht_index)]))

    return best_H_vec, best_N_down, best_N_up

# Abhebesicherheit Utils -----------------------------------

def bewerte_lastfall_fuer_abheben(
    norm: Norm, lastfall: Kraefte, *,
    protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
) -> Tuple[float, float]:
    base_bc = breadcrumb
    """
    Zerlegt einen Lastfall in:
      N_down (günstig, NACH UNTEN; nur aus GEWICHT mit γ_günstig, als positive Größe),
      N_up   (ungünstig, NACH OBEN; aus allen Lastfällen mit γ_ungünstig, als positive Größe).
    Rückgabe: (N_down, N_up)
    """
    N_down = 0.0
    N_up = 0.0

    for F in lastfall.Einzelkraefte:
        fz = F[2]
        if fz > _EPS:
            # nach oben → ungünstig
            gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False, protokoll=protokoll, breadcrumb=base_bc).wert
            N_up += gamma * fz
        elif fz < -_EPS:
            # nach unten → günstig, positive Magnitude
            gamma = sicherheitsbeiwert(norm, lastfall, ist_guenstig=True, protokoll=protokoll, breadcrumb=base_bc).wert
            N_down += gamma * (-fz)

    return N_down, N_up


def abhebe_envelope_pro_bauelement(
    norm: Norm, lastfaelle: Iterable[Kraefte], *,
    protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None
) -> Tuple[float, float]:
    base_bc = breadcrumb

    wind_lastfall_index = -1
    best_wind_index = None
    best_wind_N_up = -math.inf
    best_wind_N_down = 0.0

    gewicht_lastfall_index = -1
    best_gewicht_index = None
    best_gewicht_N_up = -math.inf
    best_gewicht_N_down = 0.0

    for k in lastfaelle:
        N_down, N_up = bewerte_lastfall_fuer_abheben(norm, k, protokoll=protokoll, breadcrumb=base_bc)

        if k.typ == Lasttyp.WIND:
            wind_lastfall_index += 1
            lastfall_index = wind_lastfall_index
            lasttyp = "WIND"

            if (N_up - N_down) > (best_wind_N_up - best_wind_N_down):
                best_wind_N_up = N_up
                best_wind_N_down = N_down
                best_wind_index = wind_lastfall_index

        if k.typ == Lasttyp.GEWICHT:
            gewicht_lastfall_index += 1
            lastfall_index = gewicht_lastfall_index
            lasttyp = "GEWICHT"

            if (N_up - N_down) > (best_gewicht_N_up - best_gewicht_N_down):
                best_gewicht_N_up = N_up
                best_gewicht_N_down = N_down
                best_gewicht_index = gewicht_lastfall_index

        lastfall_bc = merge_breadcrumb(base_bc, [bc_step("lasttyp", lasttyp), bc_step("lastfall_index", lastfall_index)])

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_normalkraft_down",
            wert=N_down,
            label="Normalkraft N_down",
            einheit="N"
        )

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=lastfall_bc,
            name="lastfall_normalkraft_up",
            wert=N_up,
            label="Normalkraft N_up",
            einheit="N"
        )

    else:
        pass

    if best_wind_N_up == -math.inf:
        best_wind_N_up, best_wind_N_down = 0.0, 0.0
    if best_gewicht_N_up == -math.inf:
        best_gewicht_N_down, best_gewicht_N_up = 0.0, 0.0

    best_N_up = best_wind_N_up + best_gewicht_N_up
    best_N_down = best_wind_N_down + best_gewicht_N_down


    if best_wind_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "WIND"), bc_step("lastfall_index", best_wind_index)]))

    if best_gewicht_index is not None:
        set_winner(protokoll, merge_breadcrumb(base_bc, [bc_step("lasttyp", "GEWICHT"), bc_step("lastfall_index", best_gewicht_index)]))

    return best_N_down, best_N_up