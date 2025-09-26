from flask import request, jsonify
from . import bp_v1
from .schemas import TorInput, Result
from core_adapter.tor import berechne_tor

@bp_v1.post("/tor/berechnen") # Setzt Endpunkt /api/v1/tor/berechnen
def tor_berechnen(): # Funktion wird aufgerufen bei POST-Request
    try:
        data = TorInput.model_validate_json(request.data) # Prüft, ob eingehende JSON-Daten dem Schema TorInput entsprechen
        payload = data.model_dump() # Wandelt validierte Daten in Dictionary um
        resp = berechne_tor(payload) # Ruft die Berechnungsfunktion auf
        return jsonify(Result(**resp).model_dump()) # Validiert Antwort mit Result-Schema und gibt sie als JSON zurück
    except Exception as e:
        return jsonify({"error": {"code": "INVALID_INPUT", "message": str(e)}}), 400
