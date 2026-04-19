from __future__ import annotations

import sqlite3
from pathlib import Path


class NetworkRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = project_root / "data" / "desktop_agent.db"
        self.db_path = Path(db_path)

    def get_latest_sample(self) -> dict | None:
        query = """
            SELECT
                timestamp,
                sample_seconds,
                bytes_sent,
                bytes_recv,
                upload_bps,
                download_bps,
                upload_mbps,
                download_mbps
            FROM network_samples
            ORDER BY id DESC
            LIMIT 1
        """

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(query).fetchone()

        if row is None:
            return None

        return {
            "timestamp": row[0],
            "sample_seconds": float(row[1]),
            "bytes_sent": int(row[2]),
            "bytes_recv": int(row[3]),
            "upload_bps": float(row[4]),
            "download_bps": float(row[5]),
            "upload_mbps": float(row[6]),
            "download_mbps": float(row[7]),
        }

    def get_recent_samples(self, limit: int = 20) -> list[dict]:
        query = """
            SELECT
                timestamp,
                download_mbps,
                upload_mbps,
                bytes_recv,
                bytes_sent
            FROM network_samples
            ORDER BY id DESC
            LIMIT ?
        """

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, (limit,)).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "timestamp": row[0],
                    "download_mbps": float(row[1]),
                    "upload_mbps": float(row[2]),
                    "bytes_recv": int(row[3]),
                    "bytes_sent": int(row[4]),
                }
            )
        return results

    def get_summary(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            sample_count = conn.execute(
                "SELECT COUNT(*) FROM network_samples"
            ).fetchone()[0]

            peak_download = conn.execute(
                "SELECT COALESCE(MAX(download_mbps), 0) FROM network_samples"
            ).fetchone()[0]

            peak_upload = conn.execute(
                "SELECT COALESCE(MAX(upload_mbps), 0) FROM network_samples"
            ).fetchone()[0]

            avg_download = conn.execute(
                "SELECT COALESCE(AVG(download_mbps), 0) FROM network_samples"
            ).fetchone()[0]

            avg_upload = conn.execute(
                "SELECT COALESCE(AVG(upload_mbps), 0) FROM network_samples"
            ).fetchone()[0]

        return {
            "sample_count": int(sample_count),
            "peak_download_mbps": float(peak_download),
            "peak_upload_mbps": float(peak_upload),
            "avg_download_mbps": float(avg_download),
            "avg_upload_mbps": float(avg_upload),
        }


if __name__ == "__main__":
    repo = NetworkRepository()

    print("LATEST SAMPLE")
    print(repo.get_latest_sample())

    print("\nSUMMARY")
    print(repo.get_summary())

    print("\nRECENT SAMPLES")
    for row in repo.get_recent_samples(limit=10):
        print(row)