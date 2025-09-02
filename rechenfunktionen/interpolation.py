# rechenfunktionen/interpolation.py
from __future__ import annotations
from typing import Sequence, Tuple
import bisect

def interpol_2D(x: Sequence[float], y: Sequence[float], xq: float) -> float:
    if len(x) != len(y):
        raise ValueError("x und y müssen gleich lang sein.")
    if len(x) < 2:
        raise ValueError("mindestens zwei Stützstellen nötig.")
    if xq <= x[0]:
        return y[0]
    if xq >= x[-1]:
        return y[-1]
    for i in range(len(x) - 1):
        if x[i] <= xq <= x[i+1]:
            t = (xq - x[i]) / (x[i+1] - x[i])
            return y[i] + t * (y[i+1] - y[i])
    raise RuntimeError("Interpolation fehlgeschlagen.")

# --- NEU: Grid-Helfer für bilineare Interpolation --------------------------------

def clamp_range(value: float, low: float, high: float) -> float:
    """Begrenzt value auf [low, high]."""
    return high if value > high else low if value < low else value

def find_bracketing_indices(grid: Sequence[float], x: float) -> Tuple[int, int, float]:
    """
    Liefert (i0, i1, t) mit grid[i0] <= x <= grid[i1] und t in [0,1] als Interpolationsfaktor.
    Außerhalb wird auf die Randzellen geklemmt und t=0 geliefert.
    """
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

def bilinear_interpolate_grid(
    x_grid: Sequence[float],
    y_grid_inc: Sequence[float],
    z: Sequence[Sequence[float]],
    x: float,
    y: float,
) -> float:
    """
    Bilineare Interpolation auf einem Rechteckgitter.
    y_grid_inc muss aufsteigend sortiert sein. z hat Shape [len(y_grid_inc)][len(x_grid)].
    """
    ix0, ix1, tx = find_bracketing_indices(x_grid, x)
    iy0, iy1, ty = find_bracketing_indices(y_grid_inc, y)

    z00 = z[iy0][ix0]
    z10 = z[iy0][ix1]
    z01 = z[iy1][ix0]
    z11 = z[iy1][ix1]

    zx0 = z00 + tx * (z10 - z00)
    zx1 = z01 + tx * (z11 - z01)
    return zx0 + ty * (zx1 - zx0)
