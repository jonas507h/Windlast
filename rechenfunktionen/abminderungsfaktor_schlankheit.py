from __future__ import annotations
from typing import Sequence, Tuple, Dict, Callable
import bisect
from datenstruktur.zwischenergebnis import Norm,Zwischenergebnis

# --- Tabellendaten ----------------------------------------------------------
_X_Schlankheit: Tuple[float, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70)
_Y_Voelligkeitsgrad:   Tuple[float, ...] = (1.0, 0.95, 0.9, 0.5, 0.1)  # abnehmend
_Z_Abminderungsfaktor: Tuple[Tuple[float, ...], ...] = (
    (0.60, 0.63, 0.645, 0.66, 0.67, 0.675, 0.68, 0.685, 0.69, 0.695, 0.775, 0.82, 0.85, 0.875, 0.90, 0.92),
    (0.73, 0.75, 0.76, 0.77, 0.775, 0.78, 0.79, 0.795, 0.80, 0.805, 0.85,  0.88, 0.90, 0.92, 0.93, 0.94),
    (0.825,0.84, 0.85, 0.855,0.86, 0.865,0.87, 0.875,0.875,0.88, 0.91,  0.92, 0.935,0.94, 0.95, 0.96),
    (0.885,0.89, 0.895,0.90, 0.905,0.905,0.91, 0.91, 0.915,0.915,0.935, 0.945,0.95, 0.96, 0.965,0.97),
    (0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.995, 0.995,0.995,1.0, 1.0, 1.0),
)

# --- Hilfsfunktionen --------------------------------------------------------

def _clamp(value: float, low: float, high: float) -> float: #Setzt Werte außerhalb von [low, high] auf die Grenzen
    return high if value > high else low if value < low else value

def _find_bracketing_indices(grid: Sequence[float], x: float) -> Tuple[int, int, float]: #Findet die Indizes der Gitterpunkte links und rechts von x und den Interpolationsfaktor t
    j = bisect.bisect_left(grid, x)
    if j <= 0:
        return 0, 0, 0.0
    if j >= len(grid):
        k = len(grid) - 1
        return k, k, 0.0
    i1 = j
    i0 = j - 1
    x0, x1 = grid[i0], grid[i1]
    t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
    return i0, i1, t

def _bilinear_interpolate(
    x_grid: Sequence[float],
    y_grid_inc: Sequence[float],
    z: Sequence[Sequence[float]],
    x: float,
    y: float,
) -> float:
    ix0, ix1, tx = _find_bracketing_indices(x_grid, x)
    iy0, iy1, ty = _find_bracketing_indices(y_grid_inc, y)

    z00 = z[iy0][ix0]
    z10 = z[iy0][ix1]
    z01 = z[iy1][ix0]
    z11 = z[iy1][ix1]

    zx0 = z00 + tx * (z10 - z00)
    zx1 = z01 + tx * (z11 - z01)
    return zx0 + ty * (zx1 - zx0)

# --- Eingabevalidierung ----------------------------------------------------------

def _validate_inputs(schlankheit: float, voelligkeitsgrad: float) -> None:
    if schlankheit <= 0:
        raise ValueError("schlankheit muss > 0 sein.")
    if not (0.0 <= voelligkeitsgrad <= 1.0):
        raise ValueError("voelligkeitsgrad muss im Bereich [0,1] liegen.")

# --- Hauptfunktion ----------------------------------------------------------

def _abminderungsfaktor_schlankheit_default(
    schlankheit: float,
    voelligkeitsgrad: float,
) -> Zwischenergebnis:
    """
    Bilineare Interpolation des Abminderungsfaktors.
    Erwartet direkt die Schlankheit λ und den Völligkeitsgrad v als Input.
    Werte außerhalb des Tabellenbereichs werden auf den Randbereich geklemmt.
    """

    # Clamp auf Tabellenbereiche
    x = _clamp(schlankheit, _X_Schlankheit[0], _X_Schlankheit[-1])

    # Y-Achse für Interpolation aufsteigend sortieren
    y_desc = _Y_Voelligkeitsgrad
    y_inc = tuple(sorted(y_desc))  # (0.1, 0.5, 0.9, 0.95, 1.0)

    idx_map = [y_desc.index(v) for v in y_inc]
    z_inc = tuple(_Z_Abminderungsfaktor[i] for i in idx_map)

    y = _clamp(voelligkeitsgrad, y_inc[0], y_inc[-1])

    wert = _bilinear_interpolate(_X_Schlankheit, y_inc, z_inc, x, y)

    return Zwischenergebnis(
        wert=wert,
        formel="---",
        quelle_formel="---",
        formelzeichen=["---", "---", "---"],
        quelle_formelzeichen=["---"]
    )

#zuweisung Norm -> Funktion
_DISPATCH: Dict[Norm, Callable[[float, float], Zwischenergebnis]] = {
    Norm.DEFAULT: _abminderungsfaktor_schlankheit_default,
}

def abminderungsfaktor_schlankheit(
    schlankheit: float,
    voelligkeitsgrad: float,
    norm: Norm = Norm.DEFAULT,
) -> Zwischenergebnis:
    _validate_inputs(schlankheit, voelligkeitsgrad)
    funktion = _DISPATCH.get(norm, _abminderungsfaktor_schlankheit_default)
    return funktion(schlankheit, voelligkeitsgrad)