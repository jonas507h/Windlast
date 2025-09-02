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
    windkraft,
    windkraft_zu_vektor
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
        _reynoldszahl = reynoldszahl(_norm, self.objekttyp, self.traverse_name_intern, _staudruck, _zaehigkeit, _luftdichte)
        _projizierte_Flaeche = projizierte_flaeche(_norm, self.objekttyp, self.traverse_name_intern, [self.start, self.ende, self.orientierung], _windrichtung)
        _eingeschlossene_Flaeche = eingeschlossene_flaeche(_norm, self.objekttyp, self.traverse_name_intern, [self.start, self.ende])
        _voelligkeitsgrad = voelligkeitsgrad(_norm, _projizierte_Flaeche.wert, _eingeschlossene_Flaeche.wert,)
        _grundkraftbeiwert = grundkraftbeiwert(_norm, self.objekttyp, self.traverse_name_intern, [self.start, self.ende, self.orientierung], None, _windrichtung, _voelligkeitsgrad.wert, _reynoldszahl.wert)
        _schlankheit = schlankheit(_norm, self.objekttyp, self.traverse_name_intern, [self.start, self.ende])
        _abminderungsfaktor_schlankheit = abminderungsfaktor_schlankheit(_norm, self.objekttyp, _schlankheit.wert, _voelligkeitsgrad.wert)
        _kraftbeiwert = kraftbeiwert(_norm, self.objekttyp, _grundkraftbeiwert.wert, _abminderungsfaktor_schlankheit.wert)
        _windkraft = windkraft(_norm, self.objekttyp, _kraftbeiwert.wert, _staudruck, _projizierte_Flaeche.wert)
        _windkraft_vektor = windkraft_zu_vektor(_norm, self.objekttyp, None, _windkraft.wert, _windrichtung)

        return Kraefte(
            typ=Lasttyp.WIND,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=[_windkraft_vektor.wert],
            Angriffsflaeche_Einzelkraefte=[[self.start, self.ende]],
        )