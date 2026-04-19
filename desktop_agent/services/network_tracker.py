from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psutil

from desktop_agent.storage.migrate_network import migrate


@dataclass
class NetworkSample:
    timestamp: str
    sample_seconds: float
    bytes_sent: int
    bytes_recv: int
    upload_bps: float
    download_bps: float
    upload_mbps: float
    download_mbps: float


class PassiveNetworkTracker:
    def __init__(self, poll_interval: int = 5) -> None:
        self.poll_interval = poll_interval
        self.db_path = self._get_db_path()
        self._previous_counters = None
        self._previous_time: datetime | None = None

        migrate()

    def _get_db_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[2]
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "desktop_agent.db"

    def run(self) -> None:
        print("Passive network tracker started.")
        print(f"Poll interval: {self.poll_interval}s")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                self._tick(min_elapsed=1.0)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\nStopping passive network tracker...")
            print("Passive network tracker stopped.")

    def _tick(self, min_elapsed: float = 1.0) -> bool:
        now = datetime.now()
        counters = psutil.net_io_counters()

        if self._previous_counters is None or self._previous_time is None:
            self._previous_counters = counters
            self._previous_time = now
            print("[BASE ] Baseline network counters captured.")
            return False

        elapsed = max((now - self._previous_time).total_seconds(), 0.001)

        if elapsed < min_elapsed:
            return False

        sent_delta = max(counters.bytes_sent - self._previous_counters.bytes_sent, 0)
        recv_delta = max(counters.bytes_recv - self._previous_counters.bytes_recv, 0)

        upload_bps = sent_delta / elapsed
        download_bps = recv_delta / elapsed

        upload_mbps = (upload_bps * 8) / 1_000_000
        download_mbps = (download_bps * 8) / 1_000_000

        sample = NetworkSample(
            timestamp=now.isoformat(timespec="seconds"),
            sample_seconds=elapsed,
            bytes_sent=int(counters.bytes_sent),
            bytes_recv=int(counters.bytes_recv),
            upload_bps=upload_bps,
            download_bps=download_bps,
            upload_mbps=upload_mbps,
            download_mbps=download_mbps,
        )

        self._save_sample(sample)

        print(
            f"[SAVE ] {sample.timestamp} | "
            f"Down {sample.download_mbps:.3f} Mbps | "
            f"Up {sample.upload_mbps:.3f} Mbps"
        )

        self._previous_counters = counters
        self._previous_time = now
        return True

    def _save_sample(self, sample: NetworkSample) -> None:
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.execute(
                """
                INSERT INTO network_samples (
                    timestamp,
                    sample_seconds,
                    bytes_sent,
                    bytes_recv,
                    upload_bps,
                    download_bps,
                    upload_mbps,
                    download_mbps
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample.timestamp,
                    sample.sample_seconds,
                    sample.bytes_sent,
                    sample.bytes_recv,
                    sample.upload_bps,
                    sample.download_bps,
                    sample.upload_mbps,
                    sample.download_mbps,
                ),
            )
            conn.commit()


if __name__ == "__main__":
    tracker = PassiveNetworkTracker(poll_interval=5)
    tracker.run()