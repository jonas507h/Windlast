from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Hashable
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.rechenfunktionen.geom3d import Vec3

@dataclass
class LastSet:
    winkel_deg: float
    windrichtung: Vec3
    kraefte_nach_element: Dict[str, List[Kraefte]]

@dataclass
class LastPool:
    nach_winkel: Dict[int, LastSet] = field(default_factory=dict)  # key: int(round(winkel_deg*1e4))