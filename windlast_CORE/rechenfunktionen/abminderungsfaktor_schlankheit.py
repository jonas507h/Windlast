# rechenfunktionen/abminderungsfaktor_schlankheit.py
from __future__ import annotations
from typing import Tuple, Dict, Callable, Optional
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity

from windlast_CORE.rechenfunktionen.interpolation import (
    clamp_range,
    bilinear_interpolate_grid,
)

_X_Schlankheit: Tuple[float, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70)
_Y_Voelligkeitsgrad:   Tuple[float, ...] = (1.0, 0.95, 0.9, 0.5, 0.1)
_Z_Abminderungsfaktor: Tuple[Tuple[float, ...], ...] = (
    (0.60, 0.63, 0.645, 0.66, 0.67, 0.675, 0.68, 0.685, 0.69, 0.695, 0.775, 0.82, 0.85, 0.875, 0.90, 0.92),
    (0.73, 0.75, 0.76, 0.77, 0.775, 0.78, 0.79, 0.795, 0.80, 0.805, 0.85,  0.88, 0.90, 0.92, 0.93, 0.94),
    (0.825,0.84, 0.85, 0.855,0.86, 0.865,0.87, 0.875,0.875,0.88, 0.91,  0.92, 0.935,0.94, 0.95, 0.96),
    (0.885,0.89, 0.895,0.90, 0.905,0.905,0.91, 0.91, 0.915,0.915,0.935, 0.945,0.95, 0.96, 0.965,0.97),
    (0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.995, 0.995,0.995,1.0, 1.0, 1.0),
)

def _validate_inputs(objekttyp: ObjektTyp, schlankheit: float, voelligkeitsgrad: float) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if schlankheit <= 0:
        raise ValueError("schlankheit muss > 0 sein.")
    if not (0.0 <= voelligkeitsgrad <= 1.0):
        raise ValueError("voelligkeitsgrad muss im Bereich [0,1] liegen.")

def _abminderungsfaktor_schlankheit_default(
    objekttyp: ObjektTyp,
    schlankheit: float,
    voelligkeitsgrad: float,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    """
    Bilineare Interpolation des Abminderungsfaktors auf Tabelle (λ vs. φ).
    Werte außerhalb des Tabellenbereichs werden auf den Randbereich geklemmt.
    Der Objekttyp ist zzt. ohne Einfluss (Platzhalter für zukünftige Spezialisierungen).
    """
    base_ctx = merge_kontext(kontext, {
        "funktion": "abminderungsfaktor_schlankheit",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
    })

    # Originale Eingaben merken für Logging
    lam_orig = schlankheit
    phi_orig = voelligkeitsgrad

    # Clamp auf Tabellenbereiche
    x = clamp_range(schlankheit, _X_Schlankheit[0], _X_Schlankheit[-1])
    if x != lam_orig:
        protokolliere_msg(
            protokoll,
            severity=Severity.WARN,
            code="ABM_SCHL/CLAMP_LAMBDA",
            text=f"Schlankheit λ von {lam_orig:.3f} auf {x:.3f} geklemmt.",
            kontext=merge_kontext(base_ctx, {"bounds_lambda": [_X_Schlankheit[0], _X_Schlankheit[-1]]}),
        )

    # Y-Achse für Interpolation aufsteigend sortieren
    y_desc = _Y_Voelligkeitsgrad
    y_inc = tuple(sorted(y_desc))  # (0.1, 0.5, 0.9, 0.95, 1.0)
    idx_map = [y_desc.index(v) for v in y_inc]
    z_inc = tuple(_Z_Abminderungsfaktor[i] for i in idx_map)

    y = clamp_range(voelligkeitsgrad, y_inc[0], y_inc[-1])
    if y != phi_orig:
        protokolliere_msg(
            protokoll,
            severity=Severity.WARN,
            code="ABM_SCHL/CLAMP_VOELLIGKEIT",
            text=f"Völligkeitsgrad φ von {phi_orig:.3f} auf {y:.3f} geklemmt.",
            kontext=merge_kontext(base_ctx, {"bounds_phi": [y_inc[0], y_inc[-1]]}),
        )

    wert = bilinear_interpolate_grid(_X_Schlankheit, y_inc, z_inc, x, y)

    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(
            titel="Abminderungsfaktor η_schlank",
            wert=wert,
            formel="bilinear λ–φ → η",
            quelle_formel="Projekt-/Tabellenwerte (λ×φ → Abminderungsfaktor)",
            formelzeichen=["η", "λ", "φ"],
            quelle_formelzeichen=["Projektinterne Bezeichnungen"],
            einzelwerte=[x, y],
        ),
        kontext=base_ctx,
    )

    return Zwischenergebnis(wert=wert)

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _abminderungsfaktor_schlankheit_default,
}

def abminderungsfaktor_schlankheit(
    norm: Norm,
    objekttyp: ObjektTyp,
    schlankheit: float,
    voelligkeitsgrad: float,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "abminderungsfaktor_schlankheit",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs(objekttyp, schlankheit, voelligkeitsgrad)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="ABM_SCHL/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Abminderungsfaktor η_schlank", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, schlankheit, voelligkeitsgrad,
        protokoll=protokoll, kontext=base_ctx,
    )
