# reibwert.py
from __future__ import annotations

from typing import List, Optional, Sequence, Dict, Tuple

from windlast_CORE.datenstruktur.enums import MaterialTyp, Norm, Severity
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.materialdaten.catalog import catalog

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
    # Gummi existiert in 13814 nicht → nur Paarungen ohne Gummi
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


def _pair(a: MaterialTyp, b: MaterialTyp) -> tuple[MaterialTyp, MaterialTyp]:
    # Sortiert nach Enum-Wert, so ist (A,B) == (B,A)
    return (a, b) if a.value <= b.value else (b, a)

REIBWERT_PRIORITAET: tuple[Norm, ...] = (Norm.DIN_EN_13814_2005_06, Norm.DIN_EN_17879_2024_08)

def get_reibwert(a: MaterialTyp, b: MaterialTyp, norm: Norm,
           prioritaet: tuple[Norm, ...] = REIBWERT_PRIORITAET) -> tuple[float, str, Norm]:
    key = _pair(a, b)
    # 1) Angefragte Norm
    pool = DATA_REIBWERTE.get(norm, {})
    if key in pool:
        mu, quelle = pool[key]
        return mu, quelle, norm
    # 2) Fallback entlang Priorität
    for n in prioritaet:
        pool = DATA_REIBWERTE.get(n, {})
        if key in pool:
            mu, quelle = pool[key]
            return mu, quelle, n
    raise KeyError(f"Kein Reibwert für Paarung {a}–{b} in den bekannten Normen vorhanden.")

def reibwert(
    norm: Norm,
    materialfolge: Sequence[Optional[MaterialTyp]],
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "reibwert",
        "norm": getattr(norm, "name", str(norm)),
    })

    # 1) None rausfiltern
    cleaned: List[MaterialTyp] = [m for m in materialfolge if m is not None]
    if len(cleaned) < 2:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="REIB/INPUT_INVALID",
            text="Es werden mindestens zwei reale Materialien benötigt.",
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Effektiver Reibwert μ_eff", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))

    # 2) Reibwerte Quellen ermitteln
    einzelwerte: List[float] = []
    quelle_einzelwerte: List[str] = []
    norm_einzelwerte: List[Norm] = []

    try:
        for i in range(len(cleaned) - 1):
            a, b = cleaned[i], cleaned[i + 1]

            mu, quelle, used_norm = get_reibwert(a, b, norm)
            einzelwerte.append(mu)
            quelle_einzelwerte.append(quelle)
            norm_einzelwerte.append(used_norm)

            if used_norm != norm:
                    protokolliere_msg(
                        protokoll,
                        severity=Severity.HINT,
                        code="REIB/FALLBACK_NORM",
                        text=f"Für Paarung {a.name}–{b.name} wurde auf {used_norm.name} zurückgegriffen.",
                        kontext=merge_kontext(base_ctx, {"paarung": (a.name, b.name), "norm_used": used_norm.name}),
                    )
    except KeyError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="REIB/PAIR_UNKNOWN",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Effektiver Reibwert μ_eff", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))

    # 3) effektiver Reibwert ist das Minimum
    reibwert_eff = min(einzelwerte)
    idx_min = einzelwerte.index(reibwert_eff)
    # maßgebende Übergangspaarung (nur Hinweis)
    a_gov = cleaned[idx_min]
    b_gov = cleaned[idx_min + 1]
    protokolliere_msg(
        protokoll,
        severity=Severity.HINT,
        code="REIB/PAIR_GOVERNING",
        text=f"Maßgebend ist die Paarung {a_gov.name}–{b_gov.name} mit μ={reibwert_eff:.3f}.",
        kontext=merge_kontext(base_ctx, {"paarung": (a_gov.name, b_gov.name)}),
    )

    # 4) in Zwischenergebnis schreiben
    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(
            titel="Effektiver Reibwert μ_eff",
            wert=reibwert_eff,
            formel="μ_eff = min(μ_i)",
            quelle_formel="Konservatives Verfahren: kleinster Reibwert maßgebend.",
            einzelwerte=einzelwerte,
            quelle_einzelwerte=quelle_einzelwerte,
        ),
        kontext=base_ctx,
    )

    return Zwischenergebnis(wert=reibwert_eff)
