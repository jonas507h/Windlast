from dataclasses import dataclass, field
from typing import List, Optional, Sequence
from bauelemente import Bodenplatte, Traversenstrecke
from materialdaten.catalog import catalog
from rechenfunktionen import (
    kippsicherheit as _kippsicherheit,
    gleitsicherheit as _gleitsicherheit,
    abhebesicherheit as _abhebesicherheit,
    gesamtgewicht as _gesamtgewicht,
)
from datenstruktur.enums import Norm, MaterialTyp, FormTyp, RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben, VereinfachungKonstruktion
from datenstruktur.zwischenergebnis import Zwischenergebnis 

# TODO: ID-Vergabe
@dataclass
class Tor:
    name: str = "Tor"
    breite: Optional[float] = None #[m]
    hoehe: Optional[float] = None #[m]

    bauelemente: List[object] = field(default_factory=list)

    # Konfiguration
    bodenplatte_name_intern: Optional[str] = None
    anzahl_bodenplatten: int = 2
    traverse_name_intern: Optional[str] = None

    def __post_init__(self):
        B = float(self.breite)
        H = float(self.hoehe)
        # Traversenstrecken aus Breite/Höhe + Profilhöhe t
        hat_traversen = any(isinstance(k, Traversenstrecke) for k in self.bauelemente)
        if (not hat_traversen) and self.breite and self.hoehe and self.traverse_name_intern:
            
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

    def gesamthoehe(self) -> float:
        """Maximale Gesamthöhe über alle Bauelemente mit .gesamthoehe()."""
        max_h = 0.0
        found = False

        for el in self.bauelemente:
            gh = getattr(el, "gesamthoehe", None)
            if callable(gh):
                try:
                    h = float(gh())
                except Exception:
                    # falls ein Element fehlschlägt, überspringen
                    continue
                if h > max_h:
                    max_h = h
                found = True

        if found:
            return max_h

        # Fallback: falls Tor selbst eine Höhe definiert hat
        if self.hoehe is not None:
            return float(self.hoehe)

        raise ValueError("Kein Bauelement mit gesamthoehe() gefunden und 'hoehe' am Tor ist nicht gesetzt.")

    def berechne_kippsicherheit(
        self,
        norm: Norm,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        *,
        konst=None,
        reset_berechnungen: bool = True,
        methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
        vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
        anzahl_windrichtungen: int = 4,
    ) -> Zwischenergebnis:
        return _kippsicherheit(
            self,
            norm,
            staudruecke,
            obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
        )

    def berechne_gleitsicherheit(
        self,
        norm: Norm,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        *,
        konst=None,
        reset_berechnungen: bool = False,
        methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
        vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
        anzahl_windrichtungen: int = 4,
    ) -> Zwischenergebnis:
        return _gleitsicherheit(
            self,
            norm,
            staudruecke,
            obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
        )

    def berechne_abhebesicherheit(
        self,
        norm: Norm,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        *,
        konst=None,
        reset_berechnungen: bool = False,
        methode: RechenmethodeAbheben = RechenmethodeAbheben.STANDARD,
        vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
        anzahl_windrichtungen: int = 4,
    ) -> Zwischenergebnis:
        return _abhebesicherheit(
            self,
            norm,
            staudruecke,
            obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
        )
    
    def gesamtgewicht(self) -> float:
        return _gesamtgewicht(self)
