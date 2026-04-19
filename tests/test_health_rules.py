"""Simple unit tests for the deterministic rules."""

from desktop_agent.analyzers.health_rules import HealthAnalyzer


analyzer = HealthAnalyzer()


def test_high_memory_creates_critical_finding() -> None:
    snapshot = {
        "cpu_percent": 10,
        "memory_percent": 92,
        "disk_percent": 40,
    }
    processes = [{"pid": 1234, "name": "python.exe", "cpu_percent": 5.0, "memory_mb": 120.0}]

    result = analyzer.analyze(snapshot, processes)

    severities = [item["severity"] for item in result["findings"]]
    assert "critical" in severities
    assert result["health_score"] < 100


def test_stable_system_returns_info_finding() -> None:
    snapshot = {
        "cpu_percent": 10,
        "memory_percent": 30,
        "disk_percent": 20,
    }
    processes = [{"pid": 1, "name": "system", "cpu_percent": 1.0, "memory_mb": 50.0}]

    result = analyzer.analyze(snapshot, processes)

    assert result["findings"][0]["severity"] == "info"
