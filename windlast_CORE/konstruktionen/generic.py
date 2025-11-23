from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Dict, Any

from windlast_CORE.bauelemente import Bodenplatte, Traversenstrecke, Rohr
from windlast_CORE.rechenfunktionen import (
    gesamtgewicht as _gesamtgewicht,
)
from windlast_CORE.rechenfunktionen.kippsicherheit import kippsicherheit as _kippsicherheit
from windlast_CORE.rechenfunktionen.gleitsicherheit import gleitsicherheit as _gleitsicherheit
from windlast_CORE.rechenfunktionen.abhebesicherheit import abhebesicherheit as _abhebesicherheit
from windlast_CORE.datenstruktur.enums import (
    Norm,
    MaterialTyp,
    FormTyp,
    RechenmethodeKippen,
    RechenmethodeGleiten,
    RechenmethodeAbheben,
    VereinfachungKonstruktion,
)
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis, Protokoll, merge_kontext

def _parse_material(value, default: "MaterialTyp | None" = None):
    """
    Akzeptiert sowohl Enum-Namen ("STAHL") als auch Values ("Stahl") und gibt einen MaterialTyp zurück.
    """
    from windlast_CORE.datenstruktur.enums import MaterialTyp  # oder dein tatsächlicher Pfad

    if value is None:
        return default
    if isinstance(value, MaterialTyp):
        return value

    # zuerst als Enum-Name probieren: MaterialTyp["STAHL"]
    try:
        return MaterialTyp[value]
    except Exception:
        pass

    # dann als Value probieren: MaterialTyp("Stahl")
    try:
        return MaterialTyp(value)
    except Exception:
        if default is not None:
            return default
        raise

def _build_bauelement(el: Dict[str, Any]) -> object:
    typ = el.get("typ")

    if typ == "Traversenstrecke":
        return Traversenstrecke(
            traverse_name_intern=el["traverse_name_intern"],
            start=tuple(el["start"]),
            ende=tuple(el["ende"]),
            orientierung=tuple(el["orientierung"]),
            element_id_intern=el.get("element_id_intern"),
            anzeigename=el.get("anzeigename"),
        )

    if typ == "Bodenplatte":
        untergrund = _parse_material(el.get("untergrund"), default=MaterialTyp.BETON)
        gummimatte = _parse_material(el.get("gummimatte")) if el.get("gummimatte") else None

        return Bodenplatte(
            name_intern=el["name_intern"],
            mittelpunkt=tuple(el["mittelpunkt"]),
            orientierung=tuple(el["orientierung"]),
            drehung=tuple(el["drehung"]),
            untergrund=untergrund,
            gummimatte=gummimatte,
            element_id_intern=el.get("element_id_intern"),
        )

    if typ == "Rohr":
        # Falls dein Rohr-Bauelement anders heißt / andere Parameter hat → hier anpassen.
        from windlast_CORE.bauelemente import Rohr  # optionaler Inline-Import
        return Rohr(
            rohr_name_intern=el["rohr_name_intern"],
            start=tuple(el["start"]),
            ende=tuple(el["ende"]),
            element_id_intern=el.get("element_id_intern"),
            anzeigename=el.get("anzeigename"),
        )

    raise ValueError(f"Unbekannter Bauelement-typ: {typ}")

@dataclass
class Konstruktion:
    """
    Generische Konstruktion:
    - name: Bezeichner (z.B. "Tor", "Steher", "Tisch", "Whatever")
    - build: roher Python-Build aus der UI (dict mit 'bauelemente', ... )
    - bauelemente: Liste von Bodenplatten, Traversenstrecken, Rohren, ...
    """
    name: str = "Konstruktion"
    build: Dict[str, Any] = field(default_factory=dict)
    bauelemente: List[object] = field(default_factory=list)

    def __post_init__(self):
        # Wenn bereits Bauelemente gesetzt wurden, nichts tun
        if self.bauelemente:
            return

        # Build erwartet: {"bauelemente": [...]} – kommt direkt aus JS-Build
        elements_data = self.build.get("bauelemente", [])
        for el in elements_data:
            self.bauelemente.append(_build_bauelement(el))

    # ====== ab hier 1:1 Patterns wie beim bisherigen Tor ======

    def gesamthoehe(
        self, *,
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> float:
        """Maximale Gesamthöhe über alle Bauelemente mit .gesamthoehe()."""
        base_ctx = merge_kontext(kontext, {
            "funktion": "Konstruktion.Gesamthoehe",
        })
        max_h = 0.0
        found = False

        for el in self.bauelemente:
            gh = getattr(el, "gesamthoehe", None)
            if callable(gh):
                try:
                    h = float(gh())
                except Exception:
                    continue
                if h > max_h:
                    max_h = h
                found = True

        if found:
            return max_h

        raise ValueError("Keine Bauelemente mit gesamthoehe() gefunden.")

    def berechne_kippsicherheit(
        self,
        norm: Norm,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        *,
        konst=None,
        reset_berechnungen: bool = True,
        methode: RechenmethodeKippen = RechenmethodeKippen.STANDARD,
        vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
        anzahl_windrichtungen: int = 4,
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> List[Zwischenergebnis]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Konstruktion.BerechneKippsicherheit",
        })

        return _kippsicherheit(
            self,
            norm,
            staudruecke,
            obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            kontext=base_ctx,
        )

    def berechne_gleitsicherheit(
        self,
        norm: Norm,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        *,
        konst=None,
        reset_berechnungen: bool = False,
        methode: RechenmethodeGleiten = RechenmethodeGleiten.MIN_REIBWERT,
        vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
        anzahl_windrichtungen: int = 4,
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> List[Zwischenergebnis]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Konstruktion.BerechneGleitsicherheit",
        })

        return _gleitsicherheit(
            self,
            norm,
            staudruecke,
            obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            kontext=base_ctx,
        )

    def berechne_abhebesicherheit(
        self,
        norm: Norm,
        staudruecke: Sequence[float],
        obergrenzen: Sequence[float],
        *,
        konst=None,
        reset_berechnungen: bool = False,
        methode: RechenmethodeAbheben = RechenmethodeAbheben.STANDARD,
        vereinfachung_konstruktion: VereinfachungKonstruktion = VereinfachungKonstruktion.KEINE,
        anzahl_windrichtungen: int = 4,
        protokoll: Optional[Protokoll] = None,
        kontext: Optional[dict] = None,
    ) -> List[Zwischenergebnis]:
        base_ctx = merge_kontext(kontext, {
            "funktion": "Konstruktion.BerechneAbhebesicherheit",
        })

        return _abhebesicherheit(
            self,
            norm,
            staudruecke,
            obergrenzen,
            konst=konst,
            reset_berechnungen=reset_berechnungen,
            methode=methode,
            vereinfachung_konstruktion=vereinfachung_konstruktion,
            anzahl_windrichtungen=anzahl_windrichtungen,
            protokoll=protokoll,
            kontext=base_ctx,
        )

    def gesamtgewicht(self) -> float:
        return _gesamtgewicht(self)