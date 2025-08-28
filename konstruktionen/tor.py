from dataclasses import dataclass, field
from typing import List, Optional
from bauelemente import Bodenplatte, Traversenstrecke
from rechenfunktionen import (
    kippsicherheit as _kippsicherheit,
    gleitsicherheit as _gleitsicherheit,
    abhebesicherheit as _abhebesicherheit,
    gesamtgewicht as _gesamtgewicht,
)

@dataclass
class Tor:
    name: str = "Tor"
    breite_m: Optional[float] = None
    hoehe_m: Optional[float] = None

    # Kinder
    traversen: List[Traversenstrecke] = field(default_factory=list)
    bodenplatten: List[Bodenplatte] = field(default_factory=list)

    # Konfiguration: wie viele Bodenplatten und welche Auswahl
    bodenplatte_name_intern: Optional[str] = None
    anzahl_bodenplatten: int = 2
    traverse_name_intern: Optional[str] = None

    def __post_init__(self):
         # Default: (später gern 3 Traversen) – aktuell Gewicht kommt nur aus Bodenplatten
        if not self.traversen:
            self.traversen = []  # Platzhalter

        if not self.bodenplatten:
            # Wenn Auswahl vorhanden → entsprechend viele Instanzen
            if self.bodenplatte_name_intern:
                self.bodenplatten = [
                    Bodenplatte(name_intern=self.bodenplatte_name_intern)
                    for _ in range(self.anzahl_bodenplatten)
                ]
            # Falls keine Auswahl → leer lassen (führt zu 0 kg)

    # öffentliche Methoden, die auf gemeinsame Rechenfunktionen delegieren
    def berechne_kippsicherheit(self) -> float:
        return _kippsicherheit(self)

    def berechne_gleitsicherheit(self) -> float:
        return _gleitsicherheit(self)

    def berechne_abhebesicherheit(self) -> float:
        return _abhebesicherheit(self)
    
    def gesamtgewicht(self) -> float:
        return _gesamtgewicht(self)
