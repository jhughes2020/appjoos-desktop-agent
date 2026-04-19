from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from desktop_agent.collectors.activity_windows import (
    ForegroundApp,
    WindowsActivityCollector,
)
from desktop_agent.storage.migrate_usage import migrate


@dataclass
class ActiveSession:
    app_key: str
    process_name: str
    exe_path: str
    window_title: str
    started_at: str
    ended_at: str
    active_seconds: int
    is_idle_filtered: int
    last_observed_at: datetime


class UsageTrackerService:
    def __init__(self, poll_interval: int = 5, idle_threshold: int = 60) -> None:
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.collector = WindowsActivityCollector()
        self.current_session: ActiveSession | None = None
        self.db_path = self._get_db_path()

        # Safety: make sure the usage tables exist.
        migrate()

    def _get_db_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[2]
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "desktop_agent.db"

    def run(self) -> None:
        print("Usage tracker started.")
        print(f"Poll interval: {self.poll_interval}s")
        print(f"Idle threshold: {self.idle_threshold}s")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                self._tick()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\nStopping usage tracker...")
            self._flush_current_session()
            print("Usage tracker stopped.")

    def _tick(self) -> None:
        now = datetime.now()
        idle_seconds = self.collector.get_idle_seconds()
        app = self.collector.get_foreground_app()

        # If user is idle or we cannot detect an app, close current session.
        if idle_seconds >= self.idle_threshold or app is None:
            if self.current_session is not None:
                self.current_session.is_idle_filtered = 1 if idle_seconds >= self.idle_threshold else 0
                self.current_session.ended_at = now.isoformat(timespec="seconds")
                self._save_session(self.current_session)
                print(
                    f"[CLOSE] {self.current_session.process_name} "
                    f"active_seconds={self.current_session.active_seconds} "
                    f"idle_filtered={self.current_session.is_idle_filtered}"
                )
                self.current_session = None
            return

        # Keep catalog fresh.
        self._upsert_app_catalog(app, now)

        # Start first session.
        if self.current_session is None:
            self.current_session = self._new_session(app, now)
            print(f"[OPEN ] {app.process_name} | {app.window_title}")
            return

        # App changed -> close old session, open new one.
        if app.app_key != self.current_session.app_key:
            self._add_elapsed_time(now)
            self.current_session.ended_at = now.isoformat(timespec="seconds")
            self._save_session(self.current_session)
            print(
                f"[SWAP ] {self.current_session.process_name} "
                f"active_seconds={self.current_session.active_seconds}"
            )

            self.current_session = self._new_session(app, now)
            print(f"[OPEN ] {app.process_name} | {app.window_title}")
            return

        # Same app still active -> keep extending session.
        self._add_elapsed_time(now)
        self.current_session.process_name = app.process_name
        self.current_session.exe_path = app.exe_path
        self.current_session.window_title = app.window_title
        self.current_session.ended_at = now.isoformat(timespec="seconds")

    def _new_session(self, app: ForegroundApp, now: datetime) -> ActiveSession:
        timestamp = now.isoformat(timespec="seconds")
        return ActiveSession(
            app_key=app.app_key,
            process_name=app.process_name,
            exe_path=app.exe_path,
            window_title=app.window_title,
            started_at=timestamp,
            ended_at=timestamp,
            active_seconds=0,
            is_idle_filtered=0,
            last_observed_at=now,
        )

    def _add_elapsed_time(self, now: datetime) -> None:
        if self.current_session is None:
            return

        delta = int((now - self.current_session.last_observed_at).total_seconds())
        if delta > 0:
            self.current_session.active_seconds += delta
        self.current_session.last_observed_at = now

    def _upsert_app_catalog(self, app: ForegroundApp, now: datetime) -> None:
        timestamp = now.isoformat(timespec="seconds")

        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO app_catalog (
                    app_key, process_name, exe_path, first_seen_at, last_seen_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    app.app_key,
                    app.process_name,
                    app.exe_path,
                    timestamp,
                    timestamp,
                ),
            )

            conn.execute(
                """
                UPDATE app_catalog
                SET process_name = ?,
                    exe_path = ?,
                    last_seen_at = ?
                WHERE app_key = ?
                """,
                (
                    app.process_name,
                    app.exe_path,
                    timestamp,
                    app.app_key,
                ),
            )
            conn.commit()

    def _save_session(self, session: ActiveSession) -> None:
        # Skip zero-length sessions.
        if session.active_seconds <= 0:
            return

        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.execute(
                """
                INSERT INTO app_sessions (
                    app_key,
                    process_name,
                    exe_path,
                    window_title,
                    started_at,
                    ended_at,
                    active_seconds,
                    is_idle_filtered
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.app_key,
                    session.process_name,
                    session.exe_path,
                    session.window_title,
                    session.started_at,
                    session.ended_at,
                    session.active_seconds,
                    session.is_idle_filtered,
                ),
            )
            conn.commit()

    def _flush_current_session(self) -> None:
        if self.current_session is None:
            return

        now = datetime.now()
        self._add_elapsed_time(now)
        self.current_session.ended_at = now.isoformat(timespec="seconds")
        self._save_session(self.current_session)
        self.current_session = None


if __name__ == "__main__":
    tracker = UsageTrackerService(poll_interval=5, idle_threshold=60)
    tracker.run()