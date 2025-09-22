from flask import request, jsonify
from . import bp_v1
from .schemas import TorInput, Result
from core_adapter.tor import berechne_tor

@bp_v1.post("/tor/berechnen")
def tor_berechnen():
    try:
        data = TorInput.model_validate_json(request.data)
        payload = data.model_dump()
        resp = berechne_tor(payload)
        return jsonify(Result(**resp).model_dump())
    except Exception as e:
        return jsonify({"error": {"code": "INVALID_INPUT", "message": str(e)}}), 400
