from dataclasses import dataclass
from typing import Tuple, List, Sequence, Optional
from datenstruktur.konstanten import PhysikKonstanten, aktuelle_konstanten
from materialdaten.catalog import catalog
from rechenfunktionen import (
    Vec3,
    flaechenschwerpunkt,
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
class Rohr:
    rohr_name_intern: str
    start: Vec3
    ende:  Vec3
    objekttyp: ObjektTyp = ObjektTyp.ROHR
    element_id_intern: Optional[str] = None

    def gesamthoehe(self) -> float:
        return max(self.start[2], self.ende[2])

    def gewichtskraefte(self) -> List[Kraefte]:
        laenge = abstand_punkte(self.start, self.ende)

        specs = catalog.get_rohr(self.rohr_name_intern)
        gewichtskraft_lin = float(specs.gewicht_linear) * aktuelle_konstanten().erdbeschleunigung  # [N/m]

        Fz = -laenge * gewichtskraft_lin
        einzelkraefte_vektoren: list[Vec3] = [(0.0, 0.0, Fz)]

        angriffsbereiche: list[list[Vec3]] = [[self.start, self.ende]]

        schwerpunkt = flaechenschwerpunkt([self.start, self.ende])

        return [Kraefte(
            element_id_intern=self.element_id_intern,
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=einzelkraefte_vektoren,
            Angriffsflaeche_Einzelkraefte=angriffsbereiche,
            Schwerpunkt=schwerpunkt,
        )]

    def windkraefte(
        self,
        norm: Norm,
        windrichtung: Vec3,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        konst: PhysikKonstanten | None = None,   # optional: Defaults oder Override-Set
    ) -> List[Kraefte]:
        k = konst or aktuelle_konstanten()
        _zaehigkeit = k.zaehigkeit_kin
        _luftdichte = k.luftdichte

        # 1) Gesamt (einmalig)
        _schlankheit = schlankheit(
            norm, self.objekttyp, self.rohr_name_intern, [self.start, self.ende]
        )

        # 2) Segmentierung nach Höhenbereichen
        segmente = segmentiere_strecke_nach_hoehenbereichen(
            self.start, self.ende, staudruecke, obergrenzen
        )
        if not segmente:
            raise ValueError("Rohr liegt in keinem Windbereich.")

        # 3) Pro Abschnitt rechnen
        einzelkraefte_vektoren: list[Vec3] = []
        angriffsbereiche: list[list[Vec3]] = []

        for seg in segmente:
            start_lokal = seg["start_lokal"]
            ende_lokal  = seg["ende_lokal"]
            staudruck   = seg["staudruck"]

            # Abschnittsweise Größen (abhängig von lokaler Geometrie / staudruck)
            _reynoldszahl = reynoldszahl(
                norm, self.objekttyp, self.rohr_name_intern, staudruck, _zaehigkeit, _luftdichte
            )
            _projizierte_Flaeche = projizierte_flaeche(
                norm, self.objekttyp, self.rohr_name_intern,
                [start_lokal, ende_lokal], windrichtung
            )
            _eingeschlossene_Flaeche = eingeschlossene_flaeche(
                norm, self.objekttyp, self.rohr_name_intern, [start_lokal, ende_lokal]
            )
            _voelligkeitsgrad = voelligkeitsgrad(
                norm, _projizierte_Flaeche.wert, _eingeschlossene_Flaeche.wert
            )
            _grundkraftbeiwert = grundkraftbeiwert(
                norm, self.objekttyp, self.rohr_name_intern,
                [start_lokal, ende_lokal],
                None,
                windrichtung,
                _voelligkeitsgrad.wert,
                _reynoldszahl.wert,
            )
            _abminderungsfaktor_schlankheit = abminderungsfaktor_schlankheit(
                norm, self.objekttyp, _schlankheit.wert, _voelligkeitsgrad.wert
            )
            _kraftbeiwert = kraftbeiwert(
                norm, self.objekttyp, _grundkraftbeiwert.wert, _abminderungsfaktor_schlankheit.wert
            )
            _windkraft = windkraft(
                norm, self.objekttyp, _kraftbeiwert.wert, staudruck, _projizierte_Flaeche.wert
            )
            _windkraft_vec = windkraft_zu_vektor(
                norm, self.objekttyp, None, _windkraft.wert, windrichtung
            )

            einzelkraefte_vektoren.append(_windkraft_vec.wert)
            angriffsbereiche.append([start_lokal, ende_lokal])

        return [Kraefte(
            element_id_intern=self.element_id_intern,
            typ=Lasttyp.WIND,
            variabilitaet=Variabilitaet.VERAENDERLICH,
            Einzelkraefte=einzelkraefte_vektoren,
            Angriffsflaeche_Einzelkraefte=angriffsbereiche,
        )]