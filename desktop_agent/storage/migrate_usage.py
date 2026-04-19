from __future__ import annotations

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """
    Assumes the current project stores the DB in:
    data/desktop_agent.db
    """
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
            CREATE TABLE IF NOT EXISTS app_catalog (
                app_key TEXT PRIMARY KEY,
                process_name TEXT,
                exe_path TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_key TEXT NOT NULL,
                process_name TEXT,
                exe_path TEXT,
                window_title TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                active_seconds INTEGER NOT NULL DEFAULT 0,
                is_idle_filtered INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (app_key) REFERENCES app_catalog(app_key)
            );

            CREATE INDEX IF NOT EXISTS idx_app_sessions_started_at
            ON app_sessions(started_at);

            CREATE INDEX IF NOT EXISTS idx_app_sessions_app_key
            ON app_sessions(app_key);

            CREATE INDEX IF NOT EXISTS idx_app_catalog_last_seen_at
            ON app_catalog(last_seen_at);
            """
        )
        conn.commit()
        print(f"Usage migration complete: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()