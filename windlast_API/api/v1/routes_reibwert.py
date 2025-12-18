# routes_reibwert.py
from __future__ import annotations

from flask import jsonify, request
from . import bp_v1

from windlast_CORE.materialdaten.catalog import catalog
from windlast_CORE.datenstruktur.enums import MaterialTyp, Norm
from windlast_CORE.rechenfunktionen.reibwert import pair_supported, materialfolge_supported


def _parse_bool_ja_nein(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    v = str(value).strip().lower()
    if v in ("1", "true", "ja", "yes", "y"):
        return True
    if v in ("0", "false", "nein", "no", "n"):
        return False
    return default


def _parse_norm(value: str | None) -> Norm:
    # Erwartet Enum-Name (z.B. DIN_EN_17879_2024_08) oder .value
    if not value:
        return Norm.DIN_EN_17879_2024_08
    try:
        return Norm[value]
    except KeyError:
        for n in Norm:
            if n.value == value:
                return n
        raise


def _bodenplatte_material(name_intern: str) -> MaterialTyp:
    bp = catalog.bodenplatten.get(name_intern)
    if not bp:
        raise KeyError(f"Unbekannte Bodenplatte: {name_intern}")

    mat = getattr(bp, "material", None)
    if not isinstance(mat, MaterialTyp):
        raise KeyError(f"Bodenplatte '{name_intern}' hat kein gültiges MaterialTyp-Feld 'material'.")
    return mat


def _allowed_untergruende(bp_mat: MaterialTyp, use_gummi: bool, norm: Norm) -> list[str]:
    allowed: list[str] = []
    for ug in MaterialTyp:
        # bewusst MaterialTyp komplett: BP<->UG bzw. Gummi<->UG (Materialpaarungen)
        if use_gummi:
            ok = materialfolge_supported(norm, [bp_mat, MaterialTyp.GUMMI, ug])
        else:
            ok = materialfolge_supported(norm, [bp_mat, ug])

        if ok:
            allowed.append(ug.name)
    return allowed


@bp_v1.get("/reibwert/kompatibilitaet")
def get_reibwert_kompatibilitaet():
    bp_name = (request.args.get("bodenplatte") or "").strip()
    gummi_requested = _parse_bool_ja_nein(request.args.get("gummimatte"), default=False)
    norm = _parse_norm(request.args.get("norm"))

    if not bp_name:
        return jsonify({"error": "Parameter 'bodenplatte' fehlt."}), 400

    try:
        bp_mat = _bodenplatte_material(bp_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # 1) Darf man überhaupt Gummi zwischen BP und etwas verwenden?
    # (Deine Regel: erst BP<->Gummi prüfen, sonst "ja" ausblenden)
    can_use_gummi = pair_supported(bp_mat, MaterialTyp.GUMMI, norm)

    allowed_gummi = ["ja", "nein"] if can_use_gummi else ["nein"]
    gummi_effective = bool(gummi_requested and can_use_gummi)

    # 2) Untergründe abhängig von effective gummi filtern
    allowed_ug = _allowed_untergruende(bp_mat, gummi_effective, norm)

    return jsonify({
        "gummimatte": {
            "allowed": allowed_gummi,
            "requested": "ja" if gummi_requested else "nein",
            "effective": "ja" if gummi_effective else "nein",
        },
        "untergruende": {
            "allowed": allowed_ug
        }
    })
