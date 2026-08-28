from pydantic import BaseModel, Field, PositiveFloat
from typing import Literal, Dict, Any, List, Optional, Annotated
from pydantic import BaseModel, ConfigDict, Field

MAX_BAUELEMENTE = 100

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

Vec3 = tuple[float, float, float]


class BauelementBase(BaseModel):
    model_config = ConfigDict(extra="allow")

    element_id_intern: str | None = None
    anzeigename: str | None = None


class TraversenstreckeInput(BauelementBase):
    typ: Literal["Traversenstrecke"]

    traverse_name_intern: str
    start: Vec3
    ende: Vec3
    orientierung: Vec3


class BodenplatteInput(BauelementBase):
    typ: Literal["Bodenplatte"]

    name_intern: str
    mittelpunkt: Vec3
    orientierung: Vec3
    drehung: Vec3

    untergrund: str | None = None
    gummimatte: str | None = None


class RohrInput(BauelementBase):
    typ: Literal["Rohr"]

    rohr_name_intern: str
    start: Vec3
    ende: Vec3


class SenkrechteFlaecheInput(BauelementBase):
    typ: Literal["senkrechteFlaeche"]

    eckpunkte: list[Vec3]

    flaeche_typ: str | None = None
    flaechenlast: float | None = None
    gesamtgewicht: float | None = None


BauelementInput = Annotated[
    TraversenstreckeInput
    | BodenplatteInput
    | RohrInput
    | SenkrechteFlaecheInput,
    Field(discriminator="typ"),
]


class KonstruktionBuildInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: Literal[1]
    typ: str
    name: str

    bauelemente: list[BauelementInput] = Field(
        max_length=MAX_BAUELEMENTE
    )


class KonstruktionInput(BaseModel):
    konstruktion: KonstruktionBuildInput
    aufstelldauer: DauerInput | None = None
    windzone: str

# =========================
# Output-Modelle
# =========================

NumberLike = float | str | None  # "INF" | "-INF" | None | float

class ResultDoc(BaseModel):
    title: Optional[str] = None
    value: Any = None
    unit: Optional[str] = None
    formula: Optional[str] = None
    formula_source: Optional[str] = None
    symbols: Optional[List[Any]] = None
    symbols_source: Optional[List[Any]] = None
    items: Optional[List[Any]] = None          # i.d.R. Liste von ["Name", Wert]-Paaren
    items_source: Optional[List[Any]] = None
    context: Dict[str, Any] = Field(default_factory=dict)

class ResultMessage(BaseModel):
    # wir erlauben jeden String für mögliche Erweiterungen; Tooltips filtern/normalisieren später
    severity: str | None = None      # "error" | "warn" | "hint" | "info" | ...
    text: str | None = None
    code: str | None = None
    context: Dict[str, Any] = Field(default_factory=dict)

class ResultNormAltVals(BaseModel):
    anzeigename: Optional[str] = None
    kipp:    NumberLike
    gleit:   NumberLike
    abhebe:  NumberLike
    ballast: NumberLike = None  # kg
    messages: List[ResultMessage] = Field(default_factory=list)
    docs: List[ResultDoc] = Field(default_factory=list)

class ResultNormVals(BaseModel):
    kipp:    NumberLike
    gleit:   NumberLike
    abhebe:  NumberLike
    ballast: NumberLike = None  # kg
    alternativen: Dict[str, ResultNormAltVals] | None = None  # z.B. {"IN_BETRIEB": {...}}
    # NEU: flache Nachrichtenliste pro Norm (Text, Severity, Kontext)
    messages: List[ResultMessage] = Field(default_factory=list)
    docs: List[ResultDoc] = Field(default_factory=list)

class Result(BaseModel):
    normen: Dict[str, ResultNormVals]
    meta: Dict[str, Any]
