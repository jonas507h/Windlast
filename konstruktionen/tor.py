from dataclasses import dataclass, field
from typing import List, Optional
from bauelemente import Bodenplatte, Traversenstrecke
from materialdaten.catalog import catalog
from rechenfunktionen import (
    kippsicherheit as _kippsicherheit,
    gleitsicherheit as _gleitsicherheit,
    abhebesicherheit as _abhebesicherheit,
    gesamtgewicht as _gesamtgewicht,
)
from datenstruktur.enums import Norm, ObjektTyp, MaterialTyp, FormTyp, Lasttyp, Variabilitaet

# TODO: ID-Vergabe
@dataclass
class Tor:
    name: str = "Tor"
    breite_m: Optional[float] = None
    hoehe_m: Optional[float] = None

    # NEU: alle Kinder an einer Stelle
    bauelemente: List[object] = field(default_factory=list)

    # Konfiguration
    bodenplatte_name_intern: Optional[str] = None
    anzahl_bodenplatten: int = 2
    traverse_name_intern: Optional[str] = None

    def __post_init__(self):
        B = float(self.breite_m)
        H = float(self.hoehe_m)
        # Traversenstrecken aus Breite/Höhe + Profilhöhe t
        hat_traversen = any(isinstance(k, Traversenstrecke) for k in self.bauelemente)
        if (not hat_traversen) and self.breite_m and self.hoehe_m and self.traverse_name_intern:
            
            if B <= 0 or H <= 0:
                raise ValueError("Breite und Höhe müssen > 0 sein.")

            spec = catalog.get_traverse(self.traverse_name_intern)
            t = float(spec.hoehe)  # Traversenhöhe (Profilmaß)

            if H <= t or B <= 0:
                raise ValueError("Höhe muss größer als Traversenhöhe sein und Breite > 0.")

            left = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(t/2, 0.0, 0.0),
                ende=(t/2, 0.0, H),
                orientierung=(0.0, 1.0, 0.0),
                element_id_intern="Strecke_Links",
            )
            top = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(0.0, 0.0, H - t/2),
                ende=(B,   0.0, H - t/2),
                orientierung=(0.0, 1.0, 0.0),
                element_id_intern="Strecke_Oben",
            )
            right = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(B - t/2, 0.0, 0.0),
                ende=(B - t/2, 0.0, H),
                orientierung=(0.0, 1.0, 0.0),
                element_id_intern="Strecke_Rechts",
            )
            self.bauelemente.extend([left, top, right])

        # Bodenplatten ggf. anlegen
        hat_bodenplatten = any(isinstance(k, Bodenplatte) for k in self.bauelemente)
        if (not hat_bodenplatten) and self.bodenplatte_name_intern:
            left = Bodenplatte(
                name_intern=self.bodenplatte_name_intern,
                mittelpunkt=(0.0, 0.0, 0.0),
                orientierung=(0.0, 0.0, 1.0),
                drehung=(0.0, 1.0, 0.0),
                form=FormTyp.RECHTECK,
                material=MaterialTyp.STAHL,
                untergrund=MaterialTyp.BETON,
                gummimatte=MaterialTyp.GUMMI,
                element_id_intern="Bodenplatte_Links",
            )
            right = Bodenplatte(
                name_intern=self.bodenplatte_name_intern,
                mittelpunkt=(B, 0.0, 0.0),
                orientierung=(0.0, 0.0, 1.0),
                drehung=(0.0, 1.0, 0.0),
                form=FormTyp.RECHTECK,
                material=MaterialTyp.STAHL,
                untergrund=MaterialTyp.BETON,
                gummimatte=MaterialTyp.GUMMI,
                element_id_intern="Bodenplatte_Rechts",
            )
            self.bauelemente.extend([left, right])

    # öffentliche Methoden, die auf gemeinsame Rechenfunktionen delegieren
    def berechne_kippsicherheit(self) -> float:
        return _kippsicherheit(self)

    def berechne_gleitsicherheit(self) -> float:
        return _gleitsicherheit(self)

    def berechne_abhebesicherheit(self) -> float:
        return _abhebesicherheit(self)
    
    def gesamtgewicht(self) -> float:
        return _gesamtgewicht(self)
