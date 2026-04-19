from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SpeedTestResult:
    timestamp: str
    status: str
    ping_ms: float | None
    download_mbps: float | None
    upload_mbps: float | None
    packet_loss: float | None
    isp: str | None
    external_ip: str | None
    server_name: str | None
    server_id: str | None
    server_location: str | None
    result_url: str | None
    error_message: str | None
    raw_json: str | None


class SpeedTestRunner:
    """
    Runs an external speed test CLI and stores results in SQLite.

    This version assumes an installed CLI executable named `speedtest`
    is available on PATH, or that you pass an explicit executable path.
    """

    def __init__(self, executable: str = "speedtest") -> None:
        self.executable = executable
        self.db_path = self._get_db_path()

    def _get_db_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[2]
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "desktop_agent.db"

    def is_available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run_test(self, timeout_seconds: int = 180) -> SpeedTestResult:
        timestamp = datetime.now().isoformat(timespec="seconds")

        if not self.is_available():
            result = SpeedTestResult(
                timestamp=timestamp,
                status="error",
                ping_ms=None,
                download_mbps=None,
                upload_mbps=None,
                packet_loss=None,
                isp=None,
                external_ip=None,
                server_name=None,
                server_id=None,
                server_location=None,
                result_url=None,
                error_message=f"Speedtest executable '{self.executable}' was not found on PATH.",
                raw_json=None,
            )
            self._save_result(result)
            return result

        cmd = [
            self.executable,
            "--accept-license",
            "--accept-gdpr",
            "--format=json",
        ]

        try:
            run_kwargs = {
                "capture_output": True,
                "text": True,
                "timeout": timeout_seconds,
                "check": False,
            }

            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                run_kwargs["startupinfo"] = startupinfo

            completed = subprocess.run(cmd, **run_kwargs)

        except subprocess.TimeoutExpired:
            result = SpeedTestResult(
                timestamp=timestamp,
                status="error",
                ping_ms=None,
                download_mbps=None,
                upload_mbps=None,
                packet_loss=None,
                isp=None,
                external_ip=None,
                server_name=None,
                server_id=None,
                server_location=None,
                result_url=None,
                error_message=f"Speed test timed out after {timeout_seconds} seconds.",
                raw_json=None,
            )
            self._save_result(result)
            return result

        except Exception as exc:
            result = SpeedTestResult(
                timestamp=timestamp,
                status="error",
                ping_ms=None,
                download_mbps=None,
                upload_mbps=None,
                packet_loss=None,
                isp=None,
                external_ip=None,
                server_name=None,
                server_id=None,
                server_location=None,
                result_url=None,
                error_message=str(exc),
                raw_json=None,
            )
            self._save_result(result)
            return result

        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()

        if completed.returncode != 0:
            result = SpeedTestResult(
                timestamp=timestamp,
                status="error",
                ping_ms=None,
                download_mbps=None,
                upload_mbps=None,
                packet_loss=None,
                isp=None,
                external_ip=None,
                server_name=None,
                server_id=None,
                server_location=None,
                result_url=None,
                error_message=stderr or f"Speed test failed with exit code {completed.returncode}.",
                raw_json=stdout or None,
            )
            self._save_result(result)
            return result

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            result = SpeedTestResult(
                timestamp=timestamp,
                status="error",
                ping_ms=None,
                download_mbps=None,
                upload_mbps=None,
                packet_loss=None,
                isp=None,
                external_ip=None,
                server_name=None,
                server_id=None,
                server_location=None,
                result_url=None,
                error_message="Speed test completed but did not return valid JSON.",
                raw_json=stdout or None,
            )
            self._save_result(result)
            return result

        result = self._parse_payload(timestamp=timestamp, payload=payload, raw_json=stdout)
        self._save_result(result)
        return result

    def _parse_payload(self, timestamp: str, payload: dict, raw_json: str) -> SpeedTestResult:
        ping_ms = self._safe_float(payload.get("ping", {}).get("latency"))

        download_bandwidth = self._safe_float(payload.get("download", {}).get("bandwidth"))
        upload_bandwidth = self._safe_float(payload.get("upload", {}).get("bandwidth"))

        download_mbps = (download_bandwidth * 8 / 1_000_000) if download_bandwidth is not None else None
        upload_mbps = (upload_bandwidth * 8 / 1_000_000) if upload_bandwidth is not None else None

        packet_loss = self._safe_float(payload.get("packetLoss"))

        isp = self._safe_str(payload.get("isp"))
        external_ip = self._safe_str(payload.get("interface", {}).get("externalIp"))

        server = payload.get("server", {}) or {}
        server_name = self._safe_str(server.get("name"))
        server_id = self._safe_str(server.get("id"))
        server_location = self._join_location(server.get("location"), server.get("country"))

        result_url = self._safe_str(payload.get("result", {}).get("url"))

        return SpeedTestResult(
            timestamp=timestamp,
            status="success",
            ping_ms=ping_ms,
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            packet_loss=packet_loss,
            isp=isp,
            external_ip=external_ip,
            server_name=server_name,
            server_id=server_id,
            server_location=server_location,
            result_url=result_url,
            error_message=None,
            raw_json=raw_json,
        )

    def _save_result(self, result: SpeedTestResult) -> None:
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.execute(
                """
                INSERT INTO speedtest_results (
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
                    error_message,
                    raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.timestamp,
                    result.status,
                    result.ping_ms,
                    result.download_mbps,
                    result.upload_mbps,
                    result.packet_loss,
                    result.isp,
                    result.external_ip,
                    result.server_name,
                    result.server_id,
                    result.server_location,
                    result.result_url,
                    result.error_message,
                    result.raw_json,
                ),
            )
            conn.commit()

    def _safe_float(self, value) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _safe_str(self, value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _join_location(self, location, country) -> str | None:
        parts = [self._safe_str(location), self._safe_str(country)]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else None


if __name__ == "__main__":
    runner = SpeedTestRunner()
    result = runner.run_test()

    print("SPEED TEST RESULT\n")
    print(f"Status: {result.status}")
    print(f"Ping: {result.ping_ms}")
    print(f"Download Mbps: {result.download_mbps}")
    print(f"Upload Mbps: {result.upload_mbps}")
    print(f"ISP: {result.isp}")
    print(f"External IP: {result.external_ip}")
    print(f"Server: {result.server_name}")
    print(f"Error: {result.error_message}")