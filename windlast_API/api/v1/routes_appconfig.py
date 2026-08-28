from flask import current_app
from . import bp_v1

@bp_v1.get("/appconfig/runtime")
def runtime_config():
    mode = current_app.config["RUNTIME_MODE"]

    return {
        "mode": mode.value,
    }
