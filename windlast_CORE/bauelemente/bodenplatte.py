from dataclasses import dataclass
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.datenstruktur.konstanten import PhysikKonstanten, aktuelle_konstanten
from windlast_CORE.datenstruktur.zwischenergebnis import Protokoll, merge_kontext, protokolliere_msg
from typing import List, Optional
from windlast_CORE.rechenfunktionen import (
    Vec3,
    vektor_laenge,
    vektor_normieren,
    vektor_invertieren, 
    vektor_skalarprodukt,
    flaechenschwerpunkt,
    vektor_parallelanteil,
    vektor_senkrechtanteil,
    senkrechter_vektor,
    vektoren_addieren,
    vektor_multiplizieren,
    reibwert as reibwert_fn,
)
from windlast_CORE.datenstruktur.enums import ObjektTyp, MaterialTyp, Lasttyp, Variabilitaet, FormTyp, Norm, Severity
from windlast_CORE.datenstruktur.kraefte import Kraefte
from windlast_CORE.datenstruktur.konstanten import _EPS

@dataclass
class Bodenplatte:
    name_intern: str
    mittelpunkt: Vec3
    orientierung: Vec3
    drehung: Vec3 # Einheitsvektor entlang der langen Kante, senkrecht zur Orientierung
    form: FormTyp
    material: MaterialTyp
    untergrund: MaterialTyp
    gummimatte: Optional[MaterialTyp] = None
    objekttyp: ObjektTyp = ObjektTyp.BODENPLATTE
    element_id_intern: Optional[str] = None
    anzeigename: Optional[str] = None

    def __post_init__(self):
        if not self.anzeigename:
            try:
                specs = catalog.get_bodenplatte(self.name_intern)
                self.anzeigename = specs.anzeige_name or self.name_intern
            except Exception:
                self.anzeigename = self.name_intern

    def gesamthoehe(self) -> float:
        return self.mittelpunkt[2]
    
    def gewichtskraefte(
        self, *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
    ) -> List[Kraefte]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Gewichtskräfte",
            "element_id": self.element_id_intern,
            "objekttyp": self.objekttyp.value,
            "objekt_name": self.anzeigename,
        })
        try:
            specs = catalog.get_bodenplatte(self.name_intern)
            gewichtskraft = -1 * float(specs.gewicht) * aktuelle_konstanten().erdbeschleunigung  # [N]
        except Exception as e:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="BOP/LOOKUP_FAILED",
                text=f"Bodenplatte '{self.name_intern}': Katalogzugriff fehlgeschlagen ({e}).",
                kontext=base_ctx,
            )
            return []

        try:
            ecken = self.eckpunkte(protokoll=protokoll, kontext=base_ctx)
            schwerpunkt = flaechenschwerpunkt(ecken) if ecken else self.mittelpunkt
        except Exception as e:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="BOP/ECKPUNKTE_FAILED",
                text=f"Eckpunkte/Schwerpunkt konnten nicht ermittelt werden ({e}).",
                kontext=base_ctx,
            )
            ecken = []
            schwerpunkt = self.mittelpunkt

        einzelkraefte_vektoren: list[Vec3] = [(0.0, 0.0, gewichtskraft)]
        angriffsbereiche: list[list[Vec3]] = [ecken]

        return [Kraefte(
            element_id_intern=self.element_id_intern,
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=einzelkraefte_vektoren,
            Angriffsflaeche_Einzelkraefte=angriffsbereiche,
            Schwerpunkt=schwerpunkt,
        )]
    
    def reibwert_effektiv(
        self, norm: Norm, *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
    ) -> float:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Reibwert",
            "element_id": self.element_id_intern,
            "objekt_name": self.anzeigename,
        })
        materialfolge = [self.material, self.gummimatte, self.untergrund]
        return reibwert_fn(
            norm, materialfolge, protokoll=protokoll, kontext=base_ctx
        ).wert
    
    def reibkraefte(
        self, norm: Norm, belastung: Vec3, *,
        protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
    ) -> List[Kraefte]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Reibkräfte",
            "element_id": self.element_id_intern,
            "objekttyp": self.objekttyp.value,
            "objekt_name": self.anzeigename,
            "belastung": belastung,
        })
        # Reibwert ermitteln
        _materialfolge = [self.material, self.gummimatte, self.untergrund]
        _reibwert = reibwert_fn(
            norm, _materialfolge, protokoll=protokoll, kontext=base_ctx
        ).wert

        # Belastungsrichtung prüfen
        _belastungsrichtung = vektor_skalarprodukt(belastung, self.orientierung)
        # Tangentialkomponente prüfen
        _belastung_tangential = vektor_senkrechtanteil(belastung, self.orientierung)

        if _belastungsrichtung >=-_EPS or vektor_laenge(_belastung_tangential) < _EPS:
            _reibkraft = (0.0, 0.0, 0.0)  # Keine Reibung bei Zugkräften oder senkrechter Belastung
        else:
            # Normalkraft (parallel zu Orientierung) berechnen
            _normalkraft = vektor_parallelanteil(belastung, self.orientierung)
            _normalkraft_betrag = vektor_laenge(_normalkraft)

            # Reibkraft Richtung bestimmen
            _reibkraft_richtung = vektor_invertieren(vektor_normieren(_belastung_tangential))

            # Reibkraft berechnen
            _reibkraft_betrag = _reibwert * _normalkraft_betrag
            _reibkraft = (
                _reibkraft_richtung[0] * _reibkraft_betrag,
                _reibkraft_richtung[1] * _reibkraft_betrag,
                _reibkraft_richtung[2] * _reibkraft_betrag,
            )
        
        try:
            angriffsbereich = self.eckpunkte(protokoll=protokoll, kontext=base_ctx)
        except Exception as e:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="BOP/ECKPUNKTE_FAILED",
                text=f"Eckpunkte konnten für Reibkraft nicht ermittelt werden ({e}).",
                kontext=base_ctx,
            )
            angriffsbereich = []

        return [Kraefte(
            element_id_intern=self.element_id_intern,
            typ=Lasttyp.REIBUNG,
            variabilitaet=Variabilitaet.VERAENDERLICH,
            Einzelkraefte=[_reibkraft],
            Angriffsflaeche_Einzelkraefte=[angriffsbereich],
        )]
    
    def eckpunkte(
        self, *, protokoll: Optional[Protokoll] = None, kontext: Optional[dict] = None
    ) -> List[Vec3]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Eckpunkte",
            "element_id": self.element_id_intern,
            "objekttyp": self.objekttyp.value,
            "objekt_name": self.anzeigename,
            "form": self.form.value,
        })

        if self.form == FormTyp.RECHTECK:
            spec = catalog.get_bodenplatte(self.name_intern)
            kantenlaenge = spec.kantenlaenge
            if kantenlaenge is None or kantenlaenge <= 0:
                protokolliere_msg(
                    protokoll, severity=Severity.ERROR, code="BOP/KANTENLAENGE_INVALID",
                    text=f"Bodenplatte '{self.name_intern}' hat keine gültige Kantenlänge.",
                    kontext=merge_kontext(base_ctx, {"kantenlaenge": kantenlaenge}),
                )
                return []
            halbe_kante = kantenlaenge / 2.0

            richtung1 = vektor_normieren(self.drehung)
            halbe_kante1 = vektor_multiplizieren(richtung1, halbe_kante)
            richtung2 = senkrechter_vektor(richtung1, self.orientierung)
            halbe_kante2 = vektor_multiplizieren(richtung2, halbe_kante)

            ecke1 = vektoren_addieren([self.mittelpunkt, halbe_kante1, halbe_kante2])
            ecke2 = vektoren_addieren([self.mittelpunkt, halbe_kante1, vektor_invertieren(halbe_kante2)])
            ecke3 = vektoren_addieren([self.mittelpunkt, vektor_invertieren(halbe_kante1), vektor_invertieren(halbe_kante2)])
            ecke4 = vektoren_addieren([self.mittelpunkt, vektor_invertieren(halbe_kante1), halbe_kante2])

            return [ecke1, ecke2, ecke3, ecke4]
        else:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="BOP/FORM_UNSUPPORTED",
                text=f"Eckpunkte für Form {self.form.name} noch nicht implementiert.",
                kontext=base_ctx,
            )
            return []