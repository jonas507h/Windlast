# ======================================================================
#  PROTOKOLLIERUNG – Anleitung (How-To)
#  Ziel: Einheitlich Fehlermeldungen, Warnungen, Hinweise und Doku-Einträge
#        in einem Rechenlauf erfassen und in das Protokoll schreiben.
#  Quelle/Beispiel: rechenfunktionen/schlankheit.py
# ======================================================================

from ..windlast_CORE.datenstruktur.enums import Severity
from ..windlast_CORE.datenstruktur.zwischenergebnis import (
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
    Zwischenergebnis,
)

# ----------------------------------------------------------------------
#  GRUNDPRINZIP
# ----------------------------------------------------------------------
# - Jede Rechenfunktion bekommt (optional) zwei Parameter:
#       protokoll : Protokoll
#       kontext   : dict
# - Meldungen oder Dokumentationseinträge werden *immer* mit diesen
#   Parametern weitergereicht.
#
# - Kontext enthält z. B.:
#       { "funktion": "schlankheit", "objekttyp": "TRAVERSE", "norm": "DIN_EN_1991_1_4_2010_12" }
#
# - protokoll wird an zentraler Stelle (z. B. pro Normlauf) erzeugt:
#
#       prot = make_protokoll()
#       result = schlankheit(..., protokoll=prot, kontext={"norm": norm.name})
#       messages = collect_messages(prot)
#
# ----------------------------------------------------------------------


# ======================================================================
# 1. FEHLER UND WARNUNGEN PROTOKOLLIEREN
# ======================================================================

def _example_validate_input(punkte, *, protokoll: Protokoll, kontext: dict) -> bool:
    if not punkte or len(punkte) < 2:
        # Fachlicher Eingabefehler -> Severity.ERROR
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="INPUT/POINTS_MISSING",
            text="Es wurden weniger als zwei Punkte übergeben.",
            kontext=merge_kontext(kontext, {"phase": "VALIDATION", "param": "punkte"}),
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Geometrieprüfung",
                wert=float("nan"),
                einzelwerte=[len(punkte) if punkte else 0],
            ),
            kontext=merge_kontext(kontext, {"nan": True}),
        )
        return False
    return True


# ======================================================================
# 2. WARNUNGEN UND HINWEISE
# ======================================================================
# Für grenzwertige Situationen oder Kappungen.
# Beispiel: Wenn eine Größe außerhalb eines definierten Bereichs liegt.

def _example_extrapolation(faktor, laenge, protokoll, kontext):
    if laenge < 15.0 or laenge > 50.0:
        protokolliere_msg(
            protokoll,
            severity=Severity.WARN,
            code="SCHLANKHEIT/EXTRAPOLATION",
            text=f"Faktor via Extrapolation für L={laenge:.3f} außerhalb [15, 50].",
            kontext=merge_kontext(kontext, {
                "phase": "ZWISCHENWERTE",
                "bounds": [15.0, 50.0],
                "laenge": laenge,
                "faktor": faktor,
            }),
        )


# ======================================================================
# 3. INFO-MELDUNGEN
# ======================================================================
# Für interne Berechnungsentscheidungen, z. B. Kappung auf Maximalwert.

def _example_clamping(rechenwert, wert, protokoll, kontext):
    if wert < rechenwert:
        protokolliere_msg(
            protokoll,
            severity=Severity.INFO,
            code="SCHLANKHEIT/CLAMP_70",
            text=f"Schlankheit auf 70 gekappt (Rechenwert {rechenwert:.3f}).",
            kontext=merge_kontext(kontext, {
                "phase": "ZWISCHENWERTE",
                "rechenwert": rechenwert,
                "lambda": wert,
            }),
        )


# ======================================================================
# 4. ZWISCHENERGEBNIS DOKUMENTIEREN
# ======================================================================
# Jeder fachlich relevante Wert (ob NaN oder berechnet) wird als
# DocBundle im Protokoll abgelegt. Das erleichtert spätere PDF-Ausgabe.

def _example_doc_entry(title, wert, einzelwerte, protokoll, kontext):
    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(
            titel=title,
            wert=wert,
            einzelwerte=einzelwerte,
            # optional:
            # formel="λ = f(L) * L / h",
            # quelle_formel="DIN EN 1991-1-4:2010-12, Tab. 7.3"
        ),
        kontext=merge_kontext(kontext, {"phase": "ZWISCHENWERTE"}),
    )


# ======================================================================
# 5. KOMPLETTE RECHENFUNKTION MIT PROTOKOLLIERUNG
# ======================================================================

def schlankheit_beispiel(punkte, laenge, hoehe, *, protokoll=None, kontext=None) -> Zwischenergebnis:
    """
    Vollständiges Beispiel: Fachliche Prüfung + Berechnung + Logging.
    """
    ctx = merge_kontext(kontext, {"funktion": "schlankheit", "objekttyp": "TRAVERSE"})

    # Eingabevalidierung
    if not _example_validate_input(punkte, protokoll=protokoll, kontext=ctx):
        return Zwischenergebnis(wert=float("nan"))

    # Interpolation und Warnungen
    faktor = 1.7  # (Beispielwert)
    _example_extrapolation(faktor, laenge, protokoll, ctx)

    # Berechnung
    rechenwert = faktor * (laenge / hoehe)
    wert = min(rechenwert, 70.0)
    _example_clamping(rechenwert, wert, protokoll, ctx)

    # Dokumentation
    _example_doc_entry("Schlankheit λ", wert, [laenge, hoehe], protokoll, ctx)

    # Rückgabe
    return Zwischenergebnis(wert=wert)


# ======================================================================
# 6. SEVERITY-STUFEN (Richtlinien)
# ======================================================================
#  ERROR : fachlicher Fehler → Ergebnis i. d. R. NaN zurück
#  WARN  : Werte geklemmt oder extrapoliert, Ergebnis aber nutzbar
#  HINT  : Entscheidung, Heuristik, alternative Szenarien
#  INFO  : Zusatzinformation, keine Relevanz für Ergebnisbewertung
#
#  Alle Einträge werden zentral über das Protokoll gesammelt und
#  im StandsicherheitErgebnis unter `reasons` abgelegt.
#
# ======================================================================
