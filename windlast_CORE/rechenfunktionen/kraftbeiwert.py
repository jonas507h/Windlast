# rechenfunktionen/kraftbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional
import math

from windlast_CORE.datenstruktur.enums import Norm, ObjektTyp, Severity, senkrechteFlaecheTyp
from windlast_CORE.datenstruktur.zwischenergebnis import (
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.rechenfunktionen.geom3d import Vec3, vektor_laenge, is_parallel

def _validate_inputs(
    objekttyp: ObjektTyp,
    grundkraftbeiwert: Optional[float] = None,
    abminderungsfaktor_schlankheit: Optional[float] = None,
    windrichtung: Optional[Vec3] = None,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    punkte: Optional[list[Vec3]] = None,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if objekttyp == ObjektTyp.TRAVERSE:
        if not math.isfinite(grundkraftbeiwert) or grundkraftbeiwert < 0:
            raise ValueError("grundkraftbeiwert muss endlich und >= 0 sein.")
        if abminderungsfaktor_schlankheit is None:
            raise ValueError("Für TRAVERSE ist abminderungsfaktor_schlankheit erforderlich.")
        if not math.isfinite(abminderungsfaktor_schlankheit) or abminderungsfaktor_schlankheit <= 0:
            raise ValueError("abminderungsfaktor_schlankheit muss > 0 und endlich sein.")
    elif objekttyp == ObjektTyp.ROHR:
        if not math.isfinite(grundkraftbeiwert) or grundkraftbeiwert < 0:
            raise ValueError("grundkraftbeiwert muss endlich und >= 0 sein.")
        if abminderungsfaktor_schlankheit is None:
            raise ValueError("Für ROHR ist abminderungsfaktor_schlankheit erforderlich.")
        if not math.isfinite(abminderungsfaktor_schlankheit) or abminderungsfaktor_schlankheit <= 0:
            raise ValueError("abminderungsfaktor_schlankheit muss > 0 und endlich sein.")
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        n_wind = vektor_laenge(windrichtung)
        if senkrechte_flaeche_typ is None:
            raise ValueError("Für SENKRECHTE_FLAECHE ist senkrechte_flaeche_typ erforderlich.")
        if not (0.999 <= n_wind <= 1.001):
            raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n_wind:.6f}.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) != 4:
            raise ValueError("Für SENKRECHTE_FLAECHE werden genau 4 Eckpunkte erwartet.")

def _kraftbeiwert_default(
    objekttyp: ObjektTyp,
    grundkraftbeiwert: Optional[float] = None,
    abminderungsfaktor_schlankheit: Optional[float] = None,
    windrichtung: Optional[Vec3] = None,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    punkte: Optional[list[Vec3]] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "kraftbeiwert",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
    })

    if objekttyp == ObjektTyp.TRAVERSE:
        wert = grundkraftbeiwert * abminderungsfaktor_schlankheit
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kraftbeiwert c_f",
                wert=wert,
                einzelwerte=[grundkraftbeiwert, abminderungsfaktor_schlankheit],
                formel="c = c₀ · η_schlank",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.ROHR:
        wert = grundkraftbeiwert * abminderungsfaktor_schlankheit
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Kraftbeiwert c_f",
                wert=wert,
                einzelwerte=[grundkraftbeiwert, abminderungsfaktor_schlankheit],
                formel="c = c₀ · η_schlank",
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)
    
    elif objekttyp == ObjektTyp.SENKRECHTE_FLAECHE:
        if senkrechte_flaeche_typ == senkrechteFlaecheTyp.ANZEIGETAFEL:
            if is_parallel('vecs/ebene', vecs=[windrichtung], punkte=punkte):
                # Wind läuft (nahezu) parallel zur Ebene → keine angeströmte Fläche → c_f,0 = 0
                wert = 0.0
                protokolliere_msg(
                    protokoll,
                    severity=Severity.INFO,
                    code="KRAFTBEI/WIND_PARALLEL_FLAECHE",
                    text="Windrichtung verläuft (nahezu) parallel zur Ebene der senkrechten Fläche – c_f = 0.",
                    kontext=base_ctx,
                )
                protokolliere_doc(
                    protokoll,
                    bundle=make_docbundle(
                        titel="Kraftbeiwert c_f",
                        wert=wert,
                        formel="c_f = 0,0 für Anzeigetafeln bei paralleler Anströmung",
                        quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 7.4.3",
                        ),
                    kontext=base_ctx,
                )
            else:
                wert = 1.8

                protokolliere_doc(
                    protokoll,
                    bundle=make_docbundle(
                        titel="Kraftbeiwert c_f",
                        wert=wert,
                        formel="c_f = 1,8 für Anzeigetafeln",
                        quelle_formel="DIN EN 1991-1-4:2010-12, Abschnitt 7.4.3",
                        ),
                    kontext=base_ctx,
                )
            return Zwischenergebnis(wert=wert)
        else:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="KRAFTBEI/NOT_IMPLEMENTED",
                text=f"Kraftbeiwert für senkrechte Fläche vom Typ '{senkrechte_flaeche_typ.name}' ist noch nicht implementiert.",
                kontext=base_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Kraftbeiwert c_f", wert=float("nan")),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))  

    else:
        raise NotImplementedError(f"Schlankheit für Objekttyp '{objekttyp}' ist noch nicht implementiert.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _kraftbeiwert_default,
}

def kraftbeiwert(
    norm: Norm,
    objekttyp: ObjektTyp,
    grundkraftbeiwert: Optional[float] = None,
    abminderungsfaktor_schlankheit: Optional[float] = None,
    windrichtung: Optional[Vec3] = None,
    senkrechte_flaeche_typ: Optional[senkrechteFlaecheTyp] = None,
    punkte: Optional[list[Vec3]] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "kraftbeiwert",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs(objekttyp, grundkraftbeiwert, abminderungsfaktor_schlankheit, windrichtung, senkrechte_flaeche_typ, punkte)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="KRAFT/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Kraftbeiwert c", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, grundkraftbeiwert, abminderungsfaktor_schlankheit, windrichtung, senkrechte_flaeche_typ, punkte,
        protokoll=protokoll, kontext=base_ctx,
    )
