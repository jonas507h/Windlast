from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence, Mapping, Any, Protocol, runtime_checkable, Dict, List, Tuple, Union
from rechenfunktionen.geom3d import Vec3  # (x,y,z)
from datenstruktur.enums import Severity

# ========= Protokoll-Schnittstelle =========

@runtime_checkable
class Protokoll(Protocol):
    """
    Minimale Schnittstelle für unseren durchgängigen Log/Trace.
    Implementationen liefern add_message(...) und add_doc(...).
    """
    def add_message(
        self,
        *,
        severity: Severity,
        code: str,           # stabiler, maschinenlesbarer Code
        text: str,           # kurzer, UI/PDF-freundlicher Text
        kontext: Optional[dict] = None,
    ) -> None: ...
    def add_doc(
        self,
        *,
        bundle: Mapping[str, Any],     # DocBundle (siehe unten)
        kontext: Optional[dict] = None,
    ) -> None: ...


# ========= Kontext-/Doc-Helfer =========

def merge_kontext(basis: Optional[dict], extra: Optional[dict]) -> dict:
    """Nicht-destruktives Merge zweier Kontext-Maps."""
    out = dict(basis or {})
    if extra:
        out.update({k: v for k, v in extra.items() if v is not None})
    return out

def make_docbundle(
    *,
    titel: str,
    wert: Union[float, Sequence[float], Vec3, None],
    formel: Optional[str] = None,
    quelle_formel: Optional[str] = None,
    formelzeichen: Optional[Sequence[str]] = None,
    quelle_formelzeichen: Optional[Sequence[str]] = None,
    einzelwerte: Optional[Sequence[Union[float, int, str, Tuple[Any, ...]]]] = None,
    quelle_einzelwerte: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Erzeugt ein leichtgewichtiges Dokumentationspaket (DocBundle),
    das über Protokoll.add_doc(...) mit-transportiert wird.
    """
    return {
        "titel": titel,
        "wert": wert,
        "formel": formel,
        "quelle_formel": quelle_formel,
        "formelzeichen": list(formelzeichen) if formelzeichen is not None else None,
        "quelle_formelzeichen": list(quelle_formelzeichen) if quelle_formelzeichen is not None else None,
        "einzelwerte": list(einzelwerte) if einzelwerte is not None else None,
        "quelle_einzelwerte": list(quelle_einzelwerte) if quelle_einzelwerte is not None else None,
    }

def protokolliere_msg(
    protokoll: Optional[Protokoll],
    *,
    severity: Severity,
    code: str,
    text: str,
    kontext: Optional[dict] = None,
) -> None:
    """Sicheres Logging einer Message (no-op, wenn kein Protokoll übergeben wurde)."""
    if protokoll is not None:
        protokoll.add_message(severity=severity, code=code, text=text, kontext=kontext)

def protokolliere_doc(
    protokoll: Optional[Protokoll],
    *,
    bundle: Mapping[str, Any],
    kontext: Optional[dict] = None,
) -> None:
    """Sicheres Anhängen eines DocBundles (no-op, wenn kein Protokoll übergeben wurde)."""
    if protokoll is not None:
        protokoll.add_doc(bundle=bundle, kontext=kontext)


# ========= Verschlankte Ergebnis-Typen =========
# Ab jetzt tragen die Hilfsfunktionen die Dokumentationsinfos (Formeln/Quellen/Einzelwerte)
# NICHT mehr im Ergebnisobjekt, sondern ausschließlich via Protokoll.add_doc(...).

@dataclass(frozen=True)
class Zwischenergebnis:
    """Allgemeiner Zwischenwert (nur der numerische Wert)."""
    wert: float

@dataclass(frozen=True)
class Zwischenergebnis_Liste:
    """Zwischenwerte als Liste/Vektor 1D (nur Werte)."""
    wert: Sequence[float]

@dataclass(frozen=True)
class Zwischenergebnis_Vektor:
    """Zwischenwert als 3D-Vektor (nur Werte)."""
    wert: Vec3
