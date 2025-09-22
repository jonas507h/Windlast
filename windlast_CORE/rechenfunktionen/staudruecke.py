from __future__ import annotations
from typing import Dict, Callable, Optional, List, Sequence, Union, Any, Tuple
import warnings

from datenstruktur.enums import Betriebszustand, Windzone, Schutzmassnahmen, Zeitfaktor, Norm
from datenstruktur.zeit import Dauer
from datenstruktur.zwischenergebnis import Zwischenergebnis_Liste
from datenstruktur.konstanten import _EPS
from datenstruktur.zeit import convert_dauer

# DIN EN 13814:2005-06 — Staudruck q [N/m²], Schlüssel: Obergrenze der Bauhöhe [m]
STAUDRUECKE_DIN_EN_13814_2005_06 = {
    Betriebszustand.IN_BETRIEB: {
        8.0:  200.0,
        20.0: 300.0,
        35.0: 350.0,
        50.0: 400.0,
    },
    Betriebszustand.AUSSER_BETRIEB: {
        8.0:  350.0,
        20.0: 500.0,
        35.0: 900.0,
        50.0: 1000.0,
    },
}

# DIN EN 17879:2024-08 — Staudruck q [N/m²], Schlüssel: Obergrenze der Bauhöhe [m]
STAUDRUECKE_DIN_EN_17879_2024_08 = {
    Betriebszustand.IN_BETRIEB: {
        5.0:  180.0,
        10.0: 250.0,
        15.0: 290.0,
        20.0: 320.0,
        25.0: 340.0,
        30.0: 360.0,
    },
    Betriebszustand.AUSSER_BETRIEB: {
        5.0:  450.0,
        10.0: 600.0,
        15.0: 690.0,
        20.0: 760.0,
        25.0: 820.0,
        30.0: 870.0,
    },
}

# DIN EN 1991-1-4:2010-12 — Geschwindigkeitsdruck q [N/m²]
# Keys: Obergrenze der Gebäudehöhe [m] (10.0, 18.0, 25.0)
GESCHWINDIGKEITSDRUCK_EN_1991_1_4_2010_12 = {
    Windzone.I_BINNENLAND: {
        10.0: 500.0,
        18.0: 650.0,
        25.0: 750.0,
    },
    Windzone.II_BINNENLAND: {
        10.0: 650.0,
        18.0: 800.0,
        25.0: 900.0,
    },
    Windzone.II_KUESTE: {
        10.0: 850.0,
        18.0: 1000.0,
        25.0: 1100.0,
    },
    Windzone.III_Binnenland: {
        10.0: 800.0,
        18.0: 950.0,
        25.0: 1100.0,
    },
    Windzone.III_KUESTE: {
        10.0: 1050.0,
        18.0: 1200.0,
        25.0: 1300.0,
    },
    Windzone.IV_BINNENLAND: {
        10.0: 950.0,
        18.0: 1150.0,
        25.0: 1300.0,
    },
    Windzone.IV_KUESTE: {
        10.0: 1250.0,
        18.0: 1400.0,
        25.0: 1550.0,
    },
    Windzone.IV_INSELN: {
        10.0: 1400.0,
    },
}


FAKTOREN_VORUEBERGENDER_ZUSTAND: dict[Dauer, dict[Schutzmassnahmen, float]] = {
    Dauer(3, Zeitfaktor.TAG): {
        Schutzmassnahmen.SCHUETZEND:   0.1,
        Schutzmassnahmen.VERSTAERKEND: 0.2,
        Schutzmassnahmen.KEINE:        0.5,
    },
    Dauer(3, Zeitfaktor.MONAT): {
        Schutzmassnahmen.SCHUETZEND:   0.2,
        Schutzmassnahmen.VERSTAERKEND: 0.3,
        Schutzmassnahmen.KEINE:        0.5,
    },
    Dauer(12, Zeitfaktor.MONAT): {
        Schutzmassnahmen.SCHUETZEND:   0.2,
        Schutzmassnahmen.VERSTAERKEND: 0.3,
        Schutzmassnahmen.KEINE:        0.6,
    },
    Dauer(24, Zeitfaktor.MONAT): {
        Schutzmassnahmen.SCHUETZEND:   0.2,
        Schutzmassnahmen.VERSTAERKEND: 0.4,
        Schutzmassnahmen.KEINE:        0.7,
    },
}

