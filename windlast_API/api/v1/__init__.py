from flask import Blueprint
from .errors import handle_api_exception

bp_v1 = Blueprint("api_v1", __name__)
bp_v1.register_error_handler(
    Exception,
    handle_api_exception,
)

# Import der Routen (am Ende lassen, damit bp_v1 existiert)
from . import routes_config  # noqa: E402,F401
from . import routes_catalog
from . import routes_berechnung
from . import routes_reibwert
from . import routes_meta
from . import routes_appconfig