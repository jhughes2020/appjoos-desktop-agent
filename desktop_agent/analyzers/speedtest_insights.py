from __future__ import annotations

from dataclasses import dataclass

from desktop_agent.storage.speedtest_repo import SpeedTestRepository


@dataclass
class SpeedTestInsight:
    severity: str
    title: str
    message: str
    recommendation: str


class SpeedTestInsightsAnalyzer:
    def __init__(self, repo: SpeedTestRepository | None = None) -> None:
        self.repo = repo or SpeedTestRepository()

    def analyze(self) -> dict:
        latest = self.repo.get_latest_successful_result()
        previous = self.repo.get_previous_successful_result()
        summary = self.repo.get_summary()

        insights: list[SpeedTestInsight] = []

        if latest is None:
            insights.append(
                SpeedTestInsight(
                    severity="info",
                    title="No successful speed test yet",
                    message="No successful active speed test results are available yet.",
                    recommendation="Run a speed test from the Network tab to build a baseline.",
                )
            )
            return self._build_result(summary, latest, previous, insights)

        ping = float(latest["ping_ms"] or 0)
        download = float(latest["download_mbps"] or 0)
        upload = float(latest["upload_mbps"] or 0)

        if ping <= 20:
            insights.append(
                SpeedTestInsight(
                    severity="info",
                    title="Latency looks healthy",
                    message=f"Latest ping is {ping:.3f} ms, which is very good for most normal use cases.",
                    recommendation="Latency currently looks strong for browsing, calls, and general responsiveness.",
                )
            )
        elif ping <= 50:
            insights.append(
                SpeedTestInsight(
                    severity="info",
                    title="Latency looks acceptable",
                    message=f"Latest ping is {ping:.3f} ms, which is still reasonable for general use.",
                    recommendation="Latency is acceptable, though not especially low.",
                )
            )
        else:
            insights.append(
                SpeedTestInsight(
                    severity="medium",
                    title="Latency is elevated",
                    message=f"Latest ping is {ping:.3f} ms, which may be noticeable in calls, gaming, or remote sessions.",
                    recommendation="Check whether other devices, uploads, or provider congestion are affecting responsiveness.",
                )
            )

        if download >= 100:
            download_label = "strong"
        elif download >= 25:
            download_label = "solid"
        elif download >= 10:
            download_label = "moderate"
        else:
            download_label = "limited"

        if upload >= 50:
            upload_label = "strong"
        elif upload >= 10:
            upload_label = "solid"
        elif upload >= 3:
            upload_label = "moderate"
        else:
            upload_label = "limited"

        insights.append(
            SpeedTestInsight(
                severity="info",
                title="Throughput summary",
                message=(
                    f"Latest speed test shows {download:.3f} Mbps download ({download_label}) "
                    f"and {upload:.3f} Mbps upload ({upload_label})."
                ),
                recommendation="Use this as an active connection benchmark alongside the passive network monitor.",
            )
        )

        if previous is not None:
            prev_download = float(previous["download_mbps"] or 0)
            prev_upload = float(previous["upload_mbps"] or 0)
            prev_ping = float(previous["ping_ms"] or 0)

            delta_download = download - prev_download
            delta_upload = upload - prev_upload
            delta_ping = ping - prev_ping

            insights.append(
                SpeedTestInsight(
                    severity="info",
                    title="Compared with previous successful test",
                    message=(
                        f"Download changed by {delta_download:+.3f} Mbps, "
                        f"upload changed by {delta_upload:+.3f} Mbps, "
                        f"and ping changed by {delta_ping:+.3f} ms."
                    ),
                    recommendation="Track this over time to see whether changes are one-off or part of a trend.",
                )
            )

        return self._build_result(summary, latest, previous, insights)

    def _build_result(
        self,
        summary: dict,
        latest: dict | None,
        previous: dict | None,
        insights: list[SpeedTestInsight],
    ) -> dict:
        return {
            "summary": summary,
            "latest": latest,
            "previous": previous,
            "insights": [
                {
                    "severity": item.severity,
                    "title": item.title,
                    "message": item.message,
                    "recommendation": item.recommendation,
                }
                for item in insights
            ],
        }


if __name__ == "__main__":
    analyzer = SpeedTestInsightsAnalyzer()
    result = analyzer.analyze()

    print("SPEED TEST INSIGHTS\n")
    for item in result["insights"]:
        print(f"[{item['severity'].upper()}] {item['title']}")
        print(f"Message: {item['message']}")
        print(f"Recommendation: {item['recommendation']}\n")