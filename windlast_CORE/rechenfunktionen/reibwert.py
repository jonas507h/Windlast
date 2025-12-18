# reibwert.py
from __future__ import annotations

from typing import List, Optional, Sequence, Dict, Tuple, Iterable, Set

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
from windlast_CORE.materialdaten.reibwert_data import DATA_REIBWERTE

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
    raise KeyError(f"Kein Reibwert für Paarung {a.value}–{b.value} in den bekannten Normen vorhanden.")

def reibwert(
    norm: Norm,
    materialfolge: Sequence[Optional[MaterialTyp]],
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "Reibwert",
        "norm": getattr(norm, "value", str(norm)),
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
            bundle=make_docbundle(titel="Effektiver Reibwert μ_eff", wert=None),
            kontext=merge_kontext(base_ctx, {"None": True}),
        )
        return Zwischenergebnis(wert=None)

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
                        text=f"Für Paarung {a.value}–{b.value} wurde auf {used_norm.value} zurückgegriffen.",
                        kontext=merge_kontext(base_ctx, {"paarung": (a.value, b.value), "norm_used": used_norm.value}),
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
            bundle=make_docbundle(titel="Effektiver Reibwert μ_eff", wert=None),
            kontext=merge_kontext(base_ctx, {"None": True}),
        )
        return Zwischenergebnis(wert=None)

    # 3) effektiver Reibwert ist das Minimum
    reibwert_eff = min(einzelwerte)
    idx_min = einzelwerte.index(reibwert_eff)
    # maßgebende Übergangspaarung (nur Hinweis)
    a_gov = cleaned[idx_min]
    b_gov = cleaned[idx_min + 1]
    protokolliere_msg(
        protokoll,
        severity=Severity.INFO,
        code="REIB/PAIR_GOVERNING",
        text=f"Maßgebend ist die Paarung {a_gov.value}–{b_gov.value} mit μ={reibwert_eff:.3f}.",
        kontext=merge_kontext(base_ctx, {"paarung": (a_gov.value, b_gov.value)}),
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

# --- Helper-Funktionen für externe Abfragen ---

def _norm_chain(norm: Norm, prioritaet: tuple[Norm, ...] = REIBWERT_PRIORITAET) -> tuple[Norm, ...]:
    # angefragte Norm zuerst, dann Priorität ohne Duplikate
    out = [norm]
    for n in prioritaet:
        if n != norm:
            out.append(n)
    return tuple(out)

def pair_supported(
    a: MaterialTyp,
    b: MaterialTyp,
    norm: Norm,
    *,
    prioritaet: tuple[Norm, ...] = REIBWERT_PRIORITAET,
) -> bool:
    try:
        get_reibwert(a, b, norm, prioritaet=prioritaet)
        return True
    except KeyError:
        return False

def supported_partners(
    a: MaterialTyp,
    norm: Norm,
    *,
    prioritaet: tuple[Norm, ...] = REIBWERT_PRIORITAET,
) -> Set[MaterialTyp]:
    """
    Liefert alle Materialien b, für die (a,b) unter norm + Fallback-Priorität existiert.
    """
    partners: Set[MaterialTyp] = set()
    for n in _norm_chain(norm, prioritaet):
        pool = DATA_REIBWERTE.get(n, {})
        for (m1, m2) in pool.keys():
            if m1 == a:
                partners.add(m2)
            elif m2 == a:
                partners.add(m1)
    return partners

def materialfolge_supported(
    norm: Norm,
    materialfolge: Sequence[Optional[MaterialTyp]],
    *,
    prioritaet: tuple[Norm, ...] = REIBWERT_PRIORITAET,
) -> bool:
    cleaned = [m for m in materialfolge if m is not None]
    if len(cleaned) < 2:
        return False
    for i in range(len(cleaned) - 1):
        if not pair_supported(cleaned[i], cleaned[i+1], norm, prioritaet=prioritaet):
            return False
    return True