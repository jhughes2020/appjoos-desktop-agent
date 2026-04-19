from __future__ import annotations

import threading

from desktop_agent.services.network_tracker import PassiveNetworkTracker


class NetworkTrackingRuntime:
    """Runs the passive network tracker in a background Python thread."""

    def __init__(self, poll_interval: int = 2) -> None:
        self.poll_interval = poll_interval

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._service: PassiveNetworkTracker | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if self.is_running:
            return False

        self._stop_event.clear()
        self._service = PassiveNetworkTracker(poll_interval=self.poll_interval)

        # Prime baseline immediately so the first manual refresh feels better.
        self._service._tick(min_elapsed=0.0)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self, timeout: float = 3.0) -> bool:
        if not self.is_running:
            return False

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

        self._thread = None
        self._service = None
        return True

    def tick_now(self) -> bool:
        if self._service is None:
            return False

        with self._lock:
            return bool(self._service._tick(min_elapsed=0.25))

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                if self._service is not None:
                    self._service._tick(min_elapsed=0.75)
            self._stop_event.wait(self.poll_interval)
