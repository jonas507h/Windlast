from pathlib import Path
import sys

def get_project_root() -> Path:
    """
    Liefert den Projekt-Root sowohl im Dev-Betrieb
    als auch in der PyInstaller-EXE.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]  # windlast_API/ -> Root
