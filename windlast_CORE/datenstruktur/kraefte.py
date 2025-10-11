from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List
from windlast_CORE.datenstruktur.enums import Lasttyp, Variabilitaet
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektoren_addieren, flaechenschwerpunkt
from windlast_CORE.datenstruktur.konstanten import _EPS

@dataclass
class Kraefte:
    """
    Ein Ergebnisobjekt pro Bauelement & Lastfall.
    - Resultierende wird automatisch aus Einzelkräften berechnet.
    - Angriffsflächen/-linien/-punkte: pro Kraft eine Liste von Eckpunkten.
      Struktur: [[Flaeche1_P1, Flaeche1_P2, ...], [Flaeche2_P1, ...], ...]
      Für Punktlast: Liste mit genau 1 Punkt. Für Linie: >=2 Punkte. Für Fläche: >=3 Punkte.
    """
    typ: Lasttyp                         # WIND / GEWICHT / REIBUNG
    variabilitaet: Variabilitaet         # STAENDIG / VERAENDERLICH

    Einzelkraefte: List[Vec3]            # [N] – eine oder mehrere Kräfte
    Angriffsflaeche_Einzelkraefte: List[List[Vec3]] = field(default_factory=list)  # [m]
    Schwerpunkt: Optional[Vec3] = None   # [m] – bei Gewicht

    # wird automatisch gesetzt (Summe der Einzelkräfte)
    Resultierende: Vec3 = field(init=False)
    Angriffspunkte_Einzelkraefte: List[Vec3] = field(init=False)  # [m] ein Punkt je Einzelkraft

    lastfall_id_intern: Optional[str] = None
    element_id_intern: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate()
        self.Resultierende = vektoren_addieren(self.Einzelkraefte)
        self._setze_angriffspunkte()

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
                    
    def _setze_angriffspunkte(self) -> None:
        """Erzeugt self.angriffspunkte_einzelkraefte 1:1 zu self.Einzelkraefte.
        - Falls Angriffsgeometrien vorhanden: Schwerpunkt je Geometrie.
        - Sonst: Schwerpunkt-Fallback.
        """
        self.Angriffspunkte_Einzelkraefte = []

        if self.Angriffsflaeche_Einzelkraefte:
            # Schwerpunkt je zugehöriger Geometrie (Punkt/Linie/Fläche)
            for poly in self.Angriffsflaeche_Einzelkraefte:
                sp = flaechenschwerpunkt(poly)
                self.Angriffspunkte_Einzelkraefte.append(sp)
        else:
            # Kein Polygon/Segment/Punkt pro Kraft angegeben → auf globalen Schwerpunkt zurückfallen
            if self.Schwerpunkt is None:
                raise ValueError("Kein Angriffspunkt ableitbar: weder Angriffsflächen noch Schwerpunkt gesetzt.")
            self.Angriffspunkte_Einzelkraefte = [self.Schwerpunkt for _ in self.Einzelkraefte]

        if len(self.Angriffspunkte_Einzelkraefte) != len(self.Einzelkraefte):
            raise RuntimeError(
                "Anzahl der Angriffspunkte passt nicht zu den Einzelkräften "
                f"({len(self.Angriffspunkte_Einzelkraefte)} vs. {len(self.Einzelkraefte)})."
            )

    # optional: falls du nach dem Erzeugen die Kräfte änderst
    def aktualisiere_resultierende(self) -> None:
        self.Resultierende = vektoren_addieren(self.Einzelkraefte)
    def aktualisiere_angriffspunkte(self) -> None:
        self._setze_angriffspunkte()