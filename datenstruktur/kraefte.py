from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List
from datenstruktur.enums import Lasttyp, Variabilitaet

Vec3 = Tuple[float, float, float]
EPS = 1e-9

@dataclass
class Kraefte:
    """
    Ein Ergebnisobjekt pro Bauelement & Lastfall.
    - Resultierende wird automatisch aus Einzelkräften berechnet.
    - Angriffsflächen/-linien/-punkte: pro Kraft eine Liste von Eckpunkten.
      Struktur: [[Flaeche1_P1, Flaeche1_P2, ...], [Flaeche2_P1, ...], ...]
      Für Punktlast: Liste mit genau 1 Punkt. Für Linie: >=2 Punkte. Für Fläche: >=3 Punkte.
    """
    typ: Lasttyp                         # WIND / GEWICHT
    variabilitaet: Variabilitaet         # STAENDIG / VERAENDERLICH

    Einzelkraefte: List[Vec3]            # [N] – eine oder mehrere Kräfte
    Angriffsflaeche_Einzelkraefte: List[List[Vec3]] = field(default_factory=list)  # [m]
    Schwerpunkt: Optional[Vec3] = None   # [m] – v.a. bei Gewicht

    # wird automatisch gesetzt (Summe der Einzelkräfte)
    Resultierende: Vec3 = field(init=False)

    def __post_init__(self) -> None:
        self._validate()
        self.Resultierende = self._sum_forces()

    # --- Helfer ---
    def _sum_forces(self) -> Vec3:
        Fx = Fy = Fz = 0.0
        for F in self.Einzelkraefte:
            Fx += F[0]; Fy += F[1]; Fz += F[2]
        return (Fx, Fy, Fz)

    def _validate(self) -> None:
        # Wenn Angriffsgeometrien angegeben sind, muss die Anzahl zur Kraftliste passen
        if self.Angriffsflaeche_Einzelkraefte:
            if len(self.Angriffsflaeche_Einzelkraefte) != len(self.Einzelkraefte):
                raise ValueError(
                    f"Anzahl Angriffsflächen ({len(self.Angriffsflaeche_Einzelkraefte)}) "
                    f"≠ Anzahl Kräfte ({len(self.Einzelkraefte)})."
                )
            # Jede Teil-Liste muss mind. 1 Punkt enthalten
            for i, poly in enumerate(self.Angriffsflaeche_Einzelkraefte):
                if not poly:
                    raise ValueError(f"Angriffsfläche #{i} ist leer.")
                for j, p in enumerate(poly):
                    if len(p) != 3:
                        raise ValueError(f"Punkt #{j} in Angriffsfläche #{i} ist kein Vec3: {p}")

    # optional: falls du nach dem Erzeugen die Kräfte änderst
    def aktualisiere_resultierende(self) -> None:
        self.Resultierende = self._sum_forces()
