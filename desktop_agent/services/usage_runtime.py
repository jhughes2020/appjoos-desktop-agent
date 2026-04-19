from __future__ import annotations

import threading
from datetime import datetime

from desktop_agent.services.usage_tracker import UsageTrackerService


class UsageTrackingRuntime:
    """Runs the usage tracker in a background Python thread."""

    def __init__(self, poll_interval: int = 5, idle_threshold: int = 60) -> None:
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._service: UsageTrackerService | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if self.is_running:
            return False

        self._stop_event.clear()
        self._service = UsageTrackerService(
            poll_interval=self.poll_interval,
            idle_threshold=self.idle_threshold,
        )
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self, timeout: float = 3.0) -> bool:
        if not self.is_running:
            return False

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

        with self._lock:
            if self._service is not None:
                self._service._flush_current_session()

        self._thread = None
        self._service = None
        return True

    def tick_now(self) -> bool:
        if self._service is None:
            return False

        with self._lock:
            self._service._tick()
        return True

    def get_live_session_snapshot(self) -> dict | None:
        if self._service is None:
            return None

        with self._lock:
            session = self._service.current_session
            if session is None:
                return None

            now = datetime.now()
            live_seconds = int(session.active_seconds)
            delta = int((now - session.last_observed_at).total_seconds())
            if delta > 0:
                live_seconds += delta

            return {
                "app_key": session.app_key,
                "process_name": session.process_name,
                "exe_path": session.exe_path,
                "window_title": session.window_title,
                "started_at": session.started_at,
                "ended_at": session.ended_at,
                "active_seconds": live_seconds,
                "is_idle_filtered": session.is_idle_filtered,
            }

    def _run_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                with self._lock:
                    if self._service is not None:
                        self._service._tick()
                self._stop_event.wait(self.poll_interval)
        finally:
            with self._lock:
                if self._service is not None:
                    self._service._flush_current_session()
