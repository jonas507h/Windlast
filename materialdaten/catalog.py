from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import sys
from typing import Dict, Optional

# --- Datamodels -----------------------------------------------------------

@dataclass(frozen=True)
class BodenplatteSpec:
    id: str
    anzeige_name: str
    kantenlaenge_m: float
    gewicht_kg: float

# --- Resource path helper (PyInstaller-kompatibel) ------------------------

def _resource_path(rel: str) -> Path:
    """
    Liefert einen Pfad, der sowohl in der Dev-Umgebung als auch
    im PyInstaller-Bundle funktioniert.
    """
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return (base / rel).resolve()

# --- Loader ---------------------------------------------------------------

def _load_bodenplatten_csv(csv_path: Path) -> Dict[str, BodenplatteSpec]:
    bp_map: Dict[str, BodenplatteSpec] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"id", "anzeige_name", "kantenlaenge_m", "gewicht_kg"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Fehlende Spalten in {csv_path.name}: {sorted(missing)}")

        for row in reader:
            iid = row["id"].strip()
            if not iid:
                continue
            try:
                bp = BodenplatteSpec(
                    id=iid,
                    anzeige_name=row["anzeige_name"].strip(),
                    kantenlaenge_m=float(row["kantenlaenge_m"]),
                    gewicht_kg=float(row["gewicht_kg"]),
                )
            except Exception as e:
                raise ValueError(f"Ungültige Werte in Zeile mit id='{iid}': {e}") from e

            if iid in bp_map:
                raise ValueError(f"Doppelte id in {csv_path.name}: {iid}")
            bp_map[iid] = bp
    return bp_map

# --- Registry (einmal laden, überall nutzen) -----------------------------

class Catalog:
    def __init__(self, daten_root: Optional[Path] = None) -> None:
        # Standard: ../daten relativ zu diesem File (PyInstaller-safe)
        self._root = daten_root or _resource_path("materialdaten")
        self._bodenplatten = _load_bodenplatten_csv(self._root / "bodenplatten.csv")

    # Zugriffsmethoden
    @property
    def bodenplatten(self) -> Dict[str, BodenplatteSpec]:
        return self._bodenplatten

    def get_bodenplatte(self, iid: str) -> BodenplatteSpec:
        try:
            return self._bodenplatten[iid]
        except KeyError:
            raise KeyError(f"Bodenplatte id='{iid}' nicht gefunden. "
                           f"Vorhanden: {', '.join(self._bodenplatten)}")

    # optional: Reload, falls Datei zur Laufzeit geändert wird
    def reload(self) -> None:
        self._bodenplatten = _load_bodenplatten_csv(self._root / "bodenplatten.csv")

# Globale, einmalige Instanz (zentrale Stelle!)
catalog = Catalog()
