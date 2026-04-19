from __future__ import annotations

from dataclasses import dataclass

from desktop_agent.storage.network_repo import NetworkRepository


@dataclass
class NetworkInsight:
    severity: str
    title: str
    message: str
    recommendation: str


class NetworkInsightsAnalyzer:
    def __init__(self, repo: NetworkRepository | None = None) -> None:
        self.repo = repo or NetworkRepository()

    def analyze(self) -> dict:
        latest = self.repo.get_latest_sample()
        summary = self.repo.get_summary()
        recent = self.repo.get_recent_samples(limit=20)

        insights: list[NetworkInsight] = []

        sample_count = int(summary["sample_count"])
        avg_down = float(summary["avg_download_mbps"])
        avg_up = float(summary["avg_upload_mbps"])
        peak_down = float(summary["peak_download_mbps"])
        peak_up = float(summary["peak_upload_mbps"])

        if sample_count == 0 or latest is None:
            insights.append(
                NetworkInsight(
                    severity="info",
                    title="No network history yet",
                    message="No passive network samples have been collected yet.",
                    recommendation="Start the passive network monitor and generate some traffic so the agent can build insights.",
                )
            )
            return self._build_result(latest, summary, recent, insights)

        if sample_count < 5:
            insights.append(
                NetworkInsight(
                    severity="info",
                    title="Limited network history",
                    message=f"Only {sample_count} network sample(s) have been collected so far.",
                    recommendation="Let the passive monitor run longer to make trend analysis more meaningful.",
                )
            )

        insights.append(
            NetworkInsight(
                severity="info",
                title="Current network snapshot",
                message=(
                    f"Latest sample shows download at {latest['download_mbps']:.3f} Mbps "
                    f"and upload at {latest['upload_mbps']:.3f} Mbps."
                ),
                recommendation="Use this as a quick point-in-time reference, not a full speed test.",
            )
        )

        if peak_down >= max(avg_down * 3, 1.0):
            insights.append(
                NetworkInsight(
                    severity="info",
                    title="Bursty download activity",
                    message=(
                        f"Peak passive download traffic reached {peak_down:.3f} Mbps, "
                        f"which is notably higher than the average of {avg_down:.3f} Mbps."
                    ),
                    recommendation="This usually means short bursts of browsing, streaming, downloads, or app updates.",
                )
            )

        if peak_up >= max(avg_up * 3, 0.5):
            insights.append(
                NetworkInsight(
                    severity="info",
                    title="Bursty upload activity",
                    message=(
                        f"Peak passive upload traffic reached {peak_up:.3f} Mbps, "
                        f"which is notably higher than the average of {avg_up:.3f} Mbps."
                    ),
                    recommendation="This can reflect sync tools, cloud backups, calls, or file uploads.",
                )
            )

        if avg_down < 0.25 and avg_up < 0.25:
            insights.append(
                NetworkInsight(
                    severity="low",
                    title="Light recent network usage",
                    message=(
                        f"Average passive network traffic is currently low "
                        f"({avg_down:.3f} Mbps down / {avg_up:.3f} Mbps up)."
                    ),
                    recommendation="That usually means the machine has been relatively quiet on the network.",
                )
            )
        elif avg_down >= 1.0 or avg_up >= 1.0:
            insights.append(
                NetworkInsight(
                    severity="info",
                    title="Sustained network activity detected",
                    message=(
                        f"Average passive traffic has been {avg_down:.3f} Mbps down "
                        f"and {avg_up:.3f} Mbps up."
                    ),
                    recommendation="Compare this with system load if the machine feels slow during active network periods.",
                )
            )

        if latest["download_mbps"] < max(avg_down * 0.25, 0.05) and avg_down >= 0.5:
            insights.append(
                NetworkInsight(
                    severity="low",
                    title="Download activity has cooled off",
                    message=(
                        f"The latest download sample ({latest['download_mbps']:.3f} Mbps) "
                        f"is well below the recent average of {avg_down:.3f} Mbps."
                    ),
                    recommendation="This may simply mean recent download-heavy activity has ended.",
                )
            )

        if latest["upload_mbps"] < max(avg_up * 0.25, 0.05) and avg_up >= 0.5:
            insights.append(
                NetworkInsight(
                    severity="low",
                    title="Upload activity has cooled off",
                    message=(
                        f"The latest upload sample ({latest['upload_mbps']:.3f} Mbps) "
                        f"is well below the recent average of {avg_up:.3f} Mbps."
                    ),
                    recommendation="This may mean a sync, upload, or call-related burst has passed.",
                )
            )

        return self._build_result(latest, summary, recent, insights)

    def _build_result(
        self,
        latest: dict | None,
        summary: dict,
        recent: list[dict],
        insights: list[NetworkInsight],
    ) -> dict:
        return {
            "latest": latest,
            "summary": summary,
            "recent": recent,
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
    analyzer = NetworkInsightsAnalyzer()
    result = analyzer.analyze()

    print("NETWORK INSIGHTS\n")
    for item in result["insights"]:
        print(f"[{item['severity'].upper()}] {item['title']}")
        print(f"Message: {item['message']}")
        print(f"Recommendation: {item['recommendation']}\n")