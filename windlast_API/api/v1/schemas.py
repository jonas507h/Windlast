from pydantic import BaseModel, Field, PositiveFloat
from typing import Literal, Dict

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

# Output-Minimalformat
class ResultNormVals(BaseModel):
    kipp: float | None
    gleit: float | None
    abhebe: float | None

class Result(BaseModel):
    normen: Dict[str, ResultNormVals]
    meta: dict
