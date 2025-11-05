from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import sys
from typing import Dict, Optional, Tuple
from windlast_CORE.datenstruktur.enums import MaterialTyp
import warnings

# --- Datamodels -----------------------------------------------------------

@dataclass(frozen=True)
class BodenplatteSpec:
    name_intern: str
    anzeige_name: str
    kantenlaenge: float #fliegt
    gewicht: float
    # Neue Daten
    anzahl_ecken: int
    breite: float
    tiefe: float
    hoehe: float

@dataclass(frozen=True)
class TraverseSpec:
    name_intern: str
    anzeige_name: str
    anzahl_gurtrohre: int
    hoehe: float #fliegt
    d_gurt: float
    d_diagonalen: float #fliegt
    gewicht_linear: float
    # Neue Version der Traversendaten
    end: bool
    A_hoehe: float
    A_d_diagonalen: float
    A_winkel: float
    A_abstand: float
    A_invert: bool
    B_hoehe: float
    B_d_diagonalen: float
    B_winkel: float
    B_abstand: float
    B_invert: bool

@dataclass(frozen=True)
class RohrSpec:
    name_intern: str
    anzeige_name: str
    d_aussen: float
    t_wand: float
    dichte: float

Pair = Tuple[MaterialTyp, MaterialTyp]

def _norm_pair(a: MaterialTyp, b: MaterialTyp) -> Pair:
    """reihenfolgeunabhängig: (a,b) == (b,a)"""
    return tuple(sorted((a, b), key=lambda x: x.value))  # type: ignore[return-value]

# --- Resource path helper (PyInstaller-kompatibel) ------------------------

def _resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return (base / rel).resolve()

# --- Loader ---------------------------------------------------------------

def _load_bodenplatten_csv(csv_path: Path) -> Dict[str, BodenplatteSpec]:
    bp_map: Dict[str, BodenplatteSpec] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"name_intern", "anzeige_name", "anzahl_ecken", "breite_m", "tiefe_m", "hoehe_m", "gewicht_kg"}
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
                    kantenlaenge=float(row["breite_m"]), # fliegt
                    gewicht=float(row["gewicht_kg"]),
                    # Neue Daten
                    anzahl_ecken=int(row["anzahl_ecken"]),
                    breite=float(row["breite_m"]),
                    tiefe=float(row["tiefe_m"]),
                    hoehe=float(row["hoehe_m"]),
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
            "name_intern", "anzeige_name", "anzahl_gurtrohre", "gewicht_linear_kg_m",
            "d_gurt_m", "end_bool", "A_hoehe_m", "A_d_diagonalen_m", "A_winkel_deg",
            "A_abstand_m", "A_invert_bool", "B_hoehe_m", "B_d_diagonalen_m", "B_winkel_deg",
            "B_abstand_m", "B_invert_bool"
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
                    hoehe=float(row["A_hoehe_m"]), #fliegt
                    d_gurt=float(row["d_gurt_m"]),
                    d_diagonalen=float(row["A_d_diagonalen_m"]), #fliegt
                    gewicht_linear=float(row["gewicht_linear_kg_m"]),
                    # Neue Version der Traversendaten
                    end=row["end_bool"].strip().lower() == "true",
                    A_hoehe=float(row["A_hoehe_m"]),
                    A_d_diagonalen=float(row["A_d_diagonalen_m"]),
                    A_winkel=float(row["A_winkel_deg"]),
                    A_abstand=float(row["A_abstand_m"]),
                    A_invert=row["A_invert_bool"].strip().lower() == "true",
                    B_hoehe=float(row["B_hoehe_m"]),
                    B_d_diagonalen=float(row["B_d_diagonalen_m"]),
                    B_winkel=float(row["B_winkel_deg"]),
                    B_abstand=float(row["B_abstand_m"]),
                    B_invert=row["B_invert_bool"].strip().lower() == "true",
                )
            except Exception as e:
                raise ValueError(f"Ungültige Werte in Zeile mit name_intern='{key}': {e}") from e

            if key in tr_map:
                raise ValueError(f"Doppelter name_intern in {csv_path.name}: {key}")
            tr_map[key] = tr
    return tr_map

def _load_rohre_csv(csv_path: Path) -> Dict[str, RohrSpec]:
    rohr_map: Dict[str, RohrSpec] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"name_intern", "anzeige_name", "d_aussen_m", "t_wand_m", "dichte_kg_m3"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Fehlende Spalten in {csv_path.name}: {sorted(missing)}")

        for row in reader:
            key = (row["name_intern"] or "").strip()
            if not key:
                continue
            try:
                rohr = RohrSpec(
                    name_intern=key,
                    anzeige_name=row["anzeige_name"].strip(),
                    d_aussen=float(row["d_aussen_m"]),
                    t_wand=float(row["t_wand_m"]),
                    dichte=float(row["dichte_kg_m3"]),
                )
            except Exception as e:
                raise ValueError(f"Ungültige Werte in Zeile mit name_intern='{key}': {e}") from e

            if key in rohr_map:
                raise ValueError(f"Doppelter name_intern in {csv_path.name}: {key}")
            rohr_map[key] = rohr
    return rohr_map

# --- Registry (einmal laden, überall nutzen) -----------------------------

class Catalog:
    def __init__(self, daten_root: Optional[Path] = None) -> None:
        if hasattr(sys, "_MEIPASS"):
            # in der EXE: Daten liegen im Bundle unter windlast_CORE/materialdaten
            base = Path(sys._MEIPASS) / "windlast_CORE" / "materialdaten"
        else:
            # Dev: Ordner der aktuellen Datei
            base = Path(__file__).resolve().parent
        self._root = daten_root or base
        self._bodenplatten = _load_bodenplatten_csv(self._root / "bodenplatten.csv")
        self._traversen = _load_traversen_csv(self._root / "traversen.csv")
        self._rohre = _load_rohre_csv(self._root / "rohre.csv")

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
        
    @property
    def rohre(self) -> Dict[str, RohrSpec]:
        return self._rohre
    
    def get_rohr(self, name_intern: str) -> RohrSpec:
        try:
            return self._rohre[name_intern]
        except KeyError:
            raise KeyError(
                f"Rohr name_intern='{name_intern}' nicht gefunden. "
                f"Vorhanden: {', '.join(self._rohre)}"
            )


    def reload(self) -> None:
        self._bodenplatten = _load_bodenplatten_csv(self._root / "bodenplatten.csv")
        self._traversen = _load_traversen_csv(self._root / "traversen.csv")
        self._rohre = _load_rohre_csv(self._root / "rohre.csv")

catalog = Catalog()
