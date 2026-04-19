"""SQLite storage for snapshots and findings."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from desktop_agent.config.settings import settings


class DatabaseManager:
    """Small wrapper around sqlite3 for app persistence."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    hostname TEXT,
                    os TEXT,
                    cpu_percent REAL,
                    cpu_count_logical INTEGER,
                    memory_percent REAL,
                    memory_used_gb REAL,
                    memory_total_gb REAL,
                    disk_percent REAL,
                    disk_used_gb REAL,
                    disk_total_gb REAL,
                    disk_free_gb REAL,
                    net_bytes_sent INTEGER,
                    net_bytes_recv INTEGER,
                    boot_time TEXT,
                    uptime_hours REAL,
                    health_score INTEGER,
                    summary TEXT
                );

                CREATE TABLE IF NOT EXISTS process_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    pid INTEGER,
                    name TEXT,
                    username TEXT,
                    cpu_percent REAL,
                    memory_mb REAL,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    severity TEXT,
                    category TEXT,
                    message TEXT,
                    recommendation TEXT,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
                );
                """
            )

    def save_snapshot(
        self,
        snapshot: dict[str, Any],
        analysis: dict[str, Any],
        processes: list[dict[str, Any]],
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO snapshots (
                    timestamp, hostname, os, cpu_percent, cpu_count_logical,
                    memory_percent, memory_used_gb, memory_total_gb,
                    disk_percent, disk_used_gb, disk_total_gb, disk_free_gb,
                    net_bytes_sent, net_bytes_recv, boot_time, uptime_hours,
                    health_score, summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot["timestamp"],
                    snapshot["hostname"],
                    snapshot["os"],
                    snapshot["cpu_percent"],
                    snapshot["cpu_count_logical"],
                    snapshot["memory_percent"],
                    snapshot["memory_used_gb"],
                    snapshot["memory_total_gb"],
                    snapshot["disk_percent"],
                    snapshot["disk_used_gb"],
                    snapshot["disk_total_gb"],
                    snapshot["disk_free_gb"],
                    snapshot["net_bytes_sent"],
                    snapshot["net_bytes_recv"],
                    snapshot["boot_time"],
                    snapshot["uptime_hours"],
                    analysis["health_score"],
                    analysis["summary"],
                ),
            )
            snapshot_id = int(cursor.lastrowid)

            conn.executemany(
                """
                INSERT INTO process_samples (snapshot_id, pid, name, username, cpu_percent, memory_mb)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        snapshot_id,
                        item["pid"],
                        item["name"],
                        item["username"],
                        item["cpu_percent"],
                        item["memory_mb"],
                    )
                    for item in processes
                ],
            )

            conn.executemany(
                """
                INSERT INTO findings (snapshot_id, severity, category, message, recommendation)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        snapshot_id,
                        item["severity"],
                        item["category"],
                        item["message"],
                        item["recommendation"],
                    )
                    for item in analysis["findings"]
                ],
            )

            return snapshot_id

    def get_recent_snapshots(self, limit: int = 10) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, cpu_percent, memory_percent, disk_percent, health_score, summary
                FROM snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return rows
