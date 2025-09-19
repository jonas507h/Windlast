# datenstruktur/konstanten.py
from dataclasses import dataclass, replace
import contextlib, contextvars
from typing import Optional

# Toleranzen

_EPS = 1e-9

# Physik Konstanten

@dataclass(frozen=True)
class PhysikKonstanten:
    luftdichte: float = 1.25        # kg/m^3
    zaehigkeit_kin: float = 15.32e-6  # m^2/s
    erdbeschleunigung: float = 9.80665              # m/s^2

__konst_var = contextvars.ContextVar("physik_konstanten", default=PhysikKonstanten())

def aktuelle_konstanten() -> PhysikKonstanten:
    return __konst_var.get()

def setze_konstanten(konst: PhysikKonstanten) -> PhysikKonstanten:
    __konst_var.set(konst)
    return konst

def aktualisiere_konstanten(
    *, luftdichte: Optional[float] = None,
    zaehigkeit_kin: Optional[float] = None,
    erdbeschleunigung: Optional[float] = None,
) -> PhysikKonstanten:
    curr = __konst_var.get()
    new = curr
    if luftdichte is not None:
        new = replace(new, luftdichte=luftdichte)
    if zaehigkeit_kin is not None:
        new = replace(new, zaehigkeit_kin=zaehigkeit_kin)
    if erdbeschleunigung is not None:
        new = replace(new, erdbeschleunigung=erdbeschleunigung)
    __konst_var.set(new)
    return new

@contextlib.contextmanager
def mit_konstanten(
    konst: Optional[PhysikKonstanten] = None,
    *, luftdichte: Optional[float] = None,
    zaehigkeit_kin: Optional[float] = None,
    erdbeschleunigung: Optional[float] = None,
):
    """Temporäre Overrides: entweder komplette Dataclass ODER einzelne Felder."""
    base = konst or __konst_var.get()
    temp = base
    if luftdichte is not None:
        temp = replace(temp, luftdichte=luftdichte)
    if zaehigkeit_kin is not None:
        temp = replace(temp, zaehigkeit_kin=zaehigkeit_kin)
    if erdbeschleunigung is not None:
        temp = replace(temp, erdbeschleunigung=erdbeschleunigung)
    token = __konst_var.set(temp)
    try:
        yield temp
    finally:
        __konst_var.reset(token)
