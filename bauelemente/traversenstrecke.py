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
    windkraft_zu_vektor,
    segmentiere_strecke_nach_hoehenbereichen,
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
        _staudruecke = [450.0, 600.0]
        _obergrenzen = [5.0, 10.0]
        _zaehigkeit = 15.32e-6
        _luftdichte = 1.25
        _norm = Norm.DEFAULT
        _windrichtung: Vec3 = (0.0, 1.0, 0.0)  # Beispielwert für die Windrichtung


        # 1) Gesamt (einmalig)
        _schlankheit = schlankheit(
            _norm, self.objekttyp, self.traverse_name_intern, [self.start, self.ende]
        )

        # 2) Segmentierung nach Höhenbereichen
        segmente = segmentiere_strecke_nach_hoehenbereichen(
            self.start, self.ende, _staudruecke, _obergrenzen
        )
        if not segmente:
            raise ValueError("Traverse liegt in keinem Windbereich.")

        # 3) Pro Abschnitt rechnen
        einzelkraefte_vektoren: list[Vec3] = []
        angriffsbereiche: list[list[Vec3]] = []

        for seg in segmente:
            start_lokal = seg["start_lokal"]
            ende_lokal  = seg["ende_lokal"]
            staudruck   = seg["staudruck"]

            # Abschnittsweise Größen (abhängig von lokaler Geometrie / staudruck)
            _reynoldszahl = reynoldszahl(
                _norm, self.objekttyp, self.traverse_name_intern, staudruck, _zaehigkeit, _luftdichte
            )
            _projizierte_Flaeche = projizierte_flaeche(
                _norm, self.objekttyp, self.traverse_name_intern,
                [start_lokal, ende_lokal, self.orientierung], _windrichtung
            )
            _eingeschlossene_Flaeche = eingeschlossene_flaeche(
                _norm, self.objekttyp, self.traverse_name_intern, [start_lokal, ende_lokal]
            )
            _voelligkeitsgrad = voelligkeitsgrad(
                _norm, _projizierte_Flaeche.wert, _eingeschlossene_Flaeche.wert
            )
            _grundkraftbeiwert = grundkraftbeiwert(
                _norm, self.objekttyp, self.traverse_name_intern,
                [start_lokal, ende_lokal, self.orientierung],
                None,
                _windrichtung,
                _voelligkeitsgrad.wert,
                _reynoldszahl.wert,
            )
            _abminderungsfaktor_schlankheit = abminderungsfaktor_schlankheit(
                _norm, self.objekttyp, _schlankheit.wert, _voelligkeitsgrad.wert
            )
            _kraftbeiwert = kraftbeiwert(
                _norm, self.objekttyp, _grundkraftbeiwert.wert, _abminderungsfaktor_schlankheit.wert
            )
            _windkraft = windkraft(
                _norm, self.objekttyp, _kraftbeiwert.wert, staudruck, _projizierte_Flaeche.wert
            )
            _windkraft_vec = windkraft_zu_vektor(
                _norm, self.objekttyp, None, _windkraft.wert, _windrichtung
            )

            einzelkraefte_vektoren.append(_windkraft_vec.wert)
            angriffsbereiche.append([start_lokal, ende_lokal])

        return Kraefte(
            typ=Lasttyp.WIND,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=einzelkraefte_vektoren,
            Angriffsflaeche_Einzelkraefte=angriffsbereiche,
        )