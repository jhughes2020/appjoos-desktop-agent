from __future__ import annotations

import json
from pathlib import Path


class AppSettings:
    DEFAULTS = {
        "auto_start_usage_tracking": False,
        "start_minimized_to_tray": False,
        "minimize_to_tray": True,
    }

    def __init__(self, settings_path: str | Path | None = None) -> None:
        if settings_path is None:
            project_root = Path(__file__).resolve().parents[2]
            data_dir = project_root / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            settings_path = data_dir / "app_settings.json"

        self.settings_path = Path(settings_path)
        self._settings = self._load()

    def _load(self) -> dict:
        if not self.settings_path.exists():
            return dict(self.DEFAULTS)

        try:
            with self.settings_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return dict(self.DEFAULTS)

        merged = dict(self.DEFAULTS)
        merged.update(data)
        return merged

    def save(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def get_auto_start_usage_tracking(self) -> bool:
        return bool(self._settings.get("auto_start_usage_tracking", False))

    def set_auto_start_usage_tracking(self, enabled: bool) -> None:
        self._settings["auto_start_usage_tracking"] = bool(enabled)
        self.save()

    def get_start_minimized_to_tray(self) -> bool:
        return bool(self._settings.get("start_minimized_to_tray", False))

    def set_start_minimized_to_tray(self, enabled: bool) -> None:
        self._settings["start_minimized_to_tray"] = bool(enabled)
        self.save()

    def get_minimize_to_tray(self) -> bool:
        return bool(self._settings.get("minimize_to_tray", True))

    def set_minimize_to_tray(self, enabled: bool) -> None:
        self._settings["minimize_to_tray"] = bool(enabled)
        self.save()