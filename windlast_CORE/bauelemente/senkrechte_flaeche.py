from dataclasses import dataclass
from typing import Tuple, List, Sequence, Optional
import math
from windlast_CORE.datenstruktur.konstanten import PhysikKonstanten, aktuelle_konstanten
from windlast_CORE.datenstruktur.zwischenergebnis import Protokoll, merge_kontext, protokolliere_msg
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
    is_senkrecht,
    is_parallel,
    is_ebene,
    normale_zu_ebene,
)
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.enums import Lasttyp, Variabilitaet, ObjektTyp, Norm, Severity, senkrechteFlaecheTyp
from windlast_CORE.datenstruktur.konstanten import _EPS

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
            "norm": norm.name,
            "element_id": self.element_id_intern,
            "objekttyp": self.objekttyp.name,
            "flaechentyp": self.flaeche_typ.name if self.flaeche_typ else None,
            "windrichtung": windrichtung,
        })

        # Unterscheidung Wand / Anzeigetafel
        oberkante = max(p[2] for p in self.eckpunkte)
        unterkante = min(p[2] for p in self.eckpunkte)
        hoehe = oberkante - unterkante

        v1 = vektor_zwischen_punkten(self.eckpunkte[0], self.eckpunkte[1])
        v2 = vektor_zwischen_punkten(self.eckpunkte[1], self.eckpunkte[2])
        if is_senkrecht('vecs', vecs=[v1, (0.0, 0.0, 1.0)]):
            breite = vektor_laenge(v1)
        else:
            breite = vektor_laenge(v2)

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
            staudruck = 0.0
            for i, grenze in enumerate(obergrenzen):
                if mitte_hoehe <= grenze:
                    staudruck = staudruecke[i]
                    break

            _kraftbeiwert = kraftbeiwert(
                norm, objekttyp=self.objekttyp, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ, punkte=self.eckpunkte,
                protokoll=protokoll, kontext=kontext
            )
            _bezugsflaeche = projizierte_flaeche(
                norm, objekttyp=self.objekttyp, punkte=self.eckpunkte,
                protokoll=protokoll, kontext=kontext
            )
            _windkraft = windkraft(
                norm, objekttyp=self.objekttyp, kraftbeiwert=_kraftbeiwert.wert, staudruck=staudruck, projizierte_flaeche=_bezugsflaeche.wert,senkrechte_flaeche_typ=self.flaeche_typ,
                protokoll=protokoll, kontext=kontext
            )
            _windkraft_vec = windkraft_zu_vektor(
                norm, objekttyp=self.objekttyp, punkte=self.eckpunkte, windkraft=_windkraft.wert, windrichtung=windrichtung, senkrechte_flaeche_typ=self.flaeche_typ,
                protokoll=protokoll, kontext=kontext
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
        else:
            protokolliere_msg(
                    protokoll,
                    severity=Severity.ERROR,
                    code="WINDKRAEFTE/NOT_IMPLEMENTED",
                    text=f"Windkraefte für Flächetyp {self.flaeche_typ.name} sind noch nicht implementiert.",
                    kontext=base_ctx,
            )
            return []