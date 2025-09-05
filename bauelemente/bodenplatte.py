from dataclasses import dataclass
from materialdaten.catalog import catalog
from datenstruktur.konstanten import PhysikKonstanten, aktuelle_konstanten
from typing import List, Optional
from rechenfunktionen import (
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
    reibwert,
)
from datenstruktur.enums import ObjektTyp, MaterialTyp, Lasttyp, Variabilitaet, FormTyp
from datenstruktur.kraefte import Kraefte

_EPS = 1e-9

@dataclass
class Bodenplatte:
    name_intern: str
    mittelpunkt: Vec3
    orientierung: Vec3
    drehung: Vec3 # Einheitsvektor entlang der langen Kante, senkrecht zur Orientierung
    form: FormTyp
    material: MaterialTyp
    gummimatte: Optional[MaterialTyp] = None
    untergrund: MaterialTyp
    objekttyp: ObjektTyp = ObjektTyp.BODENPLATTE
    element_id_intern: Optional[str] = None
    
    def gewichtskraefte(self) -> List[Kraefte]:
        specs = catalog.get_bodenplatte(self.name_intern)
        gewichtskraft = -1 * float(specs.gewicht) * aktuelle_konstanten().erdbeschleunigung  # [N/m]

        einzelkraefte_vektoren: list[Vec3] = [(0.0, 0.0, gewichtskraft)]

        angriffsbereiche: list[list[Vec3]] = [self.eckpunkte()]

        schwerpunkt = flaechenschwerpunkt(self.eckpunkte())

        return [Kraefte(
            element_id_intern=self.element_id_intern,
            typ=Lasttyp.GEWICHT,
            variabilitaet=Variabilitaet.STAENDIG,
            Einzelkraefte=einzelkraefte_vektoren,
            Angriffsflaeche_Einzelkraefte=angriffsbereiche,
            Schwerpunkt=schwerpunkt,
        )]
    
    def reibkraefte(self, belastung: Vec3) -> List[Kraefte]:
        # Reibwert ermitteln
        _materialfolge = [self.material, self.gummimatte, self.untergrund]
        _reibwert = reibwert(_materialfolge).wert

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
        return [Kraefte(
            element_id_intern=self.element_id_intern,
            typ=Lasttyp.REIBUNG,
            variabilitaet=Variabilitaet.VERAENDERLICH,
            Einzelkraefte=[_reibkraft],
            Angriffsflaeche_Einzelkraefte=[self.eckpunkte()],
        )]
    
    def eckpunkte(self) -> List[Vec3]:
        if self.form != FormTyp.RECHTECK:
            raise NotImplementedError(f"Eckpunkte für Form {self.form} noch nicht implementiert.")

        if self.form == FormTyp.RECHTECK:
            spec = catalog.get_bodenplatte(self.name_intern)
            kantenlaenge = spec.kantenlaenge
            if kantenlaenge is None or kantenlaenge <= 0:
                raise ValueError(f"Bodenplatte '{self.name_intern}' hat keine gültige Kantenlänge.")
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