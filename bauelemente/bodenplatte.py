from dataclasses import dataclass
from materialdaten.catalog import catalog
from rechenfunktionen import (
    Vec3,
    flaechenschwerpunkt,
)
from datenstruktur.enums import ObjektTyp, MaterialTyp

@dataclass
class Bodenplatte:
    name_intern: str
    mittelpunkt: Vec3
    orientierung: Vec3
    material: MaterialTyp
    gummimatte: MaterialTyp
    untergrund: MaterialTyp
    objekttyp: ObjektTyp = ObjektTyp.BODENPLATTE
    # später: abmessungen, gewicht, reibbeiwert, etc.

    def gewicht(self) -> float:
        """Gewicht in kg anhand des internen Namens aus dem Katalog."""
        spec = catalog.get_bodenplatte(self.name_intern)
        return float(spec.gewicht)