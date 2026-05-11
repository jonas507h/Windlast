from pydantic import BaseModel, Field, PositiveFloat
from typing import Literal, Dict, Any, List, Optional

# Input-Modelle
class DauerInput(BaseModel):
    wert: int = Field(gt=0)
    einheit: Literal["TAG", "MONAT", "JAHR"]  # Enum-Name

# class TorInput(BaseModel):
#     breite_m: PositiveFloat
#     hoehe_m: PositiveFloat
#     traverse_name_intern: str
#     bodenplatte_name_intern: str
#     orientierung: str
#     untergrund_typ: str  # MaterialTyp.value (z.B. "beton")
#     gummimatte: bool = True
#     aufstelldauer: DauerInput | None = None
#     windzone: str  # Windzone Enum-Name (z.B. "III_Binnenland")

# class SteherInput(BaseModel):
#     hoehe_m: PositiveFloat
#     rohr_laenge_m: PositiveFloat
#     rohr_hoehe_m: PositiveFloat
#     traverse_name_intern: str
#     bodenplatte_name_intern: str
#     rohr_name_intern: str
#     untergrund_typ: str  # MaterialTyp.value (z.B. "beton")
#     gummimatte: bool = True
#     aufstelldauer: DauerInput | None = None
#     windzone: str  # Windzone Enum-Name (z.B. "III_Binnenland")

# class TischInput(BaseModel):
#     breite_m: PositiveFloat
#     hoehe_m: PositiveFloat
#     tiefe_m: PositiveFloat
#     traverse_name_intern: str
#     bodenplatte_name_intern: str
#     untergrund_typ: str  # MaterialTyp.value (z.B. "beton")
#     gummimatte: bool = True
#     aufstelldauer: DauerInput | None = None
#     windzone: str  # Windzone Enum-Name (z.B. "III_Binnenland")

class KonstruktionInput(BaseModel):
    konstruktion: Dict[str, Any]  # Platzhalter für beliebige Konstruktion-Daten aus UI-Build
    aufstelldauer: DauerInput | None = None
    windzone: str  # Windzone Enum-Name (z.B. "III_Binnenland")

# =========================
# Output-Modelle
# =========================

class ErgebnisOut(BaseModel):
    name: str
    wert: Any
    label: Optional[str] = None
    formelzeichen: Any = None
    formel: Optional[str] = None
    einheit: Optional[str] = None
    priority: int = 0
    meta: Dict[str, Any] = Field(default_factory=dict)


class MessageOut(BaseModel):
    code: str
    severity: Any
    text: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class GruppeOut(BaseModel):
    name: str
    label: Optional[str] = None
    winner: Optional[bool] = None
    ergebnisse: List[ErgebnisOut] = Field(default_factory=list)
    messages: List[MessageOut] = Field(default_factory=list)
    ebenen: List["EbeneOut"] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class EbeneOut(BaseModel):
    name: str
    label: Optional[str] = None
    gruppen: List[GruppeOut] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ErgebnisBaumOut(BaseModel):
    ebenen: List[EbeneOut] = Field(default_factory=list)
    ergebnisse: List[ErgebnisOut] = Field(default_factory=list)
    messages: List[MessageOut] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class Result(BaseModel):
    ergebnis: ErgebnisBaumOut
    meta: Dict[str, Any] = Field(default_factory=dict)
