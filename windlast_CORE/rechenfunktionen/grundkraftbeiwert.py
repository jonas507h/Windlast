# rechenfunktionen/grundkraftbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional, Sequence
from enum import Enum
import math
import warnings

from datenstruktur.enums import Norm, TraversenTyp, ObjektTyp, Severity
from datenstruktur.zwischenergebnis import (                              # + Protokoll & Helpers
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from materialdaten.catalog import catalog
from rechenfunktionen.geom3d import (
    Vec3,
    vektor_normieren,
    vektor_laenge,
    vektor_zwischen_punkten,
    projektion_vektor_auf_ebene,
    vektor_winkel,
    vektor_invertieren,
    abstand_punkte,
)
from rechenfunktionen.interpolation import interpol_2D
from datenstruktur.konstanten import _EPS


class Anstroemrichtung(Enum):
    FLAECHE = "flaeche"
    ECKE = "ecke"
    MITTE = "mitte"
    PARALLEL = "parallel"

_TRUSS_TO_FACES = {
    TraversenTyp.ZWEI_PUNKT: 2,
    TraversenTyp.DREI_PUNKT: 3,
    TraversenTyp.VIER_PUNKT: 4,
}

def anzahl_flaechen(typ: TraversenTyp) -> int:
    return _TRUSS_TO_FACES[typ]


def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str] = None,
    punkte: Optional[Sequence[Vec3]] = None,   # TRAVERSE: [start, ende, orientierung]
    abschnitt: Optional[str] = None,
    windrichtung: Optional[Vec3] = None,       # Einheitsvektor
    voelligkeitsgrad: Optional[float] = None,
    reynoldszahl: Optional[float] = None,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")

    n_wind = vektor_laenge(windrichtung)
    if not (0.999 <= n_wind <= 1.001):
        raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n_wind:.6f}.")

    if objekttyp == ObjektTyp.TRAVERSE:
        if not objekt_name_intern:
            raise ValueError("Für TRAVERSE ist objekt_name_intern erforderlich.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 3:
            raise ValueError("Für TRAVERSE werden [start, ende, orientierung] erwartet.")
        startpunkt, endpunkt, orientierung = punkte[0], punkte[1], punkte[2]
        if abstand_punkte(startpunkt, endpunkt) <= _EPS:
            raise ValueError("Start- und Endpunkt dürfen nicht identisch (bzw. zu nah) sein.")
        n_ori = vektor_laenge(orientierung)
        if not (0.999 <= n_ori <= 1.001):
            raise ValueError(f"orientierung soll Einheitsvektor sein (||v||≈1), ist {n_ori:.6f}.")
        if voelligkeitsgrad is None or reynoldszahl is None:
            raise ValueError("Für TRAVERSE sind voelligkeitsgrad und reynoldszahl erforderlich.")
        if not (0.0 <= voelligkeitsgrad <= 1.0):
            raise ValueError("voelligkeitsgrad muss in [0, 1] liegen.")
        if reynoldszahl <= 0:
            raise ValueError("reynoldszahl muss > 0 sein.")
    elif objekttyp == ObjektTyp.ROHR:
        if reynoldszahl is not None and reynoldszahl <= 0:
            raise ValueError("reynoldszahl muss > 0 sein (falls übergeben).")

    else:
        # Für andere Typen aktuell keine Pflichtparameter definiert
        pass

def _grundkraftbeiwert_DinEn1991_1_4_2010_12(
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str] = None,
    punkte: Optional[Sequence[Vec3]] = None,
    abschnitt: Optional[str] = None,
    windrichtung: Optional[Vec3] = None,
    voelligkeitsgrad: Optional[float] = None,
    reynoldszahl: Optional[float] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "grundkraftbeiwert",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "abschnitt": abschnitt,
    })

    if objekttyp == ObjektTyp.TRAVERSE:
        if reynoldszahl is not None and reynoldszahl > 2e5:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="GRUNDKRAFT/RE_OUT_OF_RANGE",
                text=f"Reynoldszahl {reynoldszahl:.3g} > 2·10^5: c₀ nicht definiert.",
                kontext=base_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Grundkraftbeiwert c₀", wert=float("nan"),
                                      einzelwerte=[voelligkeitsgrad, reynoldszahl]),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))
        
        startpunkt, endpunkt, orientierung = punkte[0], punkte[1], punkte[2]

        traversenachse = vektor_zwischen_punkten(startpunkt, endpunkt)
        traversenachse_norm = vektor_normieren(traversenachse)
        windrichtung_projiziert = vektor_invertieren(
            projektion_vektor_auf_ebene(windrichtung, traversenachse_norm)
        )
        traverse = catalog.get_traverse(objekt_name_intern)
        traversentyp = TraversenTyp.from_points(traverse.anzahl_gurtrohre)

        # Anströmrichtung
        if vektor_laenge(windrichtung_projiziert) < 1e-9:
            anstroemrichtung = Anstroemrichtung.PARALLEL
        else:
            winkel = vektor_winkel(windrichtung_projiziert, orientierung)
            if traversentyp == TraversenTyp.DREI_PUNKT:
                winkel += 90.0

            halbe_Abschnittgroesse = 180.0 / anzahl_flaechen(traversentyp)
            rest = math.fmod(winkel, halbe_Abschnittgroesse)
            if rest < 0:
                rest += halbe_Abschnittgroesse
            if rest < halbe_Abschnittgroesse / 2:
                anstroemrichtung = Anstroemrichtung.FLAECHE
            elif rest < halbe_Abschnittgroesse:
                anstroemrichtung = Anstroemrichtung.ECKE
            else:
                anstroemrichtung = Anstroemrichtung.MITTE

        wert: Optional[float] = None
        if traversentyp == TraversenTyp.ZWEI_PUNKT:
            if anstroemrichtung in (Anstroemrichtung.FLAECHE, Anstroemrichtung.MITTE, Anstroemrichtung.PARALLEL):
                wert = 1.1
            elif anstroemrichtung == Anstroemrichtung.ECKE:
                x = [0.2, 0.35, 0.55]
                y = [0.7, 0.6, 0.5]
                if not (x[0] - _EPS <= voelligkeitsgrad <= x[-1] + _EPS):
                    protokolliere_msg(
                        protokoll, severity=Severity.WARN, code="GRUNDKRAFT/EXTRAPOLATION_V",
                        text=f"Völligkeitsgrad {voelligkeitsgrad:.3f} außerhalb [{x[0]}, {x[-1]}] – Interpolation extrapoliert.",
                        kontext=merge_kontext(base_ctx, {"bereich": [x[0], x[-1]]}),
                    )
                wert = interpol_2D(x, y, voelligkeitsgrad)

        elif traversentyp == TraversenTyp.DREI_PUNKT:
            if anstroemrichtung in (Anstroemrichtung.FLAECHE, Anstroemrichtung.PARALLEL):
                wert = 1.3
            elif anstroemrichtung in (Anstroemrichtung.ECKE, Anstroemrichtung.MITTE):
                wert = 1.45

        elif traversentyp == TraversenTyp.VIER_PUNKT:
            if anstroemrichtung in (Anstroemrichtung.FLAECHE, Anstroemrichtung.PARALLEL):
                x = [0.2, 0.35, 0.55]
                y = [1.85, 1.6, 1.4]
                if not (x[0] - _EPS <= voelligkeitsgrad <= x[-1] + _EPS):
                    protokolliere_msg(
                        protokoll, severity=Severity.WARN, code="GRUNDKRAFT/EXTRAPOLATION_V",
                        text=f"Völligkeitsgrad {voelligkeitsgrad:.3f} außerhalb [{x[0]}, {x[-1]}] – Interpolation extrapoliert.",
                        kontext=merge_kontext(base_ctx, {"bereich": [x[0], x[-1]]}),
                    )
                wert = interpol_2D(x, y, voelligkeitsgrad)
            elif anstroemrichtung == Anstroemrichtung.ECKE:
                x = [0.25, 0.5]
                y = [2.0, 1.9]
                if not (x[0] - _EPS <= voelligkeitsgrad <= x[-1] + _EPS):
                    protokolliere_msg(
                        protokoll, severity=Severity.WARN, code="GRUNDKRAFT/EXTRAPOLATION_V",
                        text=f"Völligkeitsgrad {voelligkeitsgrad:.3f} außerhalb [{x[0]}, {x[-1]}] – Interpolation extrapoliert.",
                        kontext=merge_kontext(base_ctx, {"bereich": [x[0], x[-1]]}),
                    )
                wert = interpol_2D(x, y, voelligkeitsgrad)

        if wert is None:
            protokolliere_msg(
                protokoll,
                severity=Severity.ERROR,
                code="GRUNDKRAFT/NICHT_ZUGEORDNET",
                text=f"Keine Zuordnung für {traversentyp.name} bei Anströmung {anstroemrichtung.name}.",
                kontext=base_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Grundkraftbeiwert c₀", wert=float("nan"),
                                      einzelwerte=[voelligkeitsgrad, reynoldszahl, str(anstroemrichtung)]),
                kontext=merge_kontext(base_ctx, {"nan": True}),
            )
            return Zwischenergebnis(wert=float("nan"))

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Grundkraftbeiwert c₀",
                wert=wert,
                einzelwerte=[voelligkeitsgrad, reynoldszahl, str(anstroemrichtung), traversentyp.name],
                # formel/quelle kannst du ergänzen, sobald referenziert
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)

    elif objekttyp == ObjektTyp.ROHR:
        if reynoldszahl is not None and reynoldszahl > 1.8e5:
            protokolliere_msg(
                protokoll,
                severity=Severity.WARN,
                code="GRUNDKRAFT/RE_HIGH_SET_1_2",
                text=f"Re={reynoldszahl:.3g} > 1,8·10^5: setze c₀ = 1,2 (ungünstigster Wert).",
                kontext=base_ctx,
            )
        
        wert = 1.2
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Grundkraftbeiwert c₀",
                wert=wert,
                einzelwerte=[reynoldszahl],
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)

    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