# ----------------------------
# Validation
# ----------------------------
def _validate_inputs(
    norm: Norm,
    konstruktion: Any,
    zustand: Union[Betriebszustand, Schutzmassnahmen],
    aufstelldauer: Optional[Dauer],
    windzone: Optional[Windzone],
) -> None:
    # Norm
    if not isinstance(norm, Norm):
        raise TypeError("norm muss vom Typ Norm sein.")

    # Konstruktion: nur prüfen, ob gesamthoehe() vorhanden ist
    gh = getattr(konstruktion, "gesamthoehe", None)
    if not callable(gh):
        raise ValueError("konstruktion muss eine Methode gesamthoehe() bereitstellen.")

    # zustand-Typ je Norm
    if norm in (Norm.DIN_EN_13814_2005_06, Norm.DIN_EN_17879_2024_08, Norm.DEFAULT):
        if not isinstance(zustand, Betriebszustand):
            raise TypeError("Für diese Norm wird zustand vom Typ Betriebszustand erwartet.")
        # windzone/aufstelldauer optional (werden hier nicht erzwungen)
    elif norm == Norm.DIN_EN_1991_1_4_2010_12:
        if not isinstance(zustand, Schutzmassnahmen):
            raise TypeError("Für DIN EN 1991-1-4:2010-12 wird zustand vom Typ Schutzmassnahmen erwartet.")
        if windzone is None:
            raise ValueError("Für DIN EN 1991-1-4:2010-12 muss windzone gesetzt sein.")
        # aufstelldauer darf None sein -> erlaubt
    else:
        raise NotImplementedError(f"Norm '{norm}' wird derzeit nicht unterstützt.")

# ----------------------------
# Funktion je Norm
# ----------------------------
def _winddruck_DinEn13814_2005_06(
    konstruktion: Any,
    zustand: Betriebszustand,
    aufstelldauer: Optional[Dauer],
    windzone: Optional[Windzone],
) -> Tuple[Zwischenergebnis_Liste, Zwischenergebnis_Liste]:
    # 1) Obergrenzen & Staudrücke für den gesetzten Betriebszustand
    try:
        daten_dict = STAUDRUECKE_DIN_EN_13814_2005_06[zustand]
    except KeyError as e:
        raise KeyError(f"Keine Staudruckdaten für Betriebszustand '{zustand.value}' gefunden.") from e

    # sortierte Obergrenzen und zugehörige q-Werte (in N/m²)
    obergrenzen: List[float] = sorted(daten_dict.keys())
    q_werte: List[float] = [daten_dict[o] for o in obergrenzen]

    # 2) Gesamthöhe prüfen
    h = float(konstruktion.gesamthoehe())
    max_obergrenze = obergrenzen[-1]
    if h > max_obergrenze + _EPS:
        raise ValueError(
            f"Gesamthöhe {h:.3f} m überschreitet die höchste Obergrenze {max_obergrenze:.3f} m "
            f"für DIN EN 13814:2005-06 ({zustand.value})."
        )

    # 3) Aufstelldauer in Monate umrechnen; Warnung wenn > 3 Monate (rechnet weiter)
    if aufstelldauer is not None:
        dauer_monate = convert_dauer(aufstelldauer.wert, aufstelldauer.einheit, Zeitfaktor.MONAT)
        if dauer_monate > 3.0 + _EPS:
            warnings.warn(
                f"Aufstelldauer {dauer_monate:.3f} Monate > 3 Monate; "
                f"Berechnung nach DIN EN 13814:2005-06 wird dennoch fortgesetzt."
            )

    # 4) Zwei Zwischenergebnisse bauen: (a) Obergrenzen, (b) Staudrücke
    zl_obergrenzen = Zwischenergebnis_Liste(
        wert=obergrenzen,
        formel="Obergrenzen z_max",
        quelle_formel="DIN EN 13814:2005-06 (Tabelle Staudruck q vs. Bauhöhe)",
        formelzeichen=["z_max"],
        quelle_formelzeichen=["DIN EN 13814:2005-06"],
        einzelwerte=None,
        quelle_einzelwerte=None,
    )

    zl_staudruecke = Zwischenergebnis_Liste(
        wert=q_werte,
        formel="q(z)",
        quelle_formel="DIN EN 13814:2005-06 (Tabelle Staudruck q vs. Bauhöhe)",
        formelzeichen=["q"],
        quelle_formelzeichen=["DIN EN 13814:2005-06"],
        einzelwerte=None,
        quelle_einzelwerte=None,
    )

    return zl_obergrenzen, zl_staudruecke

