# rechenfunktionen/sicherheitsbeiwert.py
from __future__ import annotations
from typing import Dict, Callable
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, Lasttyp, Variabilitaet
from datenstruktur.kraefte import Kraefte

# TODO: Umgang mit Reibung (Reibung auf Boden -> Gewicht / Reibung durch Wind -> Wind)

def _validate_inputs(norm: Norm, kraft: Kraefte, ist_guenstig: bool) -> None:
    if not isinstance(norm, Norm):
        raise TypeError("norm muss vom Typ Norm sein.")
    if not isinstance(ist_guenstig, bool):
        raise TypeError("ist_guenstig muss bool sein.")
    if not hasattr(kraft, "typ") or not hasattr(kraft, "variabilitaet"):
        raise TypeError("kraft muss Felder 'typ' und 'variabilitaet' besitzen.")

def _beiwert_default(kraft: Kraefte, ist_guenstig: bool) -> Zwischenergebnis:
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
            raise NotImplementedError(f"Unbekannter Lasttyp: {kraft.typ}")

    return Zwischenergebnis(
        wert=gamma,
        formel=formel,
        quelle_formel="DIN EN 17879:2024-08 / DIN EN 13814:2005-06",
        formelzeichen=["γ"],
        quelle_formelzeichen=["---"]
    )

# Norm-Dispatch (derzeit alle Normen → default)
_DISPATCH: Dict[Norm, Callable[[Kraefte, bool], Zwischenergebnis]] = {
    Norm.DEFAULT: _beiwert_default,
}

def sicherheitsbeiwert(norm: Norm, kraft: Kraefte, ist_guenstig: bool) -> Zwischenergebnis:

    _validate_inputs(norm, kraft, ist_guenstig)
    fn = _DISPATCH.get(norm, _beiwert_default)
    return fn(kraft, ist_guenstig)
