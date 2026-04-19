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
            CREATE TABLE IF NOT EXISTS speedtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                ping_ms REAL,
                download_mbps REAL,
                upload_mbps REAL,
                packet_loss REAL,
                isp TEXT,
                external_ip TEXT,
                server_name TEXT,
                server_id TEXT,
                server_location TEXT,
                result_url TEXT,
                error_message TEXT,
                raw_json TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_speedtest_results_timestamp
            ON speedtest_results(timestamp);
            """
        )
        conn.commit()
        print(f"Speed test migration complete: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()