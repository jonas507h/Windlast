# rechenfunktionen/sicherheitsbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional

from datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from datenstruktur.enums import Norm, Lasttyp, Variabilitaet, Severity
from datenstruktur.kraefte import Kraefte

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
        "funktion": "sicherheitsbeiwert",
        "lasttyp": getattr(kraft.typ, "name", str(getattr(kraft, "typ", None))),
        "variabilitaet": getattr(kraft.variabilitaet, "name", str(getattr(kraft, "variabilitaet", None))),
        "ist_guenstig": ist_guenstig,
    })

    gamma: Optional[float] = None
    formel: str = ""

    if ist_guenstig:
        if kraft.typ == Lasttyp.GEWICHT and kraft.variabilitaet == Variabilitaet.STAENDIG:
            # Eigenlast günstig & ständig
            gamma = 1.0
            formel = "γ_G = 1.0 (günstig, ständig)"
            protokolliere_msg(protokoll, severity=Severity.HINT, code="SICHB/CASE",
                              text="Günstig: ständige Eigenlast wird mit γ=1.0 angesetzt.",
                              kontext=base_ctx)
        else:
            # alle anderen günstigen Lasten
            gamma = 0.0
            formel = "γ = 0.0 (günstige variable oder nicht zulässige Gutschrift)"
            protokolliere_msg(protokoll, severity=Severity.HINT, code="SICHB/CASE",
                              text="Günstig: variable/sonstige Lasten werden mit γ=0.0 angesetzt.",
                              kontext=base_ctx)
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
                bundle=make_docbundle(titel="Sicherheitsbeiwert γ", wert=float("nan")),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

    protokolliere_doc(
        protokoll,
        bundle=make_docbundle(
            titel="Sicherheitsbeiwert γ",
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
        "funktion": "sicherheitsbeiwert",
        "norm": getattr(norm, "name", str(norm)),
        "lasttyp": getattr(kraft.typ, "name", str(getattr(kraft, "typ", None))),
        "variabilitaet": getattr(kraft.variabilitaet, "name", str(getattr(kraft, "variabilitaet", None))),
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