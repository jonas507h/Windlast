from flask import Blueprint
bp_v1 = Blueprint("api_v1", __name__)

# Import der Routen (am Ende lassen, damit bp_v1 existiert)
from . import routes_config  # noqa: E402,F401
