from dataclasses import dataclass, field
from typing import List, Optional, Sequence
from windlast_CORE.bauelemente import Bodenplatte, Traversenstrecke
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen import (
    gesamtgewicht as _gesamtgewicht,
)
from windlast_CORE.rechenfunktionen.kippsicherheit import kippsicherheit as _kippsicherheit
from windlast_CORE.rechenfunktionen.gleitsicherheit import gleitsicherheit as _gleitsicherheit
from windlast_CORE.rechenfunktionen.abhebesicherheit import abhebesicherheit as _abhebesicherheit
from windlast_CORE.datenstruktur.enums import Norm, MaterialTyp, FormTyp, RechenmethodeKippen, RechenmethodeGleiten, RechenmethodeAbheben, VereinfachungKonstruktion, TraversenOrientierung
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_kontext

# TODO: ID-Vergabe
@dataclass
class Tisch:
    name: str = "Tisch"
    breite: Optional[float] = None #[m]
    hoehe: Optional[float] = None #[m]
    tiefe: Optional[float] = None #[m]

    bauelemente: List[object] = field(default_factory=list)

    # Konfiguration
    bodenplatte_name_intern: Optional[str] = None
    anzahl_bodenplatten: int = 2
    traverse_name_intern: Optional[str] = None

    gummimatte_vorhanden: bool = True

    def __post_init__(self):
        B = float(self.breite)
        H = float(self.hoehe)
        T = float(self.tiefe)

        # Traversenstrecken aus Breite/Höhe + Profilhöhe t
        hat_traversen = any(isinstance(k, Traversenstrecke) for k in self.bauelemente)
        if (not hat_traversen) and self.breite and self.hoehe and self.tiefe and self.traverse_name_intern:

            if B <= 0 or H <= 0 or T <= 0:
                raise ValueError("Breite, Höhe und Tiefe müssen > 0 sein.")

            spec = catalog.get_traverse(self.traverse_name_intern)
            t = float(spec.hoehe)  # Traversenhöhe (Profilmaß)

            if H <= t or B <= 0:
                raise ValueError("Höhe muss größer als Traversenhöhe sein und Breite > 0.")

            front_left = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(t/2, t/2, 0.0),
                ende=(t/2, t/2, H),
                orientierung=(0.0, 1.0, 0.0),
                element_id_intern="Strecke_Vorne_Links",
                anzeigename=spec.anzeige_name,
            )
            front_right = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(B - t/2, t/2, 0.0),
                ende=(B - t/2, t/2, H),
                orientierung=(0.0, 1.0, 0.0),
                element_id_intern="Strecke_Vorne_Rechts",
                anzeigename=spec.anzeige_name,
            )
            back_left = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(t/2, T - t/2, 0.0),
                ende=(t/2, T - t/2, H),
                orientierung=(0.0, -1.0, 0.0),
                element_id_intern="Strecke_Hinten_Links",
                anzeigename=spec.anzeige_name,
            )
            back_right = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(B - t/2, T - t/2, 0.0),
                ende=(B - t/2, T - t/2, H),
                orientierung=(0.0, -1.0, 0.0),
                element_id_intern="Strecke_Hinten_Rechts",
                anzeigename=spec.anzeige_name,
            )
            top_front = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(0, t/2, H - t/2),
                ende=(B, t/2, H - t/2),
                orientierung=(0.0, 0.0, -1.0),
                element_id_intern="Strecke_Oben_Vorne",
                anzeigename=spec.anzeige_name,
            )
            top_back = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(0, T - t/2, H - t/2),
                ende=(B, T - t/2, H - t/2),
                orientierung=(0.0, 0.0, -1.0),
                element_id_intern="Strecke_Oben_Hinten",
                anzeigename=spec.anzeige_name,
            )
            top_left = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(t/2, 0.0, H - t/2),
                ende=(t/2, T, H - t/2),
                orientierung=(0.0, 0.0, -1.0),
                element_id_intern="Strecke_Oben_Links",
                anzeigename=spec.anzeige_name,
            )
            top_right = Traversenstrecke(
                traverse_name_intern=self.traverse_name_intern,
                start=(B - t/2, 0.0, H - t/2),
                ende=(B - t/2, T, H - t/2),
                orientierung=(0.0, 0.0, -1.0),
                element_id_intern="Strecke_Oben_Rechts",
                anzeigename=spec.anzeige_name,
            )
            self.bauelemente.extend([front_left, front_right, back_left, back_right,
                                     top_front, top_back, top_left, top_right])

        # Bodenplatten ggf. anlegen
        hat_bodenplatten = any(isinstance(k, Bodenplatte) for k in self.bauelemente)
        gummi = MaterialTyp.GUMMI if self.gummimatte_vorhanden else None
        if (not hat_bodenplatten) and self.bodenplatte_name_intern:
            front_left = Bodenplatte(
                name_intern=self.bodenplatte_name_intern,
                mittelpunkt=(t/2, t/2, 0.0),
                orientierung=(0.0, 0.0, 1.0),
                drehung=(0.0, 1.0, 0.0),
                form=FormTyp.RECHTECK,
                material=MaterialTyp.STAHL,
                untergrund=MaterialTyp.BETON,
                gummimatte=gummi,
                element_id_intern="Bodenplatte_Vorne_Links",
            )
            front_right = Bodenplatte(
                name_intern=self.bodenplatte_name_intern,
                mittelpunkt=(B - t/2, t/2, 0.0),
                orientierung=(0.0, 0.0, 1.0),
                drehung=(0.0, 1.0, 0.0),
                form=FormTyp.RECHTECK,
                material=MaterialTyp.STAHL,
                untergrund=MaterialTyp.BETON,
                gummimatte=gummi,
                element_id_intern="Bodenplatte_Vorne_Rechts",
            )
            back_left = Bodenplatte(
                name_intern=self.bodenplatte_name_intern,
                mittelpunkt=(t/2, T - t/2, 0.0),
                orientierung=(0.0, 0.0, 1.0),
                drehung=(0.0, -1.0, 0.0),
                form=FormTyp.RECHTECK,
                material=MaterialTyp.STAHL,
                untergrund=MaterialTyp.BETON,
                gummimatte=gummi,
                element_id_intern="Bodenplatte_Hinten_Links",
            )
            back_right = Bodenplatte(
                name_intern=self.bodenplatte_name_intern,
                mittelpunkt=(B - t/2, T - t/2, 0.0),
                orientierung=(0.0, 0.0, 1.0),
                drehung=(0.0, -1.0, 0.0),
                form=FormTyp.RECHTECK,
                material=MaterialTyp.STAHL,
                untergrund=MaterialTyp.BETON,
                gummimatte=gummi,
                element_id_intern="Bodenplatte_Hinten_Rechts",
            )
            self.bauelemente.extend([front_left, front_right, back_left, back_right])

    def gesamthoehe(
        self, *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
    ) -> float:
        """Maximale Gesamthöhe über alle Bauelemente mit .gesamthoehe()."""
        base_ctx = merge_kontext(kontext, {
            "funktion": "Tisch.Gesamthöhe",
        })
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

        # Fallback: falls Tisch selbst eine Höhe definiert hat
        if self.hoehe is not None:
            return float(self.hoehe)

        raise ValueError("Kein Bauelement mit gesamthoehe() gefunden und 'hoehe' am Tisch ist nicht gesetzt.")

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
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> List[Zwischenergebnis]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Tisch.BerechneKippsicherheit",
        })
        
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
            protokoll=protokoll,
            kontext=base_ctx,
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
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> List[Zwischenergebnis]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Tisch.BerechneGleitsicherheit",
        })
        
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
            protokoll=protokoll,
            kontext=base_ctx,
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
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> List[Zwischenergebnis]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Tisch.BerechneAbhebesicherheit",
        })

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
            protokoll=protokoll,
            kontext=base_ctx,
        )
    
    def gesamtgewicht(self) -> float:
        return _gesamtgewicht(self)
