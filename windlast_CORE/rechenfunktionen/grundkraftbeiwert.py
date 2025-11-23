# rechenfunktionen/grundkraftbeiwert.py
from __future__ import annotations
from typing import Dict, Callable, Optional, Sequence
from enum import Enum
import math
import warnings

from windlast_CORE.datenstruktur.enums import Norm, TraversenTyp, ObjektTyp, Severity
from windlast_CORE.datenstruktur.zwischenergebnis import (                              # + Protokoll & Helpers
    Zwischenergebnis,
    Protokoll,
    merge_kontext,
    make_docbundle,
    protokolliere_msg,
    protokolliere_doc,
)
from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.rechenfunktionen.geom3d import (
    Vec3,
    vektor_normieren,
    vektor_laenge,
    vektor_zwischen_punkten,
    projektion_vektor_auf_ebene,
    vektor_winkel,
    vektor_invertieren,
    abstand_punkte,
)
from windlast_CORE.rechenfunktionen.interpolation import interpol_2D
from windlast_CORE.datenstruktur.konstanten import _EPS


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

def _angle_mod180(theta: float) -> float:
    t = theta % 180.0
    return 180.0 if abs(t - 180.0) < 1e-12 else t

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

    if objekttyp == ObjektTyp.TRAVERSE:
        n_wind = vektor_laenge(windrichtung)
        if not (0.999 <= n_wind <= 1.001):
            raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n_wind:.6f}.")
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
        n_wind = vektor_laenge(windrichtung)
        if not (0.999 <= n_wind <= 1.001):
            raise ValueError(f"windrichtung soll Einheitsvektor sein (||v||≈1), ist {n_wind:.6f}.")
        if not isinstance(punkte, (list, tuple)) or len(punkte) < 2:
            raise ValueError("Für ROHR werden [start, ende] erwartet.")
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
                text=f"Reynoldszahl {reynoldszahl:.3g} > 2·10^5: c_f,0 nicht definiert.",
                kontext=base_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Grundkraftbeiwert c_f,0", wert=float("nan")),
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
            wert = 0.0

            protokolliere_msg(
                protokoll,
                severity=Severity.INFO,
                code="WIND/ANSTROEM_NULL",
                text="Windvektor ist parallel zur Traversenachse; Grundkraftbeiwert wird auf 0 gesetzt.",
                kontext=base_ctx,
            )
        else:
            winkel = vektor_winkel(windrichtung_projiziert, orientierung)
            winkel = _angle_mod180(winkel)

            if traversentyp == TraversenTyp.ZWEI_PUNKT:
                x = [0.2, 0.35, 0.55]
                y = [0.7, 0.6, 0.5]
                if not (0.2 - _EPS <= voelligkeitsgrad <= 0.6 + _EPS):
                    protokolliere_msg(
                        protokoll, severity=Severity.WARN, code="GRUNDKRAFT/EXTRAPOLATION_V",
                        text=f"Völligkeitsgrad {voelligkeitsgrad:.3f} außerhalb [{x[0]}, {x[-1]}] – Interpolation extrapoliert.",
                        kontext=merge_kontext(base_ctx, {"bereich": [x[0], x[-1]]}),
                    )
                wert_Ecke = interpol_2D(x, y, voelligkeitsgrad)
                wert_Seite = 1.1

                definierte_winkel = [0.0, 90.0, 180.0]
                definierte_werte = [wert_Ecke, wert_Seite, wert_Ecke]

                wert = interpol_2D(definierte_winkel, definierte_werte, winkel)

            elif traversentyp == TraversenTyp.DREI_PUNKT:
                definierte_winkel = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0]
                definierte_werte = [1.45, 1.3, 1.45, 1.3, 1.45, 1.3, 1.45]

                wert = interpol_2D(definierte_winkel, definierte_werte, winkel)

            elif traversentyp == TraversenTyp.VIER_PUNKT:
                x = [0.25, 0.5]
                y = [2.0, 1.9]
                if not (0.2 - _EPS <= voelligkeitsgrad <= 0.6 + _EPS):
                    protokolliere_msg(
                        protokoll, severity=Severity.WARN, code="GRUNDKRAFT/EXTRAPOLATION_V",
                        text=f"Völligkeitsgrad {voelligkeitsgrad:.3f} außerhalb [{x[0]}, {x[-1]}] – Interpolation extrapoliert.",
                        kontext=merge_kontext(base_ctx, {"bereich": [x[0], x[-1]]}),
                    )
                wert_Ecke = interpol_2D(x, y, voelligkeitsgrad)

                x = [0.2, 0.35, 0.55]
                y = [1.85, 1.6, 1.4]
                if not (0.2 - _EPS <= voelligkeitsgrad <= 0.6 + _EPS):
                    protokolliere_msg(
                        protokoll, severity=Severity.WARN, code="GRUNDKRAFT/EXTRAPOLATION_V",
                        text=f"Völligkeitsgrad {voelligkeitsgrad:.3f} außerhalb [{x[0]}, {x[-1]}] – Interpolation extrapoliert.",
                        kontext=merge_kontext(base_ctx, {"bereich": [x[0], x[-1]]}),
                    )
                wert_Seite = interpol_2D(x, y, voelligkeitsgrad)

                definierte_winkel = [0.0, 45.0, 90.0, 135.0, 180.0]
                definierte_werte = [wert_Seite, wert_Ecke, wert_Seite, wert_Ecke, wert_Seite]

                wert = interpol_2D(definierte_winkel, definierte_werte, winkel)
            else:
                protokolliere_msg(
                    protokoll,
                    severity=Severity.ERROR,
                    code="GRUNDKRAFT/NOT_IMPLEMENTED",
                    text=f"Grundkraftbeiwert für {traversentyp.value} ist noch nicht implementiert.",
                    kontext=base_ctx,
                )
                protokolliere_doc(
                    protokoll,
                    bundle=make_docbundle(titel="Grundkraftbeiwert c_f,0", wert=float("nan")),
                    kontext=merge_kontext(base_ctx, {"nan": True}),
                )
                return Zwischenergebnis(wert=float("nan"))

        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Grundkraftbeiwert c_f,0",
                wert=wert,
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)

    elif objekttyp == ObjektTyp.ROHR:
        rohr_achse = vektor_normieren(vektor_zwischen_punkten(punkte[0], punkte[1]))
        wind_proj = projektion_vektor_auf_ebene(windrichtung, rohr_achse)
        if vektor_laenge(wind_proj) < 1e-9:
            # Wind läuft (nahezu) parallel zur Rohrachse → keine angeströmte Fläche → c_f,0 = 0
            protokolliere_msg(
                protokoll,
                severity=Severity.INFO,
                code="GRUNDKRAFT/WIND_PARALLEL_ROHR",
                text="Windrichtung verläuft (nahezu) parallel zur Rohrachse – c_f,0 = 0.",
                kontext=base_ctx,
            )
            protokolliere_doc(
                protokoll,
                bundle=make_docbundle(titel="Grundkraftbeiwert c_f,0", wert=0.0),
                kontext=base_ctx,
            )
            return Zwischenergebnis(wert=0.0)

        if reynoldszahl is not None and reynoldszahl > 1.8e5:
            protokolliere_msg(
                protokoll,
                severity=Severity.WARN,
                code="GRUNDKRAFT/RE_HIGH_SET_1_2",
                text=f"Re={reynoldszahl:.3g} > 1,8·10^5: setze c_f,0 = 1,2 (ungünstigster Wert).",
                kontext=base_ctx,
            )
        
        wert = 1.2
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(
                titel="Grundkraftbeiwert c_f,0",
                wert=wert,
            ),
            kontext=base_ctx,
        )
        return Zwischenergebnis(wert=wert)

    else:
        protokolliere_msg(
            protokoll,
            severity=Severity.ERROR,
            code="GRUNDKRAFT/NOT_IMPLEMENTED",
            text=f"Grundkraftbeiwert für Objekttyp '{objekttyp.value}' ist noch nicht implementiert.",
            kontext=base_ctx,
        )
        protokolliere_doc(
            protokoll,
            bundle=make_docbundle(titel="Grundkraftbeiwert c_f,0", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))

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
            bundle=make_docbundle(titel="Grundkraftbeiwert c_f,0", wert=float("nan")),
            kontext=merge_kontext(base_ctx, {"nan": True}),
        )
        return Zwischenergebnis(wert=float("nan"))
    
    funktion = _DISPATCH.get(norm, _DISPATCH[Norm.DEFAULT])
    return funktion(
        objekttyp, objekt_name_intern, punkte, abschnitt, windrichtung, voelligkeitsgrad, reynoldszahl,
        protokoll=protokoll, kontext=base_ctx,
    )
