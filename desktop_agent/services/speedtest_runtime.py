from __future__ import annotations

import threading
from dataclasses import asdict

from desktop_agent.services.speedtest_runner import SpeedTestRunner


class SpeedTestRuntime:
    """Runs a user-triggered speed test in a background thread."""

    def __init__(self, executable: str = "speedtest") -> None:
        self.executable = executable
        self._runner = SpeedTestRunner(executable=executable)
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._status = "idle"
        self._last_result: dict | None = None
        self._last_error: str | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def status(self) -> str:
        return self._status

    @property
    def last_result(self) -> dict | None:
        return self._last_result

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self) -> bool:
        if self.is_running:
            return False

        self._last_error = None
        self._status = "running"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def _run(self) -> None:
        try:
            result = self._runner.run_test()
            with self._lock:
                self._last_result = asdict(result)
                if result.status == "success":
                    self._status = "success"
                    self._last_error = None
                else:
                    self._status = "error"
                    self._last_error = result.error_message
        except Exception as exc:
            with self._lock:
                self._status = "error"
                self._last_error = str(exc)