# windlast_CORE/materialdaten/reibwert_data.py
from __future__ import annotations
from typing import Dict, Tuple

from windlast_CORE.datenstruktur.enums import MaterialTyp, Norm

# Typ-Hinweis: Dict[Norm, Dict[Tuple[MaterialTyp, MaterialTyp], Tuple[float, str]]]
DATA_REIBWERTE = {
    Norm.DIN_EN_17879_2024_08: {
        (MaterialTyp.BETON, MaterialTyp.BETON): (0.5, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.GUMMI): (0.6, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.HOLZ): (0.6, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.KIES): (0.65, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.LEHM): (0.4, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.SAND): (0.65, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.STAHL): (0.2, "DIN EN 17879:2024-08"),
        (MaterialTyp.BETON, MaterialTyp.TON): (0.25, "DIN EN 17879:2024-08"),
        (MaterialTyp.GUMMI, MaterialTyp.HOLZ): (0.6, "DIN EN 17879:2024-08"),
        (MaterialTyp.GUMMI, MaterialTyp.STAHL): (0.6, "DIN EN 17879:2024-08"),
        (MaterialTyp.HOLZ, MaterialTyp.HOLZ): (0.4, "DIN EN 17879:2024-08"),
        (MaterialTyp.HOLZ, MaterialTyp.KIES): (0.65, "DIN EN 17879:2024-08"),
        (MaterialTyp.HOLZ, MaterialTyp.LEHM): (0.4, "DIN EN 17879:2024-08"),
        (MaterialTyp.HOLZ, MaterialTyp.SAND): (0.65, "DIN EN 17879:2024-08"),
        (MaterialTyp.HOLZ, MaterialTyp.STAHL): (0.4, "DIN EN 17879:2024-08"),
        (MaterialTyp.HOLZ, MaterialTyp.TON): (0.25, "DIN EN 17879:2024-08"),
        (MaterialTyp.KIES, MaterialTyp.STAHL): (0.2, "DIN EN 17879:2024-08"),
        (MaterialTyp.LEHM, MaterialTyp.STAHL): (0.2, "DIN EN 17879:2024-08"),
        (MaterialTyp.SAND, MaterialTyp.STAHL): (0.2, "DIN EN 17879:2024-08"),
        (MaterialTyp.STAHL, MaterialTyp.STAHL): (0.15, "DIN EN 17879:2024-08"),
        (MaterialTyp.TON, MaterialTyp.STAHL): (0.2, "DIN EN 17879:2024-08"),
    },
    Norm.DIN_EN_13814_2005_06: {
        (MaterialTyp.BETON, MaterialTyp.BETON): (0.5, "DIN EN 13814:2005-06"),
        (MaterialTyp.BETON, MaterialTyp.HOLZ): (0.6, "DIN EN 13814:2005-06"),
        (MaterialTyp.BETON, MaterialTyp.KIES): (0.65, "DIN EN 13814:2005-06"),
        (MaterialTyp.BETON, MaterialTyp.LEHM): (0.4, "DIN EN 13814:2005-06"),
        (MaterialTyp.BETON, MaterialTyp.SAND): (0.65, "DIN EN 13814:2005-06"),
        (MaterialTyp.BETON, MaterialTyp.STAHL): (0.2, "DIN EN 13814:2005-06"),
        (MaterialTyp.BETON, MaterialTyp.TON): (0.25, "DIN EN 13814:2005-06"),
        (MaterialTyp.HOLZ, MaterialTyp.HOLZ): (0.4, "DIN EN 13814:2005-06"),
        (MaterialTyp.HOLZ, MaterialTyp.KIES): (0.65, "DIN EN 13814:2005-06"),
        (MaterialTyp.HOLZ, MaterialTyp.LEHM): (0.4, "DIN EN 13814:2005-06"),
        (MaterialTyp.HOLZ, MaterialTyp.SAND): (0.65, "DIN EN 13814:2005-06"),
        (MaterialTyp.HOLZ, MaterialTyp.STAHL): (0.4, "DIN EN 13814:2005-06"),
        (MaterialTyp.HOLZ, MaterialTyp.TON): (0.25, "DIN EN 13814:2005-06"),
        (MaterialTyp.KIES, MaterialTyp.STAHL): (0.2, "DIN EN 13814:2005-06"),
        (MaterialTyp.LEHM, MaterialTyp.STAHL): (0.2, "DIN EN 13814:2005-06"),
        (MaterialTyp.SAND, MaterialTyp.STAHL): (0.2, "DIN EN 13814:2005-06"),
        (MaterialTyp.STAHL, MaterialTyp.STAHL): (0.15, "DIN EN 13814:2005-06"),
        (MaterialTyp.TON, MaterialTyp.STAHL): (0.2, "DIN EN 13814:2005-06"),
    },
}