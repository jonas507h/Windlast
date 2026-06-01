from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .definitions import SETTING_DEFS, SettingDef


class SettingsError(RuntimeError):
    pass


class SettingsManager:
    def __init__(self, preferences_path: Path | str | None = None):
        self.preferences_path = Path(preferences_path) if preferences_path else None
        self.definitions: dict[str, SettingDef] = {
            setting.key: setting for setting in SETTING_DEFS
        }
        self.values: dict[str, Any] = {}

    def load(self) -> None:
        raw_preferences = self._load_preferences()
        flat_preferences = flatten_dict(raw_preferences)

        unknown_keys = sorted(set(flat_preferences) - set(self.definitions))
        if unknown_keys:
            raise SettingsError(
                "Unbekannte Settings in preferences.yaml: "
                + ", ".join(unknown_keys)
            )

        values: dict[str, Any] = {}

        for key, definition in self.definitions.items():
            value = flat_preferences.get(key, definition.default)
            values[key] = self._validate_value(definition, value)

        self.values = values

    def get(self, key: str) -> Any:
        if key not in self.values:
            raise SettingsError(f"Setting nicht gefunden: {key}")
        return self.values[key]
    
    def set(self, key: str, value: Any) -> Any:
        if key not in self.definitions:
            raise SettingsError(f"Unbekanntes Setting: {key}")

        definition = self.definitions[key]
        clean_value = self._validate_value(definition, value)

        self.values[key] = clean_value
        return clean_value
    
    def update_many(self, updates: dict[str, Any]) -> dict[str, Any]:
        changed = {}

        for key, value in updates.items():
            changed[key] = self.set(key, value)

        return changed

    def all(self) -> dict[str, Any]:
        return dict(self.values)

    def definitions_for_api(self) -> list[dict[str, Any]]:
        return [
            {
                "key": setting.key,
                "group": setting.group,
                "label": setting.label,
                "type": setting.type,
                "default": setting.default,
                "description": setting.description,
                "min": setting.min,
                "max": setting.max,
                "allowed": setting.allowed,
                "options": setting.options,
                "meta": setting.meta,
                "value": self.values.get(setting.key, setting.default),
            }
            for setting in self.definitions.values()
        ]

    def grouped_for_api(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}

        for item in self.definitions_for_api():
            grouped.setdefault(item["group"], []).append(item)

        return grouped

    def _load_preferences(self) -> dict[str, Any]:
        if self.preferences_path is None:
            return {}

        if not self.preferences_path.exists():
            raise SettingsError(f"preferences.yaml nicht gefunden: {self.preferences_path}")

        try:
            with self.preferences_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise SettingsError(f"Ungültiges YAML in {self.preferences_path}: {exc}") from exc

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise SettingsError("preferences.yaml: Root-Element muss ein Objekt sein.")
        
        data.pop("schemaVersion", None)

        return data

    def _validate_value(self, definition: SettingDef, value: Any) -> Any:
        if definition.type == "bool":
            if not isinstance(value, bool):
                raise SettingsError(f"{definition.key}: Erwartet bool, bekommen {type(value).__name__}.")
            return value

        if definition.type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                raise SettingsError(f"{definition.key}: Erwartet int, bekommen {type(value).__name__}.")
            self._validate_number_limits(definition, value)
            return value

        if definition.type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise SettingsError(f"{definition.key}: Erwartet float, bekommen {type(value).__name__}.")
            value = float(value)
            self._validate_number_limits(definition, value)
            return value

        if definition.type == "string":
            if not isinstance(value, str):
                raise SettingsError(f"{definition.key}: Erwartet string, bekommen {type(value).__name__}.")
            if definition.allowed is not None and value not in definition.allowed:
                raise SettingsError(f"{definition.key}: Ungültiger Wert '{value}'.")
            return value

        if definition.type == "enum":
            if not isinstance(value, str):
                raise SettingsError(...)

            allowed_values = [opt["value"] for opt in definition.options or []]

            if value not in allowed_values:
                raise SettingsError(f"{definition.key}: Ungültige Option '{value}'.")

            return value

        raise SettingsError(f"{definition.key}: Unbekannter Setting-Typ '{definition.type}'.")

    def _validate_number_limits(self, definition: SettingDef, value: int | float) -> None:
        if definition.min is not None and value < definition.min:
            raise SettingsError(f"{definition.key}: Wert {value} ist kleiner als Minimum {definition.min}.")

        if definition.max is not None and value > definition.max:
            raise SettingsError(f"{definition.key}: Wert {value} ist größer als Maximum {definition.max}.")

        if definition.allowed is not None and value not in definition.allowed:
            raise SettingsError(f"{definition.key}: Wert {value} ist nicht erlaubt.")


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)

        if isinstance(value, dict):
            result.update(flatten_dict(value, full_key))
        else:
            result[full_key] = value

    return result