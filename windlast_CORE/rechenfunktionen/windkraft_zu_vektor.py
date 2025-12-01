# rechenfunktionen/windkraft_zu_vektor.py
from __future__ import annotations
from typing import Dict, Callable, Sequence, Optional
import math

from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity, senkrechteFlaecheTyp
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis_Vektor,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
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
    kontext: Optional[dict] = None,
) -> Zwischenergebnis_Vektor:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "windkraft_zu_vektor",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "windkraft": windkraft,
        "windrichtung": windrichtung,
    })

    if objekttyp == ObjektTyp.TRAVERSE:
        start, ende = punkte
        achse = vektor_normieren(vektor_zwischen_punkten(start, ende))
        senkrechtanteil = vektor_senkrechtanteil(windrichtung, achse)
        kraft_vec: Vec3 = vektor_multiplizieren(senkrechtanteil, windkraft)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft-Vektor F_W",
                wert=kraft_vec,
                einzelwerte=[windkraft, *senkrechtanteil, *achse],
                formel="F_W = F · ( ê − (ê·t̂) t̂ )",
                einheit="N",
                formelzeichen=["F_W", "F", "ê", "t̂"],
                quelle_formelzeichen=["Projektintern"],
            ),
            kontext=merge_kontext(base_ctx, {"start": start, "ende": ende}),
        )
        return Zwischenergebnis_Vektor(wert=kraft_vec)
    
    elif objekttyp == ObjektTyp.ROHR:
        start, ende = punkte
        achse = vektor_normieren(vektor_zwischen_punkten(start, ende))
        senkrechtanteil = vektor_senkrechtanteil(windrichtung, achse)
        kraft_vec: Vec3 = vektor_multiplizieren(senkrechtanteil, windkraft)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft-Vektor F_W",
                wert=kraft_vec,
                einzelwerte=[windkraft, *senkrechtanteil, *achse],
                formel="F_W = F · ( ê − (ê·t̂) t̂ )",
                einheit="N",
                formelzeichen=["F_W", "F", "ê", "t̂"],
                quelle_formelzeichen=["Projektintern"],
            ),
            kontext=merge_kontext(base_ctx, {"start": start, "ende": ende}),
        )
        return Zwischenergebnis_Vektor(wert=kraft_vec)
    
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        if senkrechte_flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            normale = normale_zu_ebene(punkte)
            parallelanteil = vektor_parallelanteil(windrichtung, normale)
            kraft_vec: Vec3 = vektor_multiplizieren(parallelanteil, windkraft)

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Windkraft-Vektor F_W",
                wert=kraft_vec,
                einzelwerte=[windkraft, *parallelanteil, *normale],
                einheit="N",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis_Vektor(wert=kraft_vec)
    
    else:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="WINDVEK/NOT_IMPLEMENTED",
            text=f"Windkraft-Vektor für Objekttyp {objekttyp.name} ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        bad = (float("nan"), float("nan"), float("nan"))
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Windkraft (Vektor) F_W", wert=bad),
            kontext=merge_kontext(base_ctx, {"nan": True}),
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
    kontext: Optional[dict] = None,
) -> Zwischenergebnis_Vektor:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "windkraft_zu_vektor",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "norm": getattr(norm, "name", str(norm)),
        "windkraft": windkraft,
        "windrichtung": windrichtung,
    })

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
            kontext=base_ctx,
        )
        bad = (float("nan"), float("nan"), float("nan"))
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Windkraft-Vektor F⃗_w", wert=bad),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis_Vektor(wert=bad)
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, punkte, windkraft, windrichtung, senkrechte_flaeche_typ,
        protokoll=protokoll, kontext=base_ctx,
    )
