from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, Union, Callable, TYPE_CHECKING, runtime_checkable

from windlast_CORE.datenstruktur.enums import Severity, ProtokollModus

if TYPE_CHECKING:
    from windlast_CORE.rechenfunktionen.geom3d import Vec3
else:
    Vec3 = Tuple[float, float, float]


WertTyp = Union[float, int, str, Sequence[float], Vec3, None]
Meta = Dict[str, Any]


# =========================
# Datenmodell
# =========================

@dataclass
class Ergebnis:
    name: str
    wert: WertTyp

    label: Optional[str] = None
    formelzeichen: Optional[Union[str, Sequence[str]]] = None
    formel: Optional[str] = None
    einheit: Optional[str] = None
    priority: int = 0

    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Strukturierte Meldung im Ergebnisbaum."""
    code: str
    severity: Severity
    text: str
    meta: Meta = field(default_factory=dict)


@dataclass
class Ebene:
    """Eine Hierarchie-Dimension, z. B. nachweis, windrichtung_deg, element_id."""
    name: str

    label: Optional[str] = None
    gruppen: List[Gruppe] = field(default_factory=list)
    meta: Meta = field(default_factory=dict)


@dataclass
class Gruppe:
    """Ein konkreter Wert innerhalb einer Ebene, z. B. KIPP, 90°, Traverse_1."""
    name: str

    label: Optional[str] = None
    winner: Optional[bool] = None
    ergebnisse: List[Ergebnis] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    ebenen: List[Ebene] = field(default_factory=list)
    meta: Meta = field(default_factory=dict)


@dataclass
class ErgebnisBaum:
    """Root-Objekt des Protokolls."""
    ebenen: List[Ebene] = field(default_factory=list)
    ergebnisse: List[Ergebnis] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    meta: Meta = field(default_factory=dict)


@dataclass(frozen=True)
class BreadcrumbStep:
    """
    Ein Breadcrumb-Schritt: gehe in Ebene `ebene` und dort in Gruppe `gruppe`.
    Labels/Meta können Ebene und Gruppe beim ersten Anlegen beschriften.
    """
    ebene: str
    gruppe: str

    ebene_label: Optional[str] = None
    gruppe_label: Optional[str] = None
    ebene_meta: Optional[Meta] = None
    gruppe_meta: Optional[Meta] = None


Breadcrumb = List[BreadcrumbStep]


# =========================
# Protokoll-Schnittstelle
# =========================

class Protokoll:
    """Baumbasierte Protokoll-Implementierung."""
    def __init__(self, *, meta: Optional[Meta] = None, modus: ProtokollModus = ProtokollModus.STANDARD) -> None:
        self.root = ErgebnisBaum(meta=dict(meta or {}))
        self.modus = modus

    def add_ergebnis(self, *, breadcrumb: Optional[Breadcrumb], ergebnis: Ergebnis) -> None:
        if self.modus == ProtokollModus.STANDARD:
            gruppe = get_or_create_gruppe(self.root, breadcrumb)
            if gruppe is None:
                self.root.ergebnisse.append(ergebnis)
            else:
                gruppe.ergebnisse.append(ergebnis)
        else:
            return

    def add_message(self, *, breadcrumb: Optional[Breadcrumb], message: Message) -> None:
        if self.modus == ProtokollModus.STANDARD:
            gruppe = get_or_create_gruppe(self.root, breadcrumb)
            if gruppe is None:
                self.root.messages.append(message)
            else:
                gruppe.messages.append(message)
        else:
            return

    def set_winner(self, *, breadcrumb: Breadcrumb) -> None:
        if self.modus == ProtokollModus.STANDARD:
            set_winner(self.root, breadcrumb)
        else:
            return


def make_protokoll(*, modus: ProtokollModus = ProtokollModus.STANDARD, meta: Optional[Meta] = None) -> Protokoll:
    return Protokoll(meta=meta, modus=modus)


# =========================
# Breadcrumb-Helfer
# =========================

def bc_step(
    ebene: str,
    gruppe: Any,
    *,
    ebene_label: Optional[str] = None,
    gruppe_label: Optional[str] = None,
    ebene_meta: Optional[Meta] = None,
    gruppe_meta: Optional[Meta] = None,
) -> BreadcrumbStep:
    """Convenience-Builder für einen BreadcrumbStep."""
    return BreadcrumbStep(
        ebene=str(ebene),
        gruppe=str(gruppe),
        ebene_label=ebene_label,
        gruppe_label=gruppe_label,
        ebene_meta=dict(ebene_meta or {}) or None,
        gruppe_meta=dict(gruppe_meta or {}) or None,
    )


def merge_breadcrumb(basis: Optional[Sequence[BreadcrumbStep]], extra: Optional[Sequence[BreadcrumbStep]]) -> Breadcrumb:
    """Nicht-destruktives Zusammenhängen zweier Breadcrumbs."""
    return list(basis or []) + list(extra or [])


def breadcrumb_from_pairs(*pairs: Tuple[str, Any]) -> Breadcrumb:
    """Kurzform: breadcrumb_from_pairs(("nachweis", "KIPP"), ("windrichtung_deg", "90°"))"""
    return [bc_step(ebene, gruppe) for ebene, gruppe in pairs]


# =========================
# Tree-Navigation
# =========================

def _find_ebene(ebenen: List[Ebene], name: str) -> Optional[Ebene]:
    for ebene in ebenen:
        if ebene.name == name:
            return ebene
    return None


def _find_gruppe(gruppen: List[Gruppe], name: str) -> Optional[Gruppe]:
    for gruppe in gruppen:
        if gruppe.name == name:
            return gruppe
    return None


def _get_or_create_ebene(ebenen: List[Ebene], step: BreadcrumbStep) -> Ebene:
    ebene = _find_ebene(ebenen, step.ebene)
    if ebene is None:
        ebene = Ebene(
            name=step.ebene,
            label=step.ebene_label,
            meta=dict(step.ebene_meta or {}),
        )
        ebenen.append(ebene)
    else:
        if ebene.label is None and step.ebene_label is not None:
            ebene.label = step.ebene_label
        if step.ebene_meta:
            ebene.meta.update(step.ebene_meta)
    return ebene


def _get_or_create_gruppe(gruppen: List[Gruppe], step: BreadcrumbStep) -> Gruppe:
    gruppe = _find_gruppe(gruppen, step.gruppe)
    if gruppe is None:
        gruppe = Gruppe(
            name=step.gruppe,
            label=step.gruppe_label,
            meta=dict(step.gruppe_meta or {}),
        )
        gruppen.append(gruppe)
    else:
        if gruppe.label is None and step.gruppe_label is not None:
            gruppe.label = step.gruppe_label
        if step.gruppe_meta:
            gruppe.meta.update(step.gruppe_meta)
    return gruppe


def get_or_create_gruppe(root: ErgebnisBaum, breadcrumb: Optional[Sequence[BreadcrumbStep]]) -> Optional[Gruppe]:
    """
    Legt den Breadcrumb-Pfad an und gibt die letzte Gruppe zurück.
    Bei leerem Breadcrumb wird None zurückgegeben; Ergebnisse/Messages hängen dann direkt am Root.
    """
    if not breadcrumb:
        return None

    current_ebenen = root.ebenen
    current_gruppe: Optional[Gruppe] = None

    for step in breadcrumb:
        ebene = _get_or_create_ebene(current_ebenen, step)
        current_gruppe = _get_or_create_gruppe(ebene.gruppen, step)
        current_ebenen = current_gruppe.ebenen

    return current_gruppe


def find_gruppe(root: ErgebnisBaum, breadcrumb: Sequence[BreadcrumbStep]) -> Optional[Gruppe]:
    """Findet eine Gruppe ohne neue Knoten anzulegen."""
    if not breadcrumb:
        return None

    current_ebenen = root.ebenen
    current_gruppe: Optional[Gruppe] = None

    for step in breadcrumb:
        ebene = _find_ebene(current_ebenen, step.ebene)
        if ebene is None:
            return None
        current_gruppe = _find_gruppe(ebene.gruppen, step.gruppe)
        if current_gruppe is None:
            return None
        current_ebenen = current_gruppe.ebenen

    return current_gruppe


def find_ebene_for_last_step(root: ErgebnisBaum, breadcrumb: Sequence[BreadcrumbStep]) -> Optional[Ebene]:
    """Findet die Ebene, in der die letzte Breadcrumb-Gruppe liegt."""
    if not breadcrumb:
        return None

    parent_steps = list(breadcrumb[:-1])
    last_step = breadcrumb[-1]

    if parent_steps:
        parent_group = find_gruppe(root, parent_steps)
        if parent_group is None:
            return None
        return _find_ebene(parent_group.ebenen, last_step.ebene)

    return _find_ebene(root.ebenen, last_step.ebene)


# =========================
# Protokollier-Funktionen
# =========================

def protokolliere_ergebnis(
    protokoll: Optional[Protokoll],
    *,
    breadcrumb: Optional[Sequence[BreadcrumbStep]] = None,
    name: str,
    wert: WertTyp,
    label: Optional[str] = None,
    formelzeichen: Optional[Union[str, Sequence[str]]] = None,
    formel: Optional[str] = None,
    einheit: Optional[str] = None,
    priority: int = 0,
    meta: Optional[Meta] = None,
) -> None:
    """Sicheres Protokollieren eines Ergebnisses in den Baum."""
    if protokoll is None:
        return

    protokoll.add_ergebnis(
        breadcrumb=list(breadcrumb or []),
        ergebnis=Ergebnis(
            name=name,
            label=label,
            formelzeichen=formelzeichen,
            formel=formel,
            wert=wert,
            einheit=einheit,
            priority=priority,
            meta=dict(meta or {}),
        ),
    )


def protokolliere_msg(
    protokoll: Optional[Protokoll],
    *,
    severity: Severity,
    code: str,
    text: str,
    breadcrumb: Optional[Sequence[BreadcrumbStep]] = None,
    meta: Optional[Meta] = None,
) -> None:
    """Sicheres Protokollieren einer Message in den Baum."""
    if protokoll is None:
        return

    protokoll.add_message(
        breadcrumb=list(breadcrumb or []),
        message=Message(
            code=code,
            severity=severity,
            text=str(text),
            meta=dict(meta or {}),
        ),
    )


def set_winner(root_or_protokoll: Union[ErgebnisBaum, Protokoll], breadcrumb: Sequence[BreadcrumbStep]) -> None:
    """
    Setzt innerhalb der Ebene des letzten Breadcrumb-Schritts genau diese Gruppe als Gewinner.
    Alle Geschwistergruppen derselben Ebene bekommen winner=False.
    """
    root = getattr(root_or_protokoll, "root", root_or_protokoll)
    if not isinstance(root, ErgebnisBaum):
        return

    ebene = find_ebene_for_last_step(root, breadcrumb)
    if ebene is None:
        # Pfad bei Bedarf anlegen und dann erneut suchen.
        get_or_create_gruppe(root, breadcrumb)
        ebene = find_ebene_for_last_step(root, breadcrumb)
        if ebene is None:
            return

    target_name = breadcrumb[-1].gruppe
    for gruppe in ebene.gruppen:
        gruppe.winner = (gruppe.name == target_name)


# =========================
# Optionale Sammler / Kompatibilität
# =========================

def collect_tree(protokoll: Optional[Protokoll]) -> Optional[ErgebnisBaum]:
    return getattr(protokoll, "root", None) if protokoll is not None else None


@dataclass(frozen=True)
class Zwischenergebnis:
    """Schlanker Rückgabewert für bestehende Rechenfunktionen."""
    wert: float


@dataclass(frozen=True)
class Zwischenergebnis_Liste:
    """Schlanker Rückgabewert für bestehende Rechenfunktionen."""
    wert: Sequence[float]


@dataclass(frozen=True)
class Zwischenergebnis_Vektor:
    """Schlanker Rückgabewert für bestehende Rechenfunktionen."""
    wert: Vec3
