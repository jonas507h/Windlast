# rechenfunktionen/sicherheitsbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional

from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.datenstruktur.enums import Norm, Lasttyp, Variabilitaet, Severity
from windlast_CORE.datenstruktur.kraefte import Kraefte

# TODO: Umgang mit Reibung (Reibung auf Boden -> Gewicht / Reibung durch Wind -> Wind)

def _validate_inputs(norm: Norm, kraft: Kraefte, ist_guenstig: bool) -> None:
    if not isinstance(norm, Norm):
        raise TypeError("norm muss vom Typ Norm sein.")
    if not isinstance(ist_guenstig, bool):
        raise TypeError("ist_guenstig muss bool sein.")
    if not hasattr(kraft, "typ") or not hasattr(kraft, "variabilitaet"):
        raise TypeError("kraft muss Felder 'typ' und 'variabilitaet' besitzen.")

def _beiwert_default(
    kraft: Kraefte,
    ist_guenstig: bool,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Sicherheitsbeiwert",
        "lasttyp": getattr(kraft.typ, "value", str(getattr(kraft, "typ", None))),
        "variabilitaet": getattr(kraft.variabilitaet, "value", str(getattr(kraft, "variabilitaet", None))),
        "ist_guenstig": ist_guenstig,
    })

    gamma: Optional[float] = None
    formel: str = ""
    titel: str = f"Sicherheitsbeiwert ({kraft.typ.value}) γ_{'G' if kraft.typ == Lasttyp.GEWICHT else 'W' if kraft.typ == Lasttyp.WIND else 'R' if kraft.typ == Lasttyp.REIBUNG else ''}"

    if ist_guenstig:
        if kraft.typ == Lasttyp.GEWICHT and kraft.variabilitaet == Variabilitaet.STAENDIG:
            # Eigenlast günstig & ständig
            gamma = 1.0
            formel = "γ_G = 1.0 (günstig, ständig)"
        else:
            # alle anderen günstigen Lasten
            gamma = 0.0
            formel = "γ = 0.0 (günstige variable oder nicht zulässige Gutschrift)"

    else:
        if kraft.typ == Lasttyp.WIND:
            # Wind ungünstig
            gamma = 1.2
            formel = "γ_wind = 1.2 (ungünstig)"
        elif kraft.typ == Lasttyp.GEWICHT:
            # Eigenlast ungünstig
            gamma = 1.1
            formel = "γ_G = 1.1 (ungünstig)"
        elif kraft.typ == Lasttyp.REIBUNG:
            # Reibung ungünstig
            gamma = 1.3
            formel = "γ_R = 1.3 (ungünstig; sonstige Lastanteile)"
        else:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="SICHB/UNKNOWN_LASTTYP",
                text=f"Unbekannter Lasttyp: {kraft.typ}",
                kontext=base_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel=titel, wert=float("nan")),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(
            titel=titel,
            wert=gamma,
            formel=formel,
            quelle_formel="DIN EN 17879:2024-08 / DIN EN 13814:2005-06",
            formelzeichen=["γ"],
            quelle_formelzeichen=["---"],
        ),
        kontext=base_ctx,
    )
    return Zwischenergebnis(wert=gamma)

# Norm-Dispatch (derzeit alle Normen → default)
_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _beiwert_default,
}

def sicherheitsbeiwert(
    norm: Norm,
    kraft: Kraefte,
    ist_guenstig: bool,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    base_ctx = merge_kontext(kontext, {
        "funktion": "Sicherheitsbeiwert",
        "norm": getattr(norm, "value", str(norm)),
        "lasttyp": getattr(kraft.typ, "value", str(getattr(kraft, "typ", None))),
        "variabilitaet": getattr(kraft.variabilitaet, "value", str(getattr(kraft, "variabilitaet", None))),
        "ist_guenstig": ist_guenstig,
    })

    try:
        _validate_inputs(norm, kraft, ist_guenstig)
    except (TypeError, ValueError) as e:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="SICHB/INPUT_INVALID",
            text=str(e), kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Sicherheitsbeiwert γ", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))

    fn = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return fn(kraft, ist_guenstig, protokoll=protokoll, kontext=base_ctx)