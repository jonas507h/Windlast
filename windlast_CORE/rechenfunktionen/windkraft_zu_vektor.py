# rechenfunktionen/windkraft_zu_vektor.py
from __future__ import annotations
from typing import Dict, Callable, Sequence, Optional
import math

from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity, senkrechteFlaecheTyp
from windlast_CORE.datenstruktur.zwischenergebnis import Zwischenergebnis_Vektor, Protokoll, merge_breadcrumb, bc_step, protokolliere_msg, protokolliere_ergebnis, set_winner
from windlast_CORE.rechenfunktionen.geom3d import (
    Vec3,
    vektor_laenge,
    vektor_zwischen_punkten,
    vektor_normieren,
    vektor_senkrechtanteil,
    vektor_parallelanteil,
    vektor_multiplizieren,
    normale_zu_ebene,
)

def _validate_inputs(
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,   # Einheitsvektor
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("Objekttyp muss vom Typ ObjektTyp sein.")
    if not math.isfinite(windkraft) or windkraft < 0:
        raise ValueError("Windkraft muss endlich und ≥ 0 sein.")

    n = vektor_laenge(windrichtung)
    if not (0.999 <= n <= 1.001):
        raise ValueError(f"Windrichtung soll Einheitsvektor sein (||v||≈1), ist {n:.6f}.")

    if objekttyp in (ObjektTyp.TRAVERSE, ObjektTyp.ROHR):
        if punkte is None or len(punkte) != 2:
            raise ValueError("Für Traverse/Rohr werden genau zwei Punkte (Start, Ende) benötigt.")
        start, ende = punkte
        achse_vec = vektor_zwischen_punkten(start, ende)
        if vektor_laenge(achse_vec) <= 1e-12:
            raise ValueError("Start- und Endpunkt der Achse fallen (nahezu) zusammen.")
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        if senkrechte_flaeche_typ is None:
            raise ValueError("Für SENKRECHTE_FLAECHE ist senkrechte_flaeche_typ erforderlich.")
        if punkte is None or len(punkte) != 4:
            raise ValueError("Für SENKRECHTE_FLAECHE werden genau 4 Eckpunkte erwartet.")
    
def _windkraft_zu_vektor_default(
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis_Vektor:
    
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "windkraft_zu_vektor_default",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
    }

    if objekttyp == ObjektTyp.TRAVERSE:
        start, ende = punkte
        achse = vektor_normieren(vektor_zwischen_punkten(start, ende))
        senkrechtanteil = vektor_senkrechtanteil(windrichtung, achse)
        kraft_vec: Vec3 = vektor_multiplizieren(senkrechtanteil, windkraft)

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft_vektor",
            wert=kraft_vec,
            label="math.windkraft_vektor_traverse.label",
            formelzeichen="math.windkraft_vektor_traverse.symbol",
            formel="math.windkraft_vektor_traverse.formula",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis_Vektor(wert=kraft_vec)
    
    elif objekttyp == ObjektTyp.ROHR:
        start, ende = punkte
        achse = vektor_normieren(vektor_zwischen_punkten(start, ende))
        senkrechtanteil = vektor_senkrechtanteil(windrichtung, achse)
        kraft_vec: Vec3 = vektor_multiplizieren(senkrechtanteil, windkraft)

        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft_vektor",
            wert=kraft_vec,
            label="math.windkraft_vektor_rohr.label",
            formelzeichen="math.windkraft_vektor_rohr.symbol",
            formel="math.windkraft_vektor_rohr.formula",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis_Vektor(wert=kraft_vec)

    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        flaeche_meta = {
            **base_meta,
            "senkrechte_flaeche_typ": getattr(senkrechte_flaeche_typ, "value", str(senkrechte_flaeche_typ)),
        }
        if senkrechte_flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            normale = normale_zu_ebene(punkte)
            parallelanteil = vektor_parallelanteil(windrichtung, normale)
            kraft_vec: Vec3 = vektor_multiplizieren(parallelanteil, windkraft)

            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="windkraft_vektor",
                wert=kraft_vec,
                label="math.windkraft_vektor_anzeigetafel.label",
                formelzeichen="math.windkraft_vektor_anzeigetafel.symbol",
                formel="math.windkraft_vektor_anzeigetafel.formula",
                priority=30,
                einheit="N",
                meta=flaeche_meta,
            )
        elif senkrechte_flaeche_typ == senkrechteFlaecheTyp.WAND:
            normale = normale_zu_ebene(punkte)
            kraft_vec: Vec3 = vektor_multiplizieren(normale, windkraft)

            protokolliere_ergebnis(
                protokoll,
                breadcrumb=base_bc,
                name="windkraft_vektor",
                wert=kraft_vec,
                label="math.windkraft_vektor_wand.label",
                formelzeichen="math.windkraft_vektor_wand.symbol",
                formel="math.windkraft_vektor_wand.formula",
                priority=30,
                einheit="N",
                meta=flaeche_meta,
            )
        else:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="WINDVEK/INVALID_SURFACE_TYPE",
                text=f"Ungültiger Typ für senkrechte Fläche: {senkrechte_flaeche_typ.value}.",
                breadcrumb=base_bc,
                meta=flaeche_meta,
            )
            return Zwischenergebnis_Vektor(wert=(float("nan"), float("nan"), float("nan")))
        return Zwischenergebnis_Vektor(wert=kraft_vec)
    
    else:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDVEK/NOT_IMPLEMENTED",
            text=f"Windkraft-Vektor für Objekttyp {objekttyp.value} ist noch nicht implementiert.",
            breadcrumb=base_bc,
            meta=base_meta,
        )
        bad = (float("nan"), float("nan"), float("nan"))
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft_vektor",
            wert=bad,
            label="math.windkraft_vektor.label",
            formelzeichen="math.windkraft_vektor.symbol",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis_Vektor(wert=bad)

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis_Vektor]] = {
    Norm.DEFAULT: _windkraft_zu_vektor_default,
}

def windkraft_zu_vektor(
    norm: Norm,
    objekttyp: ObjektTyp,
    punkte: Optional[Sequence[Vec3]],
    windkraft: float,
    windrichtung: Vec3,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    breadcrumb: Optional[list] = None,
) -> Zwischenergebnis_Vektor:
    base_bc = breadcrumb if breadcrumb is not None else []
    base_meta = {
        "funktion": "windkraft_zu_vektor",
    }

    try:
        _validate_inputs(objekttyp, punkte, windkraft, windrichtung, senkrechte_flaeche_typ)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDVEK/INPUT_INVALID",
            text=str(e),
            breadcrumb=base_bc,
            meta=base_meta,
        )
        bad = (float("nan"), float("nan"), float("nan"))
        protokolliere_ergebnis(
            protokoll,
            breadcrumb=base_bc,
            name="windkraft_vektor",
            wert=bad,
            label="math.windkraft_vektor.label",
            formelzeichen="math.windkraft_vektor.symbol",
            priority=30,
            einheit="N",
            meta=base_meta,
        )
        return Zwischenergebnis_Vektor(wert=bad)
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, punkte, windkraft, windrichtung, senkrechte_flaeche_typ,
        protokoll=protokoll, breadcrumb=base_bc,
    )
