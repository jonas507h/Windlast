from typing import Dict, Callable
import math
from datenstruktur.zwischenergebnis import Zwischenergebnis
from datenstruktur.enums import Norm, ObjektTyp
from materialdaten.catalog import catalog

def _validate_inputs(
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    staudruck_pa: float,
    zaehigkeit_pa_s: float,
    luftdichte_kg_m3: float,
) -> None:
    if not isinstance(objekttyp, ObjektTyp):
        raise TypeError("objekttyp muss vom Typ ObjektTyp sein.")
    if staudruck_pa <= 0:
        raise ValueError("staudruck muss > 0 sein (in Pa).")
    if zaehigkeit_pa_s <= 0:
        raise ValueError("zaehigkeit muss > 0 sein (in Pa·s).")
    if luftdichte_kg_m3 <= 0:
        raise ValueError("luftdichte muss > 0 sein (in kg/m³).")

def _reynoldszahl_default(
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    staudruck: float,
    zaehigkeit: float,
    luftdichte: float,
) -> Zwischenergebnis:
    geschwindigkeit = math.sqrt(2.0 * staudruck / luftdichte)

    if objekttyp == ObjektTyp.TRAVERSE:
        traverse = catalog.get_traverse(objekt_name_intern)
        charak_Laenge = traverse.d_gurt  # charakteristische Länge (hier: Durchmesser Gurt)
    elif objekttyp == ObjektTyp.ROHR:
        raise NotImplementedError("Objekttyp 'rohr' wird aktuell nicht unterstützt.")
    else:
        raise NotImplementedError(f"Objekttyp '{objekttyp}' wird aktuell nicht unterstützt.")

    wert = geschwindigkeit * charak_Laenge / zaehigkeit

    return Zwischenergebnis(
        wert=wert,
        formel="---",
        quelle_formel="---",
        formelzeichen=["---", "---", "---"],
        quelle_formelzeichen=["---"]
    )

_DISPATCH: Dict[Norm, Callable[
    [ObjektTyp, str, float, float, float], Zwischenergebnis
]] = {
    Norm.DEFAULT: _reynoldszahl_default,
}

def reynoldszahl(
    norm: Norm,
    objekttyp: ObjektTyp,
    objekt_name_intern: str,
    staudruck: float,       # N/m²
    zaehigkeit: float,      # m²/s
    luftdichte: float,      # kg/m³
) -> Zwischenergebnis:
    _validate_inputs(objekttyp, objekt_name_intern, staudruck, zaehigkeit, luftdichte)
    funktion = _DISPATCH.get(norm, _reynoldszahl_default)
    return funktion(objekttyp, objekt_name_intern, staudruck, zaehigkeit, luftdichte)

