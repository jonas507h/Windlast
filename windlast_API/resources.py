from pathlib import Path

from windlast_CORE.resource_manager import ResourceManager, ResourceError

resource_manager: ResourceManager | None = None


def init_resources(root: Path) -> ResourceManager:
    global resource_manager

    resource_dir = root / "windlast_CORE" / "resources"
    rm = ResourceManager(resource_dir)

    try:
        rm.load()
    except ResourceError as exc:
        raise RuntimeError(
            "\n\n"
            "FEHLER BEIM LADEN DER INTERNEN RESSOURCEN\n"
            "=========================================\n"
            f"{exc}\n\n"
            "Die mitgelieferten Resource-Dateien sind ungültig oder unvollständig.\n"
            "Bitte Installation/Build prüfen.\n"
        ) from exc

    resource_manager = rm
    return rm


def get_resource_manager() -> ResourceManager:
    if resource_manager is None:
        raise RuntimeError("ResourceManager wurde noch nicht initialisiert.")
    return resource_manager