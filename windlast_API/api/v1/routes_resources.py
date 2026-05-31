from flask import jsonify
from . import bp_v1

from app_resources import get_resource_manager


@bp_v1.get("/resources")
def get_resources():
    rm = get_resource_manager()
    return jsonify({
        "resources": rm.all()
    })


@bp_v1.get("/resources/<path:key>")
def get_resource(key: str):
    rm = get_resource_manager()
    return jsonify({
        "key": key,
        "value": rm.require(key)
    })