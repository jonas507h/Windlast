from typing import Dict, Any, Mapping
from dataclasses import is_dataclass, asdict
from enum import Enum
from math import isinf, isnan


def _json_safe(obj):
    if obj is None:
        return None

    if isinstance(obj, float):
        if isnan(obj):
            return "NaN"
        if isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        return obj

    if isinstance(obj, Enum):
        return obj.name

    if is_dataclass(obj):
        return {k: _json_safe(v) for k, v in asdict(obj).items()}

    if isinstance(obj, Mapping):
        return {
            str(_json_safe(k)): _json_safe(v)
            for k, v in obj.items()
        }

    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]

    return obj


_DENY_KEYS = {
    "headers", "header", "authorization", "auth", "token", "csrf_token",
    "client", "user_agent", "cookies", "session", "trace_id", "request_id"
}


def _make_meta_eingaben(payload: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}

    out: Dict[str, Any] = {}
    for k, v in payload.items():
        if k in _DENY_KEYS:
            continue
        out[k] = _json_safe(v)
    return out


def build_api_output(ergebnisbaum, input_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ergebnis": _json_safe(ergebnisbaum),
        "meta": {
            "eingaben": _make_meta_eingaben(input_payload),
        },
    }