def _winddruck_DinEn17879_2024_08(
    konstruktion: Any,
    zustand: Betriebszustand,
    aufstelldauer: Optional[Dauer],
    windzone: Optional[Windzone],
) -> Tuple[Zwischenergebnis_Liste, Zwischenergebnis_Liste]:
    # 1) Obergrenzen & Staudrücke für den gesetzten Betriebszustand
    try:
        daten_dict = STAUDRUECKE_DIN_EN_17879_2024_08[zustand]
    except KeyError as e:
        raise KeyError(f"Keine Staudruckdaten für Betriebszustand '{zustand.value}' (DIN EN 17879:2024-08).") from e

    # sortierte Obergrenzen und zugehörige q-Werte (in N/m²)
    obergrenzen: List[float] = sorted(daten_dict.keys())
    q_werte: List[float] = [daten_dict[o] for o in obergrenzen]

    # 2) Gesamthöhe prüfen (muss ≤ höchste Obergrenze sein)
    h = float(konstruktion.gesamthoehe())
    max_obergrenze = obergrenzen[-1]
    if h > max_obergrenze + _EPS:
        raise ValueError(
            f"Gesamthöhe {h:.3f} m überschreitet die höchste Obergrenze {max_obergrenze:.3f} m "
            f"für DIN EN 17879:2024-08 ({zustand.value})."
        )

    # 3) (keine Aufstelldauer-Prüfung in 17879)

    # 4) Zwei Zwischenergebnisse: (a) Obergrenzen, (b) Staudrücke
    zl_obergrenzen = Zwischenergebnis_Liste(
        wert=obergrenzen,
        formel="Obergrenzen z_max",
        quelle_formel="DIN EN 17879:2024-08 (Tabelle Staudruck q vs. Bauhöhe)",
        formelzeichen=["z_max"],
        quelle_formelzeichen=["DIN EN 17879:2024-08"],
        einzelwerte=None,
        quelle_einzelwerte=None,
    )

    zl_staudruecke = Zwischenergebnis_Liste(
        wert=q_werte,
        formel="q(z)",
        quelle_formel="DIN EN 17879:2024-08 (Tabelle Staudruck q vs. Bauhöhe)",
        formelzeichen=["q"],
        quelle_formelzeichen=["DIN EN 17879:2024-08"],
        einzelwerte=None,
        quelle_einzelwerte=None,
    )

    return zl_obergrenzen, zl_staudruecke

