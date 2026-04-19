"""Deterministic health analysis rules.

Version 0.1 is intentionally rule based. We only let the AI rewrite or summarize
findings later; the facts and severity come from clear thresholds.
"""

from __future__ import annotations

from typing import Any

from desktop_agent.config.settings import settings


SEVERITY_ORDER = {"info": 1, "warning": 2, "critical": 3}


class HealthAnalyzer:
    """Convert a snapshot plus process list into findings and a health score."""

    def analyze(
        self,
        snapshot: dict[str, Any],
        processes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        findings: list[dict[str, str]] = []

        cpu_percent = float(snapshot["cpu_percent"])
        memory_percent = float(snapshot["memory_percent"])
        disk_free_percent = 100.0 - float(snapshot["disk_percent"])

        if cpu_percent >= settings.high_cpu_threshold:
            findings.append(
                {
                    "severity": "warning",
                    "category": "CPU",
                    "message": f"CPU usage is high at {cpu_percent:.1f}%.",
                    "recommendation": "Close heavy applications or review the top process list.",
                }
            )

        if memory_percent >= settings.high_memory_threshold:
            findings.append(
                {
                    "severity": "critical",
                    "category": "Memory",
                    "message": f"Memory usage is high at {memory_percent:.1f}%.",
                    "recommendation": "Close memory-heavy apps and check whether one process is growing over time.",
                }
            )

        if disk_free_percent <= settings.low_disk_threshold:
            findings.append(
                {
                    "severity": "warning",
                    "category": "Disk",
                    "message": f"Free disk space is low at {disk_free_percent:.1f}% remaining.",
                    "recommendation": "Delete unneeded files or move large files off the primary drive.",
                }
            )

        if processes:
            top_proc = max(processes, key=lambda item: (item["cpu_percent"], item["memory_mb"]))
            if top_proc["cpu_percent"] >= settings.high_process_cpu_threshold:
                findings.append(
                    {
                        "severity": "info",
                        "category": "Process",
                        "message": (
                            f"Top active process is {top_proc['name']} (PID {top_proc['pid']}) "
                            f"using {top_proc['cpu_percent']:.1f}% CPU."
                        ),
                        "recommendation": "Confirm the process is expected. If not, investigate or end it carefully.",
                    }
                )

            if top_proc["memory_mb"] >= 1500:
                findings.append(
                    {
                        "severity": "info",
                        "category": "Process",
                        "message": (
                            f"Top memory process is {top_proc['name']} (PID {top_proc['pid']}) "
                            f"using {top_proc['memory_mb']:.0f} MB RAM."
                        ),
                        "recommendation": "If the machine feels slow, this is a good process to review first.",
                    }
                )

        if not findings:
            findings.append(
                {
                    "severity": "info",
                    "category": "General",
                    "message": "System health looks stable right now.",
                    "recommendation": "Keep monitoring over time so you can compare today with future snapshots.",
                }
            )

        score = self._score_from_findings(findings)
        summary = self._build_summary(score, findings)

        return {
            "health_score": score,
            "summary": summary,
            "findings": findings,
        }

    def _score_from_findings(self, findings: list[dict[str, str]]) -> int:
        score = 100
        for item in findings:
            severity = item["severity"]
            if severity == "critical":
                score -= 25
            elif severity == "warning":
                score -= 15
            else:
                score -= 5
        return max(score, 0)

    def _build_summary(self, score: int, findings: list[dict[str, str]]) -> str:
        highest = max(findings, key=lambda item: SEVERITY_ORDER[item["severity"]])
        return (
            f"Health score: {score}/100. "
            f"Top concern: {highest['category']} - {highest['message']}"
        )
