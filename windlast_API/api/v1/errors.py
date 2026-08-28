import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException


def api_error(
    status: int,
    code: str,
    message: str,
):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
        }
    }), status

def handle_api_exception(error):
    if isinstance(error, HTTPException):
        return api_error(
            error.code,
            "HTTP_ERROR",
            error.description,
        )

    logging.exception(
        "Unerwarteter Fehler bei API-Anfrage"
    )

    return api_error(
        500,
        "INTERNAL_ERROR",
        "Bei der Verarbeitung der Anfrage ist ein interner Fehler aufgetreten.",
    )