def _geschwindigkeitsdruck_DinEn1991_1_4_2010_12(
    konstruktion: Any,
    zustand: Schutzmassnahmen,
    aufstelldauer: Optional[Dauer],
    windzone: Optional[Windzone],
) -> Tuple[Zwischenergebnis_Liste, Zwischenergebnis_Liste]:
    if windzone is None:
        raise ValueError("Windzone muss für DIN EN 1991-1-4:2010-12 gesetzt sein.")

    # 1) Höhenklassen & q für die gegebene Windzone holen
    try:
        zonen_daten = GESCHWINDIGKEITSDRUCK_EN_1991_1_4_2010_12[windzone]
    except KeyError as e:
        raise KeyError(f"Keine Geschwindigkeitsdruck-Daten für Windzone '{windzone.value}'.") from e

    obergrenzen_sorted: List[float] = sorted(zonen_daten.keys())  # z. B. [10.0, 18.0, 25.0]

    # 2) Gesamthöhe → passende Höhenklasse suchen (erste Obergrenze >= h)
    h = float(konstruktion.gesamthoehe())
    gueltige_obergrenze = next((z for z in obergrenzen_sorted if h <= z + _EPS), None)
    if gueltige_obergrenze is None:
        max_og = obergrenzen_sorted[-1]
        raise ValueError(
            f"Gesamthöhe {h:.3f} m überschreitet die höchste definierte Obergrenze {max_og:.3f} m "
            f"für DIN EN 1991-1-4:2010-12 (Zone: {windzone.value})."
        )

    q_basis = zonen_daten[gueltige_obergrenze]  # N/m²

    # 3) Optional: Abminderung
    q_eff = q_basis
    if aufstelldauer is not None:
        dauer_monate = convert_dauer(aufstelldauer.wert, aufstelldauer.einheit, Zeitfaktor.MONAT)

        # Obergrenzen (Monate) sortieren und erste passende "bis zu …" Kategorie wählen
        grenzen_sorted = sorted(
            FAKTOREN_VORUEBERGENDER_ZUSTAND.keys(),
            key=lambda d: convert_dauer(d.wert, d.einheit, Zeitfaktor.MONAT)
        )

        faktor = None
        for grenze in grenzen_sorted:
            grenze_monate = convert_dauer(grenze.wert, grenze.einheit, Zeitfaktor.MONAT)
            if dauer_monate <= grenze_monate + 1e-9:
                faktor = FAKTOREN_VORUEBERGENDER_ZUSTAND[grenze][zustand]
                break

        if faktor is not None:
            # Nur wenn innerhalb der Tabellenobergrenzen → Faktor anwenden und warnen
            warnings.warn(
                "Abminderungen der Windlasten sind bei fliegenden Bauten nicht zulässig. "
                "Der Abminderungsfaktor wird hier nur auf ausdrücklichen Wunsch angewendet."
            )
            q_eff = q_basis * faktor
        # else: Dauer oberhalb der höchsten Obergrenze → faktor=1.0 implizit, keine Warnung

    # 4) Zwei Zwischenergebnisse: (a) [q_eff], (b) [z_max]
    zl_obergrenzen = Zwischenergebnis_Liste(
        wert=[gueltige_obergrenze],
        formel="z_max (Klassen-Obergrenze zu h)",
        quelle_formel="DIN EN 1991-1-4:2010-12 (Zonen-Tabelle)",
        formelzeichen=["z_max"],
        quelle_formelzeichen=["DIN EN 1991-1-4:2010-12"],
        einzelwerte=None,
        quelle_einzelwerte=None,
    )
    zl_staudruecke = Zwischenergebnis_Liste(
        wert=[q_eff],
        formel="q(z=h)",
        quelle_formel="DIN EN 1991-1-4:2010-12 (Zonen-Tabelle); ggf. Faktor für vorübergehenden Zustand",
        formelzeichen=["q"],
        quelle_formelzeichen=["DIN EN 1991-1-4:2010-12"],
        einzelwerte=None,
        quelle_einzelwerte=None,
    )

    return zl_obergrenzen, zl_staudruecke

# ----------------------------
# Dispatch
# ----------------------------

_DISPATCH: Dict[Norm, Callable[..., Tuple[Zwischenergebnis_Liste, Zwischenergebnis_Liste]]] = {
    Norm.DEFAULT: _winddruck_DinEn13814_2005_06,
    Norm.DIN_EN_13814_2005_06: _winddruck_DinEn13814_2005_06,
    Norm.DIN_EN_17879_2024_08: _winddruck_DinEn17879_2024_08,
    Norm.DIN_EN_1991_1_4_2010_12: _geschwindigkeitsdruck_DinEn1991_1_4_2010_12,
}

# ----------------------------
# Hauptfunktion
# ----------------------------
def staudruecke(
    norm: Norm,
    konstruktion: Any,
    zustand: Union[Betriebszustand, Schutzmassnahmen],
    *,
    aufstelldauer: Optional[Dauer] = None,
    windzone: Optional[Windzone] = None,
) -> Tuple[Zwischenergebnis_Liste, Zwischenergebnis_Liste]:
    _validate_inputs(norm, konstruktion, zustand, aufstelldauer, windzone)
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(konstruktion, zustand, aufstelldauer, windzone)