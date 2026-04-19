"""Central application settings.

Keep values here so a junior developer has one place to adjust timing,
thresholds, file paths, and optional features.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    app_name: str = "Desktop Agent"
    app_version: str = "0.1.0"
    refresh_interval_ms: int = 3000
    snapshot_interval_seconds: int = 60

    high_cpu_threshold: float = 85.0
    high_memory_threshold: float = 85.0
    low_disk_threshold: float = 15.0
    high_process_cpu_threshold: float = 40.0

    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])

    @property
    def data_dir(self) -> Path:
        path = self.base_dir / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def reports_dir(self) -> Path:
        path = self.base_dir / "reports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_path(self) -> Path:
        return self.data_dir / "desktop_agent.db"


settings = AppSettings()
