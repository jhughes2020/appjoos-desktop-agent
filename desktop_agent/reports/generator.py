"""Report generation helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from desktop_agent.config.settings import settings


class ReportGenerator:
    """Create markdown and text reports from the latest analysis."""

    def write_markdown_report(
        self,
        snapshot: dict[str, Any],
        analysis: dict[str, Any],
        processes: list[dict[str, Any]],
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = settings.reports_dir / f"desktop_agent_report_{timestamp}.md"

        findings_md = "\n".join(
            f"- **{item['severity'].upper()}** | {item['category']}: {item['message']}  \n  Recommendation: {item['recommendation']}"
            for item in analysis["findings"]
        )

        processes_md = "\n".join(
            f"- {item['name']} (PID {item['pid']}): CPU {item['cpu_percent']:.1f}% | RAM {item['memory_mb']:.0f} MB"
            for item in processes[:5]
        )

        content = f"""# Desktop Agent Report

Generated: {snapshot['timestamp']}

## Overall Summary

{analysis['summary']}

## System Snapshot

- Hostname: {snapshot['hostname']}
- OS: {snapshot['os']}
- CPU usage: {snapshot['cpu_percent']:.1f}%
- Memory usage: {snapshot['memory_percent']:.1f}% ({snapshot['memory_used_gb']} / {snapshot['memory_total_gb']} GB)
- Disk usage: {snapshot['disk_percent']:.1f}% used ({snapshot['disk_free_gb']} GB free)
- Network sent: {snapshot['net_bytes_sent']}
- Network received: {snapshot['net_bytes_recv']}
- Uptime hours: {snapshot['uptime_hours']}

## Findings

{findings_md}

## Top Processes

{processes_md}

## Notes

This version is intentionally rule-based first. It is designed to show clear logic before adding optional AI summaries.
"""
        output_path.write_text(content, encoding="utf-8")
        return output_path
