from dataclasses import dataclass
from typing import Tuple, List, Sequence, Optional
import math
from windlast_CORE.datenstruktur.konstanten import PhysikKonstanten, aktuelle_konstanten
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen import (
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
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.enums import Lasttyp, Variabilitaet, ObjektTyp, Norm, Severity

@dataclass
class Rohr:
    rohr_name_intern: str
    start: Vec3
    ende:  Vec3
    objekttyp: ObjektTyp = ObjektTyp.ROHR
    element_id_intern: Optional[str] = None
    anzeigename: Optional[str] = None

    def gesamthoehe(self) -> float:
        return max(self.start[2], self.ende[2])

    def gewichtskraefte(self, *, protokoll: Optional[Protokoll] = None, breadcrumb: Optional[list] = None) -> List[Kraefte]:
        base_bc = breadcrumb if breadcrumb is not None else []
        base_meta = {
            "funktion": "Rohr.gewichtskraefte",
        }
        laenge = abstand_punkte(self.start, self.ende)

        specs = catalog.get_rohr(self.rohr_name_intern)
        di = specs.d_aussen - 2 * specs.t_wand
        querschnitt = math.pi * (specs.d_aussen**2 - di**2) / 4.0
        gewichtskraft_lin = querschnitt * specs.dichte * aktuelle_konstanten().erdbeschleunigung  # [N/m]

        Fz = -laenge * gewichtskraft_lin
        einzelkraefte_vektoren: list[Vec3] = [(0.0, 0.0, Fz)]

        angriffsbereiche: list[list[Vec3]] = [[self.start, self.ende]]

        schwerpunkt = flaechenschwerpunkt([self.start, self.ende])

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="gewichtskraft",
            wert= -1 * Fz,
            label="Gewichtskraft F_G",
            formelzeichen="F_G",
            formel="F_G = A · ρ · g · L",
            einheit="N",
            meta=base_meta,
        )

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
        *,
        protokoll: Optional[Protokoll] = None,
        breadcrumb: Optional[list] = None,
    ) -> List[Kraefte]:
        k = konst or aktuelle_konstanten()
        _zaehigkeit = k.zaehigkeit_kin
        _luftdichte = k.luftdichte

        base_bc = breadcrumb if breadcrumb is not None else []
        base_meta = {
            "funktion": "Rohr.windkraefte",
        }

        # 1) Gesamt (einmalig)
        _schlankheit = schlankheit(
            norm, self.objekttyp, self.rohr_name_intern, [self.start, self.ende],
            protokoll=protokoll, breadcrumb=base_bc,
        )

        # 2) Segmentierung nach Höhenbereichen
        segmente = segmentiere_strecke_nach_hoehenbereichen(
            self.start, self.ende, staudruecke, obergrenzen
        )
        if not segmente:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="ROHR/NO_WIND_SEGMENTS",
                text="Rohr liegt in keinem Windbereich.",
                breadcrumb=base_bc,
                meta=base_meta,
            )
            return []

        # 3) Pro Abschnitt rechnen
        einzelkraefte_vektoren: list[Vec3] = []
        angriffsbereiche: list[list[Vec3]] = []

        for i, seg in enumerate(segmente):
            start_lokal = seg["start_lokal"]
            ende_lokal  = seg["ende_lokal"]
            staudruck   = seg["staudruck"]

            seg_bc = merge_breadcrumb(base_bc, [bc_step("segment", i)])

            # Abschnittsweise Größen (abhängig von lokaler Geometrie / staudruck)
            _reynoldszahl = reynoldszahl(
                norm, self.objekttyp, self.rohr_name_intern, staudruck, _zaehigkeit, _luftdichte,
                protokoll=protokoll, breadcrumb=seg_bc,
            )
            _bezugsflaeche = projizierte_flaeche(
                norm, self.objekttyp, [start_lokal, ende_lokal],
                self.rohr_name_intern, windrichtung,
                protokoll=protokoll, breadcrumb=seg_bc,
            )
            # _eingeschlossene_Flaeche = eingeschlossene_flaeche(
            #     norm, self.objekttyp, self.rohr_name_intern, [start_lokal, ende_lokal],
            #     protokoll=protokoll, breadcrumb=seg_bc,
            # )
            # _voelligkeitsgrad = voelligkeitsgrad(
            #     norm, _bezugsflaeche.wert, _eingeschlossene_Flaeche.wert,
            #     protokoll=protokoll, breadcrumb=seg_bc,
            # )
            _grundkraftbeiwert = grundkraftbeiwert(
                norm,
                self.objekttyp,
                reynoldszahl=_reynoldszahl.wert,
                windrichtung=windrichtung,
                punkte=[start_lokal, ende_lokal],
                protokoll=protokoll, breadcrumb=seg_bc,
            )
            _abminderungsfaktor_schlankheit = abminderungsfaktor_schlankheit(
                norm, self.objekttyp, _schlankheit.wert,
                protokoll=protokoll, breadcrumb=seg_bc,
            )
            _kraftbeiwert = kraftbeiwert(
                norm, self.objekttyp, _grundkraftbeiwert.wert, _abminderungsfaktor_schlankheit.wert,
                protokoll=protokoll, breadcrumb=seg_bc,
            )
            _windkraft = windkraft(
                norm, self.objekttyp, _kraftbeiwert.wert, staudruck, _bezugsflaeche.wert,
                protokoll=protokoll, breadcrumb=seg_bc,
            )
            _windkraft_vec = windkraft_zu_vektor(
                norm, self.objekttyp, [start_lokal, ende_lokal], _windkraft.wert, windrichtung,
                protokoll=protokoll, breadcrumb=seg_bc,
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