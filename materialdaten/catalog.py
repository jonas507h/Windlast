from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import sys
from typing import Dict, Optional

# --- Datamodels -----------------------------------------------------------

@dataclass(frozen=True)
class BodenplatteSpec:
    name_intern: str
    anzeige_name: str
    kantenlaenge: float
    gewicht: float

@dataclass(frozen=True)
class TraverseSpec:
    name_intern: str
    anzeige_name: str
    anzahl_gurtrohre: int
    hoehe: float
    d_gurt: float
    d_diagonalen: float
    gewicht_linear: float

# --- Resource path helper (PyInstaller-kompatibel) ------------------------

def _resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return (base / rel).resolve()

# --- Loader ---------------------------------------------------------------

def _load_bodenplatten_csv(csv_path: Path) -> Dict[str, BodenplatteSpec]:
    bp_map: Dict[str, BodenplatteSpec] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"name_intern", "anzeige_name", "kantenlaenge_m", "gewicht_kg"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Fehlende Spalten in {csv_path.name}: {sorted(missing)}")

        for row in reader:
            key = row["name_intern"].strip()
            if not key:
                continue
            try:
                bp = BodenplatteSpec(
                    name_intern=key,
                    anzeige_name=row["anzeige_name"].strip(),
                    kantenlaenge_m=float(row["kantenlaenge_m"]),
                    gewicht_kg=float(row["gewicht_kg"]),
                )
            except Exception as e:
                raise ValueError(f"Ungültige Werte in Zeile mit name_intern='{key}': {e}") from e

            if key in bp_map:
                raise ValueError(f"Doppelter name_intern in {csv_path.name}: {key}")
            bp_map[key] = bp
    return bp_map

def _load_traversen_csv(csv_path: Path) -> Dict[str, TraverseSpec]:
    tr_map: Dict[str, TraverseSpec] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "name_intern", "anzeige_name", "anzahl_gurtrohre",
            "hoehe_m", "d_gurt_m", "d_diagonalen_m", "gewicht_linear_kg_m"
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Fehlende Spalten in {csv_path.name}: {sorted(missing)}")

        for row in reader:
            key = (row["name_intern"] or "").strip()
            if not key:
                continue
            try:
                tr = TraverseSpec(
                    name_intern=key,
                    anzeige_name=row["anzeige_name"].strip(),
                    anzahl_gurtrohre=int(row["anzahl_gurtrohre"]),
                    hoehe_m=float(row["hoehe_m"]),
                    d_gurt_m=float(row["d_gurt_m"]),
                    d_diagonalen_m=float(row["d_diagonalen_m"]),
                    gewicht_linear_kg_m=float(row["gewicht_linear_kg_m"]),
                )
            except Exception as e:
                raise ValueError(f"Ungültige Werte in Zeile mit name_intern='{key}': {e}") from e

            if key in tr_map:
                raise ValueError(f"Doppelter name_intern in {csv_path.name}: {key}")
            tr_map[key] = tr
    return tr_map

# --- Registry (einmal laden, überall nutzen) -----------------------------

class Catalog:
    def __init__(self, daten_root: Optional[Path] = None) -> None:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        self._root = daten_root or base
        self._bodenplatten = _load_bodenplatten_csv(self._root / "bodenplatten.csv")
        self._traversen = _load_traversen_csv(self._root / "traversen.csv")

    @property
    def bodenplatten(self) -> Dict[str, BodenplatteSpec]:
        return self._bodenplatten

    def get_bodenplatte(self, name_intern: str) -> BodenplatteSpec:
        try:
            return self._bodenplatten[name_intern]
        except KeyError:
            raise KeyError(
                f"Bodenplatte name_intern='{name_intern}' nicht gefunden. "
                f"Vorhanden: {', '.join(self._bodenplatten)}"
            )
    
    @property 
    def traversen(self) -> Dict[str, TraverseSpec]:
        return self._traversen

    def get_traverse(self, name_intern: str) -> TraverseSpec:
        try:
            return self._traversen[name_intern]
        except KeyError:
            raise KeyError(
                f"Traverse name_intern='{name_intern}' nicht gefunden. "
                f"Vorhanden: {', '.join(self._traversen)}"
            )

    def reload(self) -> None:
        self._bodenplatten = _load_bodenplatten_csv(self._root / "bodenplatten.csv")
        self._traversen = _load_traversen_csv(self._root / "traversen.csv")

catalog = Catalog()
