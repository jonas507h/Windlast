import math
from typing import List, Tuple, Optional, Sequence, Iterable, Dict
from rechenfunktionen.geom3d import Vec3, vektor_zwischen_punkten, vektor_normieren, einheitsvektor_aus_winkeln, konvexe_huelle_xy, moment_einzelkraft_um_achse, vektor_laenge
from datenstruktur.objekte3d import Achse
from datenstruktur.kraefte import Kraefte
from datenstruktur.enums import Norm, Lasttyp, Variabilitaet
from rechenfunktionen.sicherheitsbeiwert import sicherheitsbeiwert
from datenstruktur.lastpool import LastPool, LastSet

_EPS = 1e-9

def generiere_windrichtungen(
    anzahl: int = 4,
    *,
    startwinkel: float = 0.0,
    winkel: Optional[Sequence[float]] = None
    ) -> List[Tuple[float, Vec3]]:
    
    if winkel is not None:
        return [(w, einheitsvektor_aus_winkeln(w, 0.0)) for w in winkel]
    if anzahl < 1:
        raise ValueError("Anzahl der Windrichtungen muss mindestens 1 sein.")
    winkelabstand = 360.0 / anzahl
    return [(i * winkelabstand + startwinkel, einheitsvektor_aus_winkeln(i * winkelabstand + startwinkel, 0.0)) for i in range(anzahl)]

def ermittle_kraefte_pro_windrichtung(
    konstruktion,
    norm: Norm,
    windrichtung: Vec3,
    staudruecke: Sequence[float],
    obergrenzen: Sequence[float],
    konst
) -> Dict[str, List[Kraefte]]:  # <- Rückgabetyp korrigiert
    # 1)Wind- & Gewichtskräfte aller Bauelemente holen
    kraefte_windrichtung: List[Kraefte] = []

    for elem in (getattr(konstruktion, "bauelemente", None) or []):
        # Gewicht
        fn_gewicht = getattr(elem, "gewichtskraefte", None)
        if callable(fn_gewicht):
            kraefte_gewicht = fn_gewicht()  # -> List[Kraefte]
            if kraefte_gewicht:
                kraefte_windrichtung.extend(kraefte_gewicht)

        # Wind
        fn_wind = getattr(elem, "windkraefte", None)
        if callable(fn_wind):
            kraefte_wind = fn_wind(
                norm=norm,
                windrichtung=windrichtung,
                staudruecke=staudruecke,
                obergrenzen=obergrenzen,
                konst=konst,
            )  # -> List[Kraefte]
            if kraefte_wind:
                kraefte_windrichtung.extend(kraefte_wind)
    
    # 2) Nach Bauelement gruppieren (erwartet: element_id_intern gesetzt)
    kraefte_nach_element: Dict[str, List[Kraefte]] = {}
    for k in kraefte_windrichtung:
        key = k.element_id_intern or f"elem_{id(k)}"  # Fallback, falls ID fehlt
        kraefte_nach_element.setdefault(key, []).append(k)

    return kraefte_nach_element

def _angle_key(winkel_deg: float) -> int:
    return int(round(winkel_deg * 1e4))

def obtain_pool(konstruktion, reset_berechnungen: bool) -> LastPool:
    if reset_berechnungen or not hasattr(konstruktion, "_lastpool") or konstruktion._lastpool is None:
        konstruktion._lastpool = LastPool()
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
    konst
) -> LastSet:
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
        )
        ls = LastSet(winkel_deg=winkel_deg, windrichtung=windrichtung, kraefte_nach_element=kbe)
        pool.nach_winkel[key] = ls
    return ls

# Kippsicherheit Utils --------------------------------------------

def sammle_kippachsen(konstruktion) -> List[Achse]:
    eckpunkte: List[Vec3] = []

    for obj in getattr(konstruktion, "bauelemente", []):
        ep = getattr(obj, "eckpunkte", None)
        if callable(ep):
            punkte = ep()
            if punkte:
                eckpunkte.extend(punkte)

    achsen = kippachsen_aus_eckpunkten(eckpunkte, include_Randpunkte=False)
    return achsen

def kippachsen_aus_eckpunkten(punkte: List[Vec3], *, include_Randpunkte: bool = False) -> List[Achse]:
    if len(punkte) < 3:
        raise ValueError("Mindestens 3 Punkte sind erforderlich, um Kippachsen zu bestimmen.")
    
    huelle = konvexe_huelle_xy(punkte)

    if len(huelle) < 2:
        raise ValueError("Die konvexe Hülle muss mindestens 2 Punkte enthalten.")
    
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

def bewerte_lastfall_fuer_achse(norm: Norm, achse: Achse, lastfall: Kraefte) -> Tuple[float, float]:
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

    Einzelkraefte: Sequence[Vec3] = lastfall.Einzelkraefte
    Angriffspunkte: Sequence[Vec3] = lastfall.Angriffspunkte_Einzelkraefte

    if Angriffspunkte is None or len(Angriffspunkte) != len(Einzelkraefte):
        raise ValueError(
            "Kraefte.angriffspunkte_einzelkraefte fehlt oder passt nicht zu Einzelkraefte."
        )

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
) -> Tuple[float, float]:
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

def ermittle_min_reibwert(konstruktion) -> float:
    """Liest μ aus allen Bodenplatten (Elem hat Methode reibwert()) und gibt das Minimum zurück.
       Falls keine Platte gefunden → 0.0 (konservativ)."""
    mu_werte: List[float] = []
    for elem in getattr(konstruktion, "bauelemente", []):
        reib_fn = getattr(elem, "reibwert", None)
        if callable(reib_fn):
            mu = reib_fn()
            if mu:
                mu_werte.append(float(mu))
    return min(mu_werte) if mu_werte else 0.0

def bewerte_lastfall_fuer_gleiten(norm: Norm, lastfall: Kraefte) -> Tuple[Vec3, float, float]:
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
    norm: Norm,
    lastfaelle: Iterable[Kraefte],
) -> Tuple[Vec3, float, float]:
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

def bewerte_lastfall_fuer_abheben(norm: Norm, lastfall: Kraefte) -> Tuple[float, float]:
    """
    Zerlegt einen Lastfall in:
      N_down (günstig, NACH UNTEN; nur aus GEWICHT mit γ_günstig, als positive Größe),
      N_up   (ungünstig, NACH OBEN; aus allen Lastfällen mit γ_ungünstig, als positive Größe).
    Rückgabe: (N_down, N_up)
    """
    N_down = 0.0
    N_up = 0.0

    gamma_unguenstig = sicherheitsbeiwert(norm, lastfall, ist_guenstig=False).wert
    gamma_guenstig = sicherheitsbeiwert(norm, lastfall, ist_guenstig=True).wert

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
    norm: Norm,
    lastfaelle: Iterable[Kraefte],
) -> Tuple[float, float]:
    """
    Element-konsistent:
      - N_up_bauteil = max (Auftrieb) über ALLE Lastfälle.
      - N_down_bauteil = min (Auflast) über GEWICHT-Lastfälle (ungünstig kleinster Wert).
    Rückgabe: (N_down_bauteil, N_up_bauteil)
    """
    best_N_up = 0.0
    best_N_down = None  # min über GEWICHT

    for k in lastfaelle:
        N_down, N_up = bewerte_lastfall_fuer_abheben(norm, k)

        if N_up > best_N_up:
            best_N_up = N_up

        if k.typ == Lasttyp.GEWICHT:
            best_N_down = N_down if best_N_down is None else min(best_N_down, N_down)

    if best_N_down is None:
        best_N_down = 0.0

    return best_N_down, best_N_up