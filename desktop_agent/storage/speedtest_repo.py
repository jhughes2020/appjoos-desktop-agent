from __future__ import annotations

import sqlite3
from pathlib import Path


class SpeedTestRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = project_root / "data" / "desktop_agent.db"
        self.db_path = Path(db_path)

    def get_recent_results(self, limit: int = 10) -> list[dict]:
        query = """
            SELECT
                timestamp,
                status,
                ping_ms,
                download_mbps,
                upload_mbps,
                packet_loss,
                isp,
                external_ip,
                server_name,
                server_id,
                server_location,
                result_url,
                error_message
            FROM speedtest_results
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
                    "status": row[1],
                    "ping_ms": row[2],
                    "download_mbps": row[3],
                    "upload_mbps": row[4],
                    "packet_loss": row[5],
                    "isp": row[6],
                    "external_ip": row[7],
                    "server_name": row[8],
                    "server_id": row[9],
                    "server_location": row[10],
                    "result_url": row[11],
                    "error_message": row[12],
                }
            )
        return results

    def get_latest_result(self) -> dict | None:
        rows = self.get_recent_results(limit=1)
        return rows[0] if rows else None

    def get_recent_successful_results(self, limit: int = 10) -> list[dict]:
        query = """
            SELECT
                timestamp,
                status,
                ping_ms,
                download_mbps,
                upload_mbps,
                packet_loss,
                isp,
                external_ip,
                server_name,
                server_id,
                server_location,
                result_url,
                error_message
            FROM speedtest_results
            WHERE status = 'success'
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
                    "status": row[1],
                    "ping_ms": row[2],
                    "download_mbps": row[3],
                    "upload_mbps": row[4],
                    "packet_loss": row[5],
                    "isp": row[6],
                    "external_ip": row[7],
                    "server_name": row[8],
                    "server_id": row[9],
                    "server_location": row[10],
                    "result_url": row[11],
                    "error_message": row[12],
                }
            )
        return results

    def get_latest_successful_result(self) -> dict | None:
        rows = self.get_recent_successful_results(limit=1)
        return rows[0] if rows else None

    def get_previous_successful_result(self) -> dict | None:
        rows = self.get_recent_successful_results(limit=2)
        return rows[1] if len(rows) >= 2 else None

    def get_chart_data(self, limit: int = 7) -> list[dict]:
        rows = list(reversed(self.get_recent_successful_results(limit=limit)))
        results = []

        for row in rows:
            results.append(
                {
                    "timestamp": row["timestamp"],
                    "download_mbps": float(row["download_mbps"] or 0),
                    "upload_mbps": float(row["upload_mbps"] or 0),
                    "ping_ms": float(row["ping_ms"] or 0),
                }
            )
        return results

    def get_summary(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total_tests = conn.execute(
                "SELECT COUNT(*) FROM speedtest_results"
            ).fetchone()[0]

            success_count = conn.execute(
                "SELECT COUNT(*) FROM speedtest_results WHERE status = 'success'"
            ).fetchone()[0]

            latest_success = conn.execute(
                """
                SELECT timestamp, ping_ms, download_mbps, upload_mbps
                FROM speedtest_results
                WHERE status = 'success'
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        summary = {
            "total_tests": int(total_tests),
            "success_count": int(success_count),
            "latest_success": None,
        }

        if latest_success:
            summary["latest_success"] = {
                "timestamp": latest_success[0],
                "ping_ms": latest_success[1],
                "download_mbps": latest_success[2],
                "upload_mbps": latest_success[3],
            }

        return summary


if __name__ == "__main__":
    repo = SpeedTestRepository()

    print("SUMMARY")
    print(repo.get_summary())

    print("\nRECENT RESULTS")
    for row in repo.get_recent_results(limit=5):
        print(row)

    print("\nCHART DATA")
    for row in repo.get_chart_data(limit=5):
        print(row)