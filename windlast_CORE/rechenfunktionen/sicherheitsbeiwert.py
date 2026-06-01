# rechenfunktionen/sicherheitsbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional

from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
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

def _sicherheitsbeiwert_default(
    kraft: Kraefte,
    ist_guenstig: bool,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "sicherheitsbeiwert_default"
    }

    gamma: Optional[float] = None
    titel: str = f"Sicherheitsbeiwert ({kraft.typ.value}) γ_{'G' if kraft.typ == Lasttyp.GEWICHT else 'W' if kraft.typ == Lasttyp.WIND else 'R' if kraft.typ == Lasttyp.REIBUNG else ''}"

    if ist_guenstig:
        if kraft.typ == Lasttyp.GEWICHT and kraft.variabilitaet == Variabilitaet.STAENDIG:
            # Eigenlast günstig & ständig
            gamma = 1.0
        else:
            # alle anderen günstigen Lasten
            gamma = 0.0

    else:
        if kraft.typ == Lasttyp.WIND:
            # Wind ungünstig
            gamma = 1.2
        elif kraft.typ == Lasttyp.GEWICHT:
            # Eigenlast ungünstig
            gamma = 1.1
        elif kraft.typ == Lasttyp.REIBUNG:
            # Reibung ungünstig
            gamma = 1.3
        else:
            protokolliere_msg(
                protokoll, severity=Severity.ERROR, code="SICHB/UNKNOWN_LASTTYP",
                text=f"Unbekannter Lasttyp: {kraft.typ}",
                breadcrumb=base_bc,
            )
            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="sicherheitsbeiwert",
                wert=float("nan"),
                label="math.sicherheitsbeiwert.label",
                formelzeichen="math.sicherheitsbeiwert.symbol",
                priority=10,
                meta=base_meta,
            )
            return Zwischenergebnis(wert=float("nan"))
        
    protokolliere_ergebnis(
        protokoll,
        breadcrumb=base_bc,
        name="sicherheitsbeiwert",
        wert=gamma,
        label="math.sicherheitsbeiwert.label",
        formelzeichen="math.sicherheitsbeiwert.symbol",
        priority=10,
        meta=base_meta,
    )
    return Zwischenergebnis(wert=gamma)

# Norm-Dispatch (derzeit alle Normen → default)
_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _sicherheitsbeiwert_default,
}

def sicherheitsbeiwert(
    norm: Norm,
    kraft: Kraefte,
    ist_guenstig: bool,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "sicherheitsbeiwert",
    }

    try:
        _validate_inputs(norm, kraft, ist_guenstig)
    except (TypeError, ValueError) as e:
        protokolliere_msg(
            protokoll, severity=Severity.ERROR, code="SICHB/INPUT_INVALID",
            text=str(e), breadcrumb=base_bc, meta=base_meta,
        )
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="sicherheitsbeiwert",
            wert=float("nan"),
            label="math.sicherheitsbeiwert.label",
            formelzeichen="math.sicherheitsbeiwert.symbol",
            priority=10,
            meta=base_meta,
        )
        return Zwischenergebnis(wert=float("nan"))

    fn = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return fn(kraft, ist_guenstig, protokoll=protokoll, breadcrumb=base_bc)