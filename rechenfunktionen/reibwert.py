# reibwert.py
from __future__ import annotations

from typing import List, Optional, Sequence

from datenstruktur.enums import MaterialTyp
from datenstruktur.zwischenergebnis import Zwischenergebnis
from materialdaten.catalog import catalog

def reibwert(materialfolge: Sequence[Optional[MaterialTyp]]) -> Zwischenergebnis:
    # 1) None rausfiltern
    cleaned: List[MaterialTyp] = [m for m in materialfolge if m is not None]
    if len(cleaned) < 2:
        raise ValueError("Es werden mindestens zwei reale Materialien benötigt.")

    # 2) Reibwerte Quellen ermitteln
    einzelwerte: List[float] = []
    quelle_einzelwerte: List[str] = []

    for i in range(len(cleaned) - 1):
        a, b = cleaned[i], cleaned[i + 1]

        spec = catalog.get_reibwert(a, b)  # ReibwertSpec
        einzelwerte.append(spec.reibwert)
        quelle_einzelwerte.append(spec.quelle)

    # 3) effektiver Reibwert ist das Minimum
    reibwert_eff = min(einzelwerte)

    # 4) in Zwischenergebnis schreiben
    return Zwischenergebnis(
        wert=reibwert_eff,
        formel="µ_eff = min(µ_i)",
        quelle_formel="Konservatives Verfahren: kleinster Reibwert maßgebend.",
        formelzeichen=["---", "---"],
        quelle_formelzeichen=["---"],
        einzelwerte=einzelwerte,
        quelle_einzelwerte=quelle_einzelwerte,
    )
