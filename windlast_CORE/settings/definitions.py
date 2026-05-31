from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SettingType = Literal["bool", "int", "float", "string", "enum"]


@dataclass(frozen=True)
class SettingDef:
    key: str
    label: str
    type: SettingType
    default: Any

    group: str = "allgemein"
    description: str | None = None

    min: int | float | None = None
    max: int | float | None = None

    allowed: list[Any] | None = None
    options: dict[str, str] | None = None

    meta: dict[str, Any] = field(default_factory=dict)


SETTING_DEFS: list[SettingDef] = [
    # SettingDef(
    #     key="ui.show_expert_details",
    #     group="ui",
    #     label="Experten-Details anzeigen",
    #     type="bool",
    #     default=False,
    #     description="Zeigt zusätzliche technische Details in der Oberfläche an.",
    # ),

    # SettingDef(
    #     key="ui.detail_level",
    #     group="ui",
    #     label="Detailgrad",
    #     type="enum",
    #     default="standard",
    #     options={
    #         "minimal": "Minimal",
    #         "standard": "Standard",
    #         "expert": "Experte",
    #     },
    # ),

    SettingDef(
        key="main.sprache",
        group="main",
        label="Sprache",
        type="enum",
        default="de",
        options={
            "de": "Deutsch",
        },
    ),

    SettingDef(
        key="berechnung.windrichtungen_anzahl",
        group="berechnung",
        label="Anzahl Windrichtungen",
        type="int",
        default=8,
        min=4,
        max=36,
        allowed=[4, 8, 12, 16, 24, 36],
    ),

    SettingDef(
        key="ui.theme",
        group="ui",
        label="Farbschema",
        type="enum",
        default="light",
        options={
            "light": "Hell",
            "dark": "Dunkel",
            "special": "Spezial",
        },

    ),
]