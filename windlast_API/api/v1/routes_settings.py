from flask import jsonify, request

from . import bp_v1
from app_settings import get_settings_manager
from windlast_CORE.settings import SettingsError


@bp_v1.get("/settings")
def get_settings():
    sm = get_settings_manager()

    return jsonify({
        "settings": sm.all()
    })


@bp_v1.get("/settings/definitions")
def get_settings_definitions():
    sm = get_settings_manager()

    return jsonify({
        "groups": sm.grouped_for_api()
    })


@bp_v1.get("/settings/<path:key>")
def get_setting(key: str):
    sm = get_settings_manager()

    return jsonify({
        "key": key,
        "value": sm.get(key)
    })

@bp_v1.post("/settings/<path:key>")
def set_setting(key: str):
    sm = get_settings_manager()
    data = request.get_json(silent=True) or {}

    if "value" not in data:
        return jsonify({
            "ok": False,
            "error": "missing_value",
            "message": "Request muss ein Feld 'value' enthalten."
        }), 400

    try:
        value = sm.set(key, data["value"])
    except SettingsError as exc:
        return jsonify({
            "ok": False,
            "error": "invalid_setting",
            "message": str(exc)
        }), 400

    return jsonify({
        "ok": True,
        "key": key,
        "value": value
    })

@bp_v1.post("/settings")
def set_settings():
    sm = get_settings_manager()
    data = request.get_json(silent=True) or {}

    updates = data.get("settings")
    if not isinstance(updates, dict):
        return jsonify({
            "ok": False,
            "error": "missing_settings",
            "message": "Request muss ein Objekt 'settings' enthalten."
        }), 400

    try:
        changed = sm.update_many(updates)
    except SettingsError as exc:
        return jsonify({
            "ok": False,
            "error": "invalid_setting",
            "message": str(exc)
        }), 400

    return jsonify({
        "ok": True,
        "settings": changed
    })