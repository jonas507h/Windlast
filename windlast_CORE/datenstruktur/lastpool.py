from dataclasses import dataclass, field
from typing import Dict, List, Optional
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.rechenfunktionen.geom3d import Vec3

@dataclass
class LastSet:
    winkel_deg: float
    windrichtung: Vec3
    kraefte_nach_element: Dict[str, List[Kraefte]]

@dataclass
class LastPool:
    # fertige kombinierte LastSets: Gewicht + Wind je Richtung
    nach_winkel: Dict[int, LastSet] = field(default_factory=dict)

    # richtungsunabhängige Gewichtskräfte
    gewicht_nach_element: Optional[Dict[str, List[Kraefte]]] = None

    # richtungsabhängige Windkräfte, aber noch ohne Gewicht
    wind_nach_winkel: Dict[int, Dict[str, List[Kraefte]]] = field(default_factory=dict)