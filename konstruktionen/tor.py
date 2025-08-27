from dataclasses import dataclass, field
from typing import List
from bauelemente import Bodenplatte, Traversenstrecke
from rechenfunktionen import (
    kippsicherheit as _kippsicherheit,
    gleitsicherheit as _gleitsicherheit,
    abhebesicherheit as _abhebesicherheit,
)

@dataclass
class Tor:
    name: str = "Tor"
    traversen: List[Traversenstrecke] = field(default_factory=list)
    bodenplatten: List[Bodenplatte] = field(default_factory=list)

    def __post_init__(self):
        # Voreinstellung: 3 Traversensegmente + 2 Bodenplatten
        if not self.traversen:
            self.traversen = [Traversenstrecke(name=f"TS{i+1}") for i in range(3)]
        if not self.bodenplatten:
            self.bodenplatten = [Bodenplatte(name=f"BP{i+1}") for i in range(2)]

    # öffentliche Methoden, die auf gemeinsame Rechenfunktionen delegieren
    def berechne_kippsicherheit(self) -> float:
        return _kippsicherheit(self)

    def berechne_gleitsicherheit(self) -> float:
        return _gleitsicherheit(self)

    def berechne_abhebesicherheit(self) -> float:
        return _abhebesicherheit(self)
