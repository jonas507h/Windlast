from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ResourceError(RuntimeError):
    pass


class ResourceManager:
    def __init__(self, resource_dir: Path | str):
        self.resource_dir = Path(resource_dir)
        self.index: dict[str, Any] = {}
        self.preferences: dict[str, Any] = {}
        self.resources: dict[str, Any] = {}

    def load(self) -> None:
        try:
            self.index = self._load_json("index.json")
            self.preferences = self._load_json("preferences.json")

            language = (
                self.preferences.get("language")
                or self.index.get("defaultLanguage")
                or "de"
            )

            self.resources = {}

            domains = self.index.get("domains", {})
            if not isinstance(domains, dict):
                raise ResourceError("index.json: 'domains' muss ein Objekt sein.")

            for domain_name, domain_config in domains.items():
                file_path = domain_config.get(language)

                if not file_path:
                    raise ResourceError(
                        f"Keine Resource-Datei für Domain '{domain_name}' "
                        f"und Sprache '{language}' definiert."
                    )

                data = self._load_json(file_path)
                entries = data.get("entries")

                if not isinstance(entries, dict):
                    raise ResourceError(
                        f"{file_path}: Feld 'entries' fehlt oder ist kein Objekt."
                    )

                self._flatten_domain(domain_name, entries)

        except Exception as exc:
            if isinstance(exc, ResourceError):
                raise

            raise ResourceError(
                f"Resources konnten nicht geladen werden: {exc}"
            ) from exc

    def get(self, key: str, fallback: Any = None) -> Any:
        return self.resources.get(key, fallback)

    def require(self, key: str) -> Any:
        if key not in self.resources:
            raise ResourceError(f"Resource-Key nicht gefunden: {key}")
        return self.resources[key]

    def all(self) -> dict[str, Any]:
        return dict(self.resources)

    def _load_json(self, relative_path: str) -> dict[str, Any]:
        path = self.resource_dir / relative_path

        if not path.exists():
            raise ResourceError(f"Resource-Datei nicht gefunden: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise ResourceError(
                f"Ungültiges JSON in {path}: Zeile {exc.lineno}, Spalte {exc.colno}"
            ) from exc

    def _flatten_domain(self, domain_name: str, entries: dict[str, Any]) -> None:
        for entry_name, entry_value in entries.items():
            self._flatten_value(
                prefix=f"{domain_name}.{entry_name}",
                value=entry_value,
            )

    def _flatten_value(self, prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                self._flatten_value(f"{prefix}.{key}", child)
        else:
            if prefix in self.resources:
                raise ResourceError(f"Doppelter Resource-Key: {prefix}")

            self.resources[prefix] = value