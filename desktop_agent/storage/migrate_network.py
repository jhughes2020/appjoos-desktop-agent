from __future__ import annotations

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "desktop_agent.db"


def migrate() -> None:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)

    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS network_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sample_seconds REAL NOT NULL DEFAULT 0,
                bytes_sent INTEGER NOT NULL DEFAULT 0,
                bytes_recv INTEGER NOT NULL DEFAULT 0,
                upload_bps REAL NOT NULL DEFAULT 0,
                download_bps REAL NOT NULL DEFAULT 0,
                upload_mbps REAL NOT NULL DEFAULT 0,
                download_mbps REAL NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_network_samples_timestamp
            ON network_samples(timestamp);
            """
        )
        conn.commit()
        print(f"Network migration complete: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()