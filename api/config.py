from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

VERSION = "0.2.0"


def _is_frozen() -> bool:
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def get_base_dir() -> Path:
    """Get the base directory for the application.

    When running as a PyInstaller bundle, this is the directory containing
    the executable. In development, it's the project root.
    """
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Get the platform-specific data directory for PaperQuant.

    Used for runtime data (caches, databases, temporary files).
    """
    if not _is_frozen():
        # Development: use project-local Temporary/
        return get_base_dir() / "Temporary"

    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / "PaperQuant" / "data"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "PaperQuant"
    else:
        xdg = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(xdg) / "PaperQuant"


def get_config_dir() -> Path:
    """Get the platform-specific config directory."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / "PaperQuant" / "config"
    elif system == "Darwin":
        return Path.home() / "Library" / "Preferences" / "PaperQuant"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(xdg) / "PaperQuant"


def get_algorithms_dir() -> Path:
    """Get the algorithms storage directory.

    In production, this is inside the data directory so user scripts persist.
    In development, it's the project-local algorithms/ folder.
    """
    if _is_frozen():
        return get_data_dir() / "algorithms"
    return get_base_dir() / "algorithms"


# Resolve all paths
BASE_DIR = get_base_dir()
TEMP_DIR = Path(os.getenv("PAPERQUANT_TEMP_DIR", str(get_data_dir() / "temp" if _is_frozen() else get_base_dir() / "Temporary")))
ALGORITHMS_DIR = Path(os.getenv("PAPERQUANT_ALGORITHMS_DIR", str(get_algorithms_dir())))
CONFIG_DIR = Path(os.getenv("PAPERQUANT_CONFIG_DIR", str(get_config_dir())))
STATE_CACHE_PATH = TEMP_DIR / "state"
LIVE_PRICES_CACHE_PATH = TEMP_DIR / "cache_liveprices"
ORDER_HISTORY_PATH = TEMP_DIR / "order_history.csv"
DATABASE_PATH = TEMP_DIR / "paperquant.db"

for _path in (TEMP_DIR, ALGORITHMS_DIR, CONFIG_DIR):
    _path.mkdir(parents=True, exist_ok=True)
