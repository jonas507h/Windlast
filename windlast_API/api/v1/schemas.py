from pydantic import BaseModel, Field, PositiveFloat
from typing import Literal, Dict, Any, List

# Input-Modelle
class DauerInput(BaseModel):
    wert: int = Field(gt=0)
    einheit: Literal["TAG", "MONAT", "JAHR"]  # Enum-Name

class TorInput(BaseModel):
    breite_m: PositiveFloat
    hoehe_m: PositiveFloat
    traverse_name_intern: str
    bodenplatte_name_intern: str
    untergrund_typ: str  # MaterialTyp.value (z.B. "beton")
    aufstelldauer: DauerInput | None = None
    windzone: str  # Windzone Enum-Name (z.B. "III_Binnenland")

# =========================
# Output-Modelle
# =========================

NumberLike = float | str | None  # "INF" | "-INF" | None | float

class ResultNormAltVals(BaseModel):
    kipp:    NumberLike
    gleit:   NumberLike
    abhebe:  NumberLike
    ballast: NumberLike = None  # kg

class ResultMessage(BaseModel):
    # wir erlauben jeden String für mögliche Erweiterungen; Tooltips filtern/normalisieren später
    severity: str | None = None      # "error" | "warn" | "hint" | "info" | ...
    text: str | None = None
    code: str | None = None
    context: Dict[str, Any] = Field(default_factory=dict)

class ResultNormVals(BaseModel):
    kipp:    NumberLike
    gleit:   NumberLike
    abhebe:  NumberLike
    ballast: NumberLike = None  # kg
    alternativen: Dict[str, ResultNormAltVals] | None = None  # z.B. {"IN_BETRIEB": {...}}
    # NEU: flache Nachrichtenliste pro Norm (Text, Severity, Kontext)
    messages: List[ResultMessage] = Field(default_factory=list)

class Result(BaseModel):
    normen: Dict[str, ResultNormVals]
    meta: Dict[str, Any]
