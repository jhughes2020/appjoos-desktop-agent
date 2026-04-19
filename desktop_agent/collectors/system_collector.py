"""System data collection helpers.

This module talks to the operating system through psutil and turns raw values
into Python dictionaries that are easy for the UI, database, and analyzer to use.
"""

from __future__ import annotations

from datetime import datetime
import platform
from typing import Any

import psutil


class SystemCollector:
    """Collect current system and process metrics."""

    def get_snapshot(self) -> dict[str, Any]:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        boot_time = datetime.fromtimestamp(psutil.boot_time())

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "cpu_percent": psutil.cpu_percent(interval=0.25),
            "cpu_count_logical": psutil.cpu_count(logical=True) or 0,
            "memory_percent": vm.percent,
            "memory_used_gb": round(vm.used / (1024**3), 2),
            "memory_total_gb": round(vm.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "net_bytes_sent": int(net.bytes_sent),
            "net_bytes_recv": int(net.bytes_recv),
            "boot_time": boot_time.isoformat(timespec="seconds"),
            "uptime_hours": round((datetime.now() - boot_time).total_seconds() / 3600, 2),
        }

    def get_top_processes(self, limit: int = 10) -> list[dict[str, Any]]:
        processes: list[dict[str, Any]] = []

        for proc in psutil.process_iter([
            "pid",
            "name",
            "username",
            "cpu_percent",
            "memory_info",
        ]):
            try:
                info = proc.info
                memory_mb = round((info["memory_info"].rss or 0) / (1024**2), 2)
                processes.append(
                    {
                        "pid": info.get("pid", 0),
                        "name": info.get("name") or "unknown",
                        "username": info.get("username") or "unknown",
                        "cpu_percent": float(info.get("cpu_percent") or 0.0),
                        "memory_mb": memory_mb,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by CPU first, then memory.
        processes.sort(key=lambda item: (item["cpu_percent"], item["memory_mb"]), reverse=True)
        return processes[:limit]
