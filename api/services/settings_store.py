from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

DEFAULT_SETTINGS = {
    "currency": "USD", "theme": "dark", "simulated_latency_ms": 0,
    "commission_percent": 0.0, "leverage": 1, "auto_clear_logs": True,
    "system_alerts": True, "sound_effects": False, "terminal_font_size": 14,
}


class SettingsStore:
    def __init__(self, config_dir: str | Path | None = None):
        directory = Path(config_dir or Path.home() / ".paperquant")
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "settings.json"
        self._lock = Lock()
        self._settings = self._load()

    def _load(self) -> dict:
        try:
            return {**DEFAULT_SETTINGS, **json.loads(self.path.read_text())}
        except (FileNotFoundError, json.JSONDecodeError):
            return dict(DEFAULT_SETTINGS)

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._settings)

    def update(self, updates: dict) -> dict:
        with self._lock:
            self._settings.update({k: v for k, v in updates.items() if k in DEFAULT_SETTINGS and v is not None})
            self.path.write_text(json.dumps(self._settings, indent=2))
            return dict(self._settings)