_DISPATCH: Dict[Norm, Callable[..., Zwischenergebnis]] = {
    Norm.DEFAULT: _grundkraftbeiwert_DinEn1991_1_4_2010_12,
    Norm.DIN_EN_1991_1_4_2010_12: _grundkraftbeiwert_DinEn1991_1_4_2010_12,
}

def grundkraftbeiwert(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: Optional[str] = None,
    punkte: Optional[Sequence[Vec3]] = None,   # TRAVERSE: [start, ende, orientierung]
    abschnitt: Optional[str] = None,
    windrichtung: Optional[Vec3] = None,       # Einheitsvektor
    voelligkeitsgrad: Optional[float] = None,
    reynoldszahl: Optional[float] = None,
    *,
    protokoll: Optional[Protokoll] = None,
    kontext: Optional[dict] = None,   
) -> Zwischenergebnis:
    
    base_ctx = merge_kontext(kontext, {
        "funktion": "grundkraftbeiwert",
        "objekttyp": getattr(objekttyp, "name", str(objekttyp)),
        "objekt_name_intern": objekt_name_intern,
        "norm": getattr(norm, "name", str(norm)),
    })

    try:
        _validate_inputs(objekttyp, objekt_name_intern, punkte, abschnitt, windrichtung, voelligkeitsgrad, reynoldszahl)
    except NotImplementedError:
        raise
    except ValueError as e:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="GRUNDKRAFT/INPUT_INVALID",
            text=str(e),
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Grundkraftbeiwert c₀", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte, abschnitt, windrichtung, voelligkeitsgrad, reynoldszahl,
        protokoll=protokoll, kontext=base_ctx,
    )
