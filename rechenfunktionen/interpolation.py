from __future__ import annotations
from typing import Sequence

def interpol_2D(x: Sequence[float], y: Sequence[float], xq: float) -> float:
    """
    Lineare Interpolation ähnlich Matlab interp1.
    Erwartet:
        - x: Stützstellen (aufsteigend sortiert)
        - y: Werte gleicher Länge
        - xq: Abszisse, an der interpoliert werden soll
    Gibt zurück:
        - Interpolierten Wert
    Extrapolation: gibt Randwert zurück (wie Matlab 'extrap' ohne Option).
    """
    if len(x) != len(y):
        raise ValueError("x und y müssen gleich lang sein.")
    if len(x) < 2:
        raise ValueError("mindestens zwei Stützstellen nötig.")

    # vor dem ersten Punkt → unterer Rand
    if xq <= x[0]:
        return y[0]
    # hinter dem letzten Punkt → oberer Rand
    if xq >= x[-1]:
        return y[-1]

    # passendes Intervall finden
    for i in range(len(x) - 1):
        if x[i] <= xq <= x[i+1]:
            t = (xq - x[i]) / (x[i+1] - x[i])
            return y[i] + t * (y[i+1] - y[i])

    # Sollte nie hier landen
    raise RuntimeError("Interpolation fehlgeschlagen.")