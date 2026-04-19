from __future__ import annotations

import sqlite3
from pathlib import Path


class UsageRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = project_root / "data" / "desktop_agent.db"
        self.db_path = Path(db_path)

    def get_top_apps(self, days: int = 7, limit: int = 10) -> list[dict]:
        query = """
            SELECT
                app_key,
                process_name,
                exe_path,
                SUM(active_seconds) AS total_seconds
            FROM app_sessions
            WHERE datetime(started_at) >= datetime('now', ?)
            GROUP BY app_key, process_name, exe_path
            ORDER BY total_seconds DESC
            LIMIT ?
        """

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, (f"-{days} days", limit)).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "app_key": row[0],
                    "process_name": row[1],
                    "exe_path": row[2],
                    "total_seconds": row[3],
                }
            )
        return results

    def get_top_apps_chart_data(self, days: int = 7, limit: int = 5) -> list[dict]:
        rows = self.get_top_apps(days=days, limit=limit)
        results = []

        for row in rows:
            results.append(
                {
                    "label": row["process_name"],
                    "seconds": int(row["total_seconds"]),
                    "minutes": round(int(row["total_seconds"]) / 60, 2),
                }
            )

        return results

    def get_daily_usage_trend(self, days: int = 7) -> list[dict]:
        query = """
            WITH RECURSIVE day_series(day_offset, day_value) AS (
                SELECT 0, date('now', ?)
                UNION ALL
                SELECT day_offset + 1, date(day_value, '+1 day')
                FROM day_series
                WHERE day_offset < ?
            )
            SELECT
                ds.day_value AS usage_day,
                COALESCE(SUM(s.active_seconds), 0) AS total_seconds
            FROM day_series ds
            LEFT JOIN app_sessions s
                ON date(s.started_at) = ds.day_value
            GROUP BY ds.day_value
            ORDER BY ds.day_value ASC
        """

        start_offset = f"-{days - 1} days"

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, (start_offset, days - 1)).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "day": row[0],
                    "total_seconds": int(row[1]),
                    "minutes": round(int(row[1]) / 60, 2),
                }
            )
        return results

    def get_unused_apps(self, days: int = 14, limit: int = 100) -> list[dict]:
        query = """
            SELECT
                app_key,
                process_name,
                exe_path,
                first_seen_at,
                last_seen_at
            FROM app_catalog
            WHERE datetime(last_seen_at) < datetime('now', ?)
            ORDER BY datetime(last_seen_at) ASC
            LIMIT ?
        """

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, (f"-{days} days", limit)).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "app_key": row[0],
                    "process_name": row[1],
                    "exe_path": row[2],
                    "first_seen_at": row[3],
                    "last_seen_at": row[4],
                }
            )
        return results

    def get_usage_counts(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            tracked_apps = conn.execute(
                "SELECT COUNT(*) FROM app_catalog"
            ).fetchone()[0]

            session_count = conn.execute(
                "SELECT COUNT(*) FROM app_sessions"
            ).fetchone()[0]

            tracked_seconds = conn.execute(
                "SELECT COALESCE(SUM(active_seconds), 0) FROM app_sessions"
            ).fetchone()[0]

        return {
            "tracked_apps": tracked_apps,
            "session_count": session_count,
            "tracked_seconds": tracked_seconds,
        }


if __name__ == "__main__":
    repo = UsageRepository()

    print("TOP APPS (7 DAYS)")
    for row in repo.get_top_apps(days=7, limit=10):
        print(row)

    print("\nTOP APPS CHART DATA")
    for row in repo.get_top_apps_chart_data(days=7, limit=5):
        print(row)

    print("\nDAILY USAGE TREND (7 DAYS)")
    for row in repo.get_daily_usage_trend(days=7):
        print(row)

    print("\nUNUSED APPS (14 DAYS)")
    for row in repo.get_unused_apps(days=14, limit=20):
        print(row)

    print("\nUNUSED APPS (30 DAYS)")
    for row in repo.get_unused_apps(days=30, limit=20):
        print(row)

    print("\nCOUNTS")
    print(repo.get_usage_counts())