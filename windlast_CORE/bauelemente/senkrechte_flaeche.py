from dataclasses import dataclass
from typing import Tuple, List, Sequence, Optional
import math
from windlast_CORE.datenstruktur.konstanten import PhysikKonstanten, aktuelle_konstanten
from windlast_CORE.datenstruktur.zwischenergebnis import Protokoll, make_docbundle, merge_kontext, protokolliere_msg, protokolliere_doc
from windlast_CORE.rechenfunktionen import (
    Vec3,
    flaechenschwerpunkt,
    projizierte_flaeche,
    kraftbeiwert,
    windkraft,
    windkraft_zu_vektor,
    flaecheninhalt_polygon,
    vektor_zwischen_punkten,
    vektor_laenge,
    vektor_normieren,
    vektor_invertieren,
    vektoren_addieren,
    vektor_multiplizieren,
    is_senkrecht,
    is_parallel,
    is_ebene,
    normale_zu_ebene,
    projektion_vektor_auf_ebene,
    vektor_winkel,
    segmentiere_strecke_nach_hoehenbereichen,
)
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.enums import Lasttyp, Variabilitaet, ObjektTyp, Norm, Severity, senkrechteFlaecheTyp, Zone
from windlast_CORE.datenstruktur.konstanten import _EPS

# Helper
def zonen_einteilung_horizontal(
        endpunkte: List[Vec3],
        einheitsvektor: Vec3,
        breite: float,
        hoehe: float
    ) -> List[Vec3]:
    trennpunkte: List[Vec3] = [endpunkte[0]]
    if breite > 0.3 * hoehe:
        endpunkt_zone = vektoren_addieren([endpunkte[0], vektor_multiplizieren(einheitsvektor, 0.3 * hoehe)])
        trennpunkte.append(endpunkt_zone)
    if breite > 2 * hoehe:
        endpunkt_zone = vektoren_addieren([endpunkte[0], vektor_multiplizieren(einheitsvektor, 2.0 * hoehe)])
        trennpunkte.append(endpunkt_zone)
    if breite > 4 * hoehe:
        endpunkt_zone = vektoren_addieren([endpunkte[0], vektor_multiplizieren(einheitsvektor, 4.0 * hoehe)])
        trennpunkte.append(endpunkt_zone)
    trennpunkte.append(endpunkte[1])
    return trennpunkte

