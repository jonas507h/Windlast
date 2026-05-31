from pathlib import Path

from windlast_CORE.settings import SettingsManager, SettingsError


settings_manager: SettingsManager | None = None


def init_settings(resource_dir: Path) -> SettingsManager:
    global settings_manager

    sm = SettingsManager(resource_dir / "preferences.yaml")

    try:
        sm.load()
    except SettingsError as exc:
        raise RuntimeError(
            "\n\n"
            "FEHLER BEIM LADEN DER EINSTELLUNGEN\n"
            "===================================\n"
            f"{exc}\n\n"
            "Die mitgelieferte preferences.yaml ist ungültig.\n"
        ) from exc

    settings_manager = sm
    return sm


def get_settings_manager() -> SettingsManager:
    if settings_manager is None:
        raise RuntimeError("SettingsManager wurde noch nicht initialisiert.")
    return settings_manager