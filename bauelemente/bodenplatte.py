from dataclasses import dataclass
from materialdaten.catalog import catalog

@dataclass
class Bodenplatte:
    name_intern: str
    # später: abmessungen, gewicht, reibbeiwert, etc.

    def gewicht(self) -> float:
        """Gewicht in kg anhand des internen Namens aus dem Katalog."""
        spec = catalog.get_bodenplatte(self.name_intern)
        return float(spec.gewicht_kg)