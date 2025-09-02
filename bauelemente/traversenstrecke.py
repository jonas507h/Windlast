from dataclasses import dataclass
from typing import Tuple
from materialdaten.catalog import catalog
from rechenfunktionen import (
    Vec3,
    abstand_punkte,
    reynoldszahl,
    projizierte_flaeche,
    eingeschlossene_flaeche,
    voelligkeitsgrad,
    grundkraftbeiwert,
    schlankheit,
    abminderungsfaktor_schlankheit,
    kraftbeiwert,
)
from datenstruktur.kraefte import Kraefte
from datenstruktur.enums import Lasttyp, Variabilitaet, ObjektTyp, Norm

@dataclass
class Traversenstrecke:
    traverse_name_intern: str
    start: Vec3
    ende:  Vec3
    orientierung: Vec3
    objekttyp: ObjektTyp = ObjektTyp.TRAVERSE

    def laenge(self) -> float:
        return abstand_punkte(self.start, self.ende)

    def gewicht(self) -> float:
        spec = catalog.get_traverse(self.traverse_name_intern)
        return self.laenge() * float(spec.gewicht_linear)

    def windkraft(self) -> Kraefte:
        # Grundgerüst, noch ohne Berechnung
        _staudruck = 350
        _zaehigkeit = 15.32e-6
        _luftdichte = 1.25
        _norm = Norm.DEFAULT
        _windrichtung: Vec3 = (0.0, 1.0, 0.0)  # Beispielwert für die Windrichtung
        _reynoldszahl = reynoldszahl(self.objekttyp, self.traverse_name_intern, _staudruck, _zaehigkeit, _luftdichte, _norm)
        _projizierte_Flaeche = projizierte_flaeche(self.objekttyp, self.traverse_name_intern, [self.start, self.ende, self.orientierung], _windrichtung, _norm)
        _eingeschlossene_Flaeche = eingeschlossene_flaeche(self.objekttyp, self.traverse_name_intern, [self.start, self.ende], _norm)
        _voelligkeitsgrad = voelligkeitsgrad(_projizierte_Flaeche.wert, _eingeschlossene_Flaeche.wert, _norm)
        _grundkraftbeiwert = grundkraftbeiwert(self.objekttyp, self.traverse_name_intern, [self.start, self.ende, self.orientierung], None, _windrichtung, _voelligkeitsgrad.wert, _reynoldszahl.wert, _norm)
        _schlankheit = schlankheit(self.objekttyp, self.traverse_name_intern, [self.start, self.ende], _norm)
        _abminderungsfaktor_schlankheit = abminderungsfaktor_schlankheit(self.objekttyp, _schlankheit.wert, _voelligkeitsgrad.wert, _norm)
        _kraftbeiwert = kraftbeiwert(self.objekttyp, _grundkraftbeiwert.wert, _abminderungsfaktor_schlankheit.wert, _norm)

        _windkraft = _kraftbeiwert.wert * _staudruck * _projizierte_Flaeche.wert #braucht noch eine Richtung

        return Kraefte(
            typ=Lasttyp.WIND,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=[(_windkraft, 0.0, 0.0)],
            Angriffsflaeche_Einzelkraefte=[[self.start, self.ende]],
        )