@dataclass
class senkrechteFlaeche:
    eckpunkte: List[Vec3]
    objekttyp: ObjektTyp = ObjektTyp.SENKRECHTE_FLAECHE
    flaeche_typ: Optional[senkrechteFlaecheTyp] = None
    element_id_intern: Optional[str] = None
    anzeigename: Optional[str] = None
    flaechenlast: Optional[float] = None  # [kg/m²]
    gesamtgewicht: Optional[float] = 0  # [kg]

    
    def __post_init__(self) -> None:
        self._validate_eckpunkte()

    def _validate_eckpunkte(self) -> None:
        """
        Prüft:
        - genau 4 Punkte
        - Punkte liegen in einer Ebene
        - Fläche ist senkrecht (Normale ~ z-Achse ⟂ Bodenebene)
        - Fläche ist rechtwinklig (Diagonalen gleich lang)

        Bei Verstoß: ValueError (oder eigene Domain-Exception) werfen.
        """
        if len(self.eckpunkte) != 4:
            raise ValueError("Für SENKRECHTE_FLAECHE werden genau 4 Eckpunkte erwartet.")
        if not is_ebene(self.eckpunkte):
            raise ValueError("Die Eckpunkte der SENKRECHTE_FLAECHE müssen in einer Ebene liegen.")
        z_Achse = (0.0, 0.0, 1.0)
        if not is_parallel('vecs/ebene', vecs=[z_Achse], punkte=self.eckpunkte):
            raise ValueError("Die SENKRECHTE_FLAECHE muss senkrecht zur Bodenebene stehen.")
        d1 = vektor_zwischen_punkten(self.eckpunkte[0], self.eckpunkte[2])
        d2 = vektor_zwischen_punkten(self.eckpunkte[1], self.eckpunkte[3])
        if abs(vektor_laenge(d1) - vektor_laenge(d2)) > _EPS:
            raise ValueError("Die SENKRECHTE_FLAECHE muss rechteckig sein (Diagonalen ungleich lang).")
        

    def gesamthoehe(self) -> float:
        return max(p[2] for p in self.eckpunkte)
  
    def gewichtskraefte(self, *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None) -> List[Kraefte]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "gewichtskraefte",
            "element_id": self.element_id_intern,
            "objekttyp": self.objekttyp.name,
            "flaechenlast": self.flaechenlast,
            "gesamtgewicht": self.gesamtgewicht,
        })
        if self.gesamtgewicht is not None:
            Fz = -self.gesamtgewicht * aktuelle_konstanten().erdbeschleunigung  # [N]
        elif self.flaechenlast is not None:
            flaeche = flaecheninhalt_polygon(self.eckpunkte)  # [m²]
            Fz = -flaeche * self.flaechenlast * aktuelle_konstanten().erdbeschleunigung  # [N]
        else:
            # protokolliere_msg(
            #     protokoll, severity=Severity.WARN, code="SENKRECHTE_FLAECHE/NO_WEIGHT",
            #     text="Weder Gesamtgewicht noch Flächenlast der Fläche angegeben. Es werden keine Gewichtskräfte berechnet.",
            #     kontext=base_ctx,
            # )
            Fz = 0.0

        einzelkraefte_vektoren: list[Vec3] = [(0.0, 0.0, Fz)]

        angriffsbereiche: list[list[Vec3]] = [self.eckpunkte]

        schwerpunkt = flaechenschwerpunkt(self.eckpunkte)

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
        kontext: Optional[dict] = None,
    ) -> List[Kraefte]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "windkraefte",
            "norm": norm.value,
            "element_id": self.element_id_intern,
            "objekttyp": self.objekttyp.value,
            "windrichtung": windrichtung,
        })

        # Unterscheidung Wand / Anzeigetafel
        oberkante = max(p[2] for p in self.eckpunkte)
        unterkante = min(p[2] for p in self.eckpunkte)
        hoehe = oberkante - unterkante
        vektor_hoehe = (0.0, 0.0, hoehe)

        endpunkte_unterkante = [p for p in self.eckpunkte if abs(p[2] - unterkante) <= _EPS]
        if len(endpunkte_unterkante) != 2:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="WINDKRAEFTE/WAND_UNTERKANTE_UNGUELTIG",
                text=f"Erwartet 2 Eckpunkte auf der Unterkante (z={unterkante}), gefunden: {len(endpunkte_unterkante)}.",
                kontext=base_ctx,
            )
            return []
        wand_dir = vektor_zwischen_punkten(endpunkte_unterkante[0], endpunkte_unterkante[1])

        breite = vektor_laenge(wand_dir)

        if unterkante >= hoehe / 4:
            self.flaeche_typ = senkrechteFlaecheTyp.ANZEIGETAFEL
        elif unterkante < hoehe / 4 and breite / hoehe <= 1.0:
            self.flaeche_typ = senkrechteFlaecheTyp.ANZEIGETAFEL
        else:
            self.flaeche_typ = senkrechteFlaecheTyp.WAND

        # Berechnung der Windkräfte
        if self.flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            # Staudruck auf mittlerer Höhe der Anzeigetafel
            mitte_hoehe = (oberkante + unterkante) / 2
            tafel_ctx = merge_kontext(base_ctx, {
                "mittlere_hoehe": mitte_hoehe,
                "flaeche_typ": self.flaeche_typ.value,
            })
            staudruck = 0.0
            for i, grenze in enumerate(obergrenzen):
                if mitte_hoehe <= grenze:
                    staudruck = staudruecke[i]
                    break
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(
                    titel="Staudruck q",
                    wert=staudruck,
                    einheit="N/m²",
                    formel="Staudruck auf mittlerer Höhe der Anzeigetafel",
                    quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 7.4.3",
                    ),
                kontext=tafel_ctx,
            )

            _kraftbeiwert = kraftbeiwert(
                norm, objekttyp=self.objekttyp, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ, punkte=self.eckpunkte,
                protokoll=protokoll, kontext=tafel_ctx
            )
            _bezugsflaeche = projizierte_flaeche(
                norm, objekttyp=self.objekttyp, punkte=self.eckpunkte,
                protokoll=protokoll, kontext=tafel_ctx
            )
            _windkraft = windkraft(
                norm, objekttyp=self.objekttyp, kraftbeiwert=_kraftbeiwert.wert, staudruck=staudruck, projizierte_flaeche=_bezugsflaeche.wert,senkrechte_flaeche_typ=self.flaeche_typ,
                protokoll=protokoll, kontext=tafel_ctx
            )
            _windkraft_vec = windkraft_zu_vektor(
                norm, objekttyp=self.objekttyp, punkte=self.eckpunkte, windkraft=_windkraft.wert, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ,
                protokoll=protokoll, kontext=tafel_ctx
            )
            einzelkraefte_vektoren = [_windkraft_vec.wert]
            angriffsbereiche = [self.eckpunkte]

            return [Kraefte(
                element_id_intern=self.element_id_intern,
                typ=Lasttyp.WIND,
                variabilitaet=Variabilitaet.VERAENDERLICH,
                Einzelkraefte=einzelkraefte_vektoren,
                Angriffsflaeche_Einzelkraefte=angriffsbereiche,
            )]
        elif self.flaeche_typ == senkrechteFlaecheTyp.WAND:
            # Winkel zwischen Wand und Windrichtung in der Horizontalen    
            wand_dir_xy = projektion_vektor_auf_ebene(wand_dir, (0.0, 0.0, 1.0))
            wind_xy     = projektion_vektor_auf_ebene(windrichtung, (0.0, 0.0, 1.0))
            
            if vektor_laenge(wand_dir_xy) < _EPS or vektor_laenge(wind_xy) < _EPS:
                protokolliere_msg(
                    protokoll,
                    severity=Severity.INFO,
                    code="WINDKRAEFTE/WAND_KEINE_HORIZ_KOMPONENTE",
                    text="Wandrichtung oder Windrichtung hat keine horizontale Komponente – keine Windlast auf freistehende Wand angesetzt.",
                    kontext=base_ctx,
                )
                return []

            # Winkel 0°…180° zwischen horizontaler Wandrichtung und horizontaler Windrichtung
            winkel = vektor_winkel(wand_dir_xy, wind_xy)

            wand_ctx = merge_kontext(base_ctx, {
                "wand_breite": f"{breite}m",
                "wand_hoehe": f"{hoehe}m",
                "winkel_wand_wind": f"{winkel:.2f}°",
                "flaeche_typ": self.flaeche_typ.value,
            })

            # Fall 1: Wind praktisch parallel
            if winkel < 5.0 or winkel > 175.0:
                protokolliere_msg(
                    protokoll,
                    severity=Severity.HINT,
                    code="WINDKRAEFTE/WAND_PARALLEL",
                    text=f"Winkel zwischen Wand und Windrichtung = {winkel:.2f}° -> Wind nahezu parallel, keine Windkraft angesetzt.",
                    kontext=wand_ctx,
                )
                return []

            kraefte_faelle: List[Kraefte] = []

            # Fall 2: 5° <= winkel <= 90° -> Anströmung von Seite A
            if 5.0 <= winkel <= 90.0+_EPS:
                einzelkraefte_vektoren: list[Vec3] = []
                angriffsbereiche: list[list[Vec3]] = []

                einheitsvektor_unterkante = vektor_normieren(wand_dir_xy)
                startpunkt_unterkante = endpunkte_unterkante[0]
                endpunkt_unterkante = endpunkte_unterkante[1]

                trennpunkte_unterkante = zonen_einteilung_horizontal(
                    endpunkte=[startpunkt_unterkante, endpunkt_unterkante],
                    einheitsvektor=einheitsvektor_unterkante,
                    breite=breite,
                    hoehe=hoehe
                )
                zonen = [Zone.A, Zone.B, Zone.C, Zone.D]

                if 90.0-_EPS < winkel <= 90.0+_EPS:
                    lastfall_ctx = merge_kontext(wand_ctx, {
                        "lastfall_index": 0,
                    })
                else:
                    lastfall_ctx = wand_ctx

                # Iteration über horizontale Zonen
                for i in range(len(trennpunkte_unterkante)-1):
                    unten_start = trennpunkte_unterkante[i]
                    unten_ende  = trennpunkte_unterkante[i+1]
                    oben_start = vektoren_addieren([unten_start, vektor_hoehe])
                    teilvektor_unterkante = vektor_zwischen_punkten(unten_start, unten_ende)
                    zone = zonen[i]

                    zonen_ctx = merge_kontext(lastfall_ctx, {
                        "zone": zone.value,
                    })

                    # Segmentierung nach Höhenbereichen
                    segmente = segmentiere_strecke_nach_hoehenbereichen(
                        unten_start, oben_start, staudruecke, obergrenzen
                    )
                    if not segmente:
                        protokolliere_msg(
                            protokoll, severity=Severity.ERROR, code="WAND/NO_WIND_SEGMENTS",
                            text="Wand liegt in keinem Windbereich.",
                            kontext=zonen_ctx,
                        )
                        return []
                    
                    # Iteration über vertikale Zonen
                    for j, seg in enumerate(segmente):
                        unten_start_lokal = seg["start_lokal"]
                        unten_ende_lokal = vektoren_addieren([unten_start_lokal, teilvektor_unterkante])
                        oben_start_lokal  = seg["ende_lokal"]
                        oben_ende_lokal   = vektoren_addieren([oben_start_lokal, teilvektor_unterkante])
                        eckpunkte_lokal = [ unten_start_lokal, unten_ende_lokal, oben_ende_lokal, oben_start_lokal ]
                        staudruck   = seg["staudruck"]

                        seg_ctx = merge_kontext(zonen_ctx, {
                            "segment_index": j,
                        })

                        _kraftbeiwert = kraftbeiwert(
                            norm, objekttyp=self.objekttyp, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ, zone=zone,
                            punkte=self.eckpunkte,
                            protokoll=protokoll, kontext=seg_ctx
                        )
                        _bezugsflaeche = projizierte_flaeche(
                            norm, objekttyp=self.objekttyp, punkte=eckpunkte_lokal,
                            protokoll=protokoll, kontext=seg_ctx
                        )
                        _windkraft = windkraft(
                            norm, objekttyp=self.objekttyp, kraftbeiwert=_kraftbeiwert.wert, staudruck=staudruck, projizierte_flaeche=_bezugsflaeche.wert, senkrechte_flaeche_typ=self.flaeche_typ,
                            protokoll=protokoll, kontext=seg_ctx
                        )
                        _windkraft_vec = windkraft_zu_vektor(
                            norm, objekttyp=self.objekttyp, punkte=eckpunkte_lokal, windkraft=_windkraft.wert, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ,
                            protokoll=protokoll, kontext=seg_ctx
                        )

                        einzelkraefte_vektoren.append(_windkraft_vec.wert)
                        angriffsbereiche.append([
                            unten_start_lokal,
                            unten_ende_lokal,
                            oben_ende_lokal,
                            oben_start_lokal
                        ])

                kraefte_faelle.append(
                    Kraefte(
                        element_id_intern=self.element_id_intern,
                        typ=Lasttyp.WIND,
                        variabilitaet=Variabilitaet.VERAENDERLICH,
                        Einzelkraefte=einzelkraefte_vektoren,
                        Angriffsflaeche_Einzelkraefte=angriffsbereiche,
                    )
                )

            # Fall 3: 90° <= winkel < 175° -> Anströmung von Seite B
            if 90.0-_EPS <= winkel < 175.0:
                einzelkraefte_vektoren: list[Vec3] = []
                angriffsbereiche: list[list[Vec3]] = []

                einheitsvektor_unterkante = vektor_invertieren(vektor_normieren(wand_dir_xy))
                startpunkt_unterkante = endpunkte_unterkante[1]
                endpunkt_unterkante = endpunkte_unterkante[0]

                trennpunkte_unterkante = zonen_einteilung_horizontal(
                    endpunkte=[startpunkt_unterkante, endpunkt_unterkante],
                    einheitsvektor=einheitsvektor_unterkante,
                    breite=breite,
                    hoehe=hoehe
                )
                zonen = [Zone.A, Zone.B, Zone.C, Zone.D]

                if 90.0-_EPS < winkel <= 90.0+_EPS:
                    lastfall_ctx = merge_kontext(wand_ctx, {
                        "lastfall_index": 1,
                    })
                else:
                    lastfall_ctx = wand_ctx

                # Iteration über horizontale Zonen
                for i in range(len(trennpunkte_unterkante)-1):
                    unten_start = trennpunkte_unterkante[i]
                    unten_ende  = trennpunkte_unterkante[i+1]
                    oben_start = vektoren_addieren([unten_start, vektor_hoehe])
                    teilvektor_unterkante = vektor_zwischen_punkten(unten_start, unten_ende)
                    zone = zonen[i]

                    zonen_ctx = merge_kontext(lastfall_ctx, {
                        "zone": zone.value,
                    })

                    # Segmentierung nach Höhenbereichen
                    segmente = segmentiere_strecke_nach_hoehenbereichen(
                        unten_start, oben_start, staudruecke, obergrenzen
                    )
                    if not segmente:
                        protokolliere_msg(
                            protokoll, severity=Severity.ERROR, code="WAND/NO_WIND_SEGMENTS",
                            text="Wand liegt in keinem Windbereich.",
                            kontext=base_ctx,
                        )
                        return []
                    
                    # Iteration über vertikale Zonen
                    for j, seg in enumerate(segmente):
                        unten_start_lokal = seg["start_lokal"]
                        unten_ende_lokal = vektoren_addieren([unten_start_lokal, teilvektor_unterkante])
                        oben_start_lokal  = seg["ende_lokal"]
                        oben_ende_lokal   = vektoren_addieren([oben_start_lokal, teilvektor_unterkante])
                        eckpunkte_lokal = [ unten_start_lokal, unten_ende_lokal, oben_ende_lokal, oben_start_lokal ]
                        staudruck   = seg["staudruck"]

                        seg_ctx = merge_kontext(zonen_ctx, {
                            "segment_index": j,
                        })

                        _kraftbeiwert = kraftbeiwert(
                            norm, objekttyp=self.objekttyp, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ, zone=zone,
                            punkte=self.eckpunkte,
                            protokoll=protokoll, kontext=seg_ctx
                        )
                        _bezugsflaeche = projizierte_flaeche(
                            norm, objekttyp=self.objekttyp, punkte=eckpunkte_lokal,
                            protokoll=protokoll, kontext=seg_ctx
                        )
                        _windkraft = windkraft(
                            norm, objekttyp=self.objekttyp, kraftbeiwert=_kraftbeiwert.wert, staudruck=staudruck, projizierte_flaeche=_bezugsflaeche.wert, senkrechte_flaeche_typ=self.flaeche_typ,
                            protokoll=protokoll, kontext=seg_ctx
                        )
                        _windkraft_vec = windkraft_zu_vektor(
                            norm, objekttyp=self.objekttyp, punkte=eckpunkte_lokal, windkraft=_windkraft.wert, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ,
                            protokoll=protokoll, kontext=seg_ctx
                        )

                        einzelkraefte_vektoren.append(_windkraft_vec.wert)
                        angriffsbereiche.append([
                            unten_start_lokal,
                            unten_ende_lokal,
                            oben_ende_lokal,
                            oben_start_lokal
                        ])

                kraefte_faelle.append(
                    Kraefte(
                        element_id_intern=self.element_id_intern,
                        typ=Lasttyp.WIND,
                        variabilitaet=Variabilitaet.VERAENDERLICH,
                        Einzelkraefte=einzelkraefte_vektoren,
                        Angriffsflaeche_Einzelkraefte=angriffsbereiche,
                    )
                )
            return kraefte_faelle

        else:
            protokolliere_msg(
                    protokoll,
                    severity=Severity.ERROR,
                    code="WINDKRAEFTE/NOT_IMPLEMENTED",
                    text=f"Windkraefte für Flächetyp {self.flaeche_typ.value} sind noch nicht implementiert.",
                    kontext=base_ctx,
            )
            return []