from __future__ import annotations

from dataclasses import dataclass

from desktop_agent.storage.usage_repo import UsageRepository


@dataclass
class UsageInsight:
    severity: str
    title: str
    message: str
    recommendation: str


class UsageInsightsAnalyzer:
    def __init__(self, repo: UsageRepository | None = None) -> None:
        self.repo = repo or UsageRepository()

    def analyze(self) -> dict:
        counts = self.repo.get_usage_counts()
        top_apps = self.repo.get_top_apps(days=7, limit=10)
        unused_14 = self.repo.get_unused_apps(days=14, limit=200)
        unused_30 = self.repo.get_unused_apps(days=30, limit=200)

        insights: list[UsageInsight] = []

        if counts["session_count"] == 0:
            insights.append(
                UsageInsight(
                    severity="info",
                    title="No usage history yet",
                    message="No app usage sessions have been collected yet.",
                    recommendation="Start usage tracking and use a few apps so the agent can build insights.",
                )
            )
            return self._build_result(counts, top_apps, unused_14, unused_30, insights)

        total_seconds = int(counts["tracked_seconds"])

        if top_apps:
            top_app = top_apps[0]
            share = round((top_app["total_seconds"] / total_seconds) * 100, 1) if total_seconds > 0 else 0.0
            insights.append(
                UsageInsight(
                    severity="info",
                    title="Top app this week",
                    message=(
                        f"{top_app['process_name']} is your most-used tracked app this week "
                        f"at {top_app['total_seconds']} seconds, about {share}% of tracked usage."
                    ),
                    recommendation="Keep watching whether this app matches how you expect to spend your time.",
                )
            )

        if len(top_apps) >= 3:
            top_three_seconds = sum(int(item["total_seconds"]) for item in top_apps[:3])
            top_three_share = round((top_three_seconds / total_seconds) * 100, 1) if total_seconds > 0 else 0.0
            insights.append(
                UsageInsight(
                    severity="info",
                    title="Usage concentration",
                    message=(
                        f"Your top 3 tracked apps account for about {top_three_share}% of recorded app time."
                    ),
                    recommendation="This helps you spot whether your time is concentrated in a few tools or spread out.",
                )
            )

        unused_14_count = len(unused_14)
        unused_30_count = len(unused_30)

        if unused_30_count > 0:
            insights.append(
                UsageInsight(
                    severity="medium",
                    title="Apps stale for 30 days",
                    message=f"{unused_30_count} tracked app(s) have not been used in the last 30 days.",
                    recommendation="Review these apps for cleanup, uninstall, or deprioritization.",
                )
            )
        elif unused_14_count > 0:
            insights.append(
                UsageInsight(
                    severity="low",
                    title="Apps stale for 14 days",
                    message=f"{unused_14_count} tracked app(s) have not been used in the last 14 days.",
                    recommendation="Watch these apps to see whether they are still needed.",
                )
            )
        else:
            insights.append(
                UsageInsight(
                    severity="info",
                    title="Recently active app set",
                    message="All tracked apps have been used within the last 14 days.",
                    recommendation="Keep collecting data to make the stale-app list more meaningful over time.",
                )
            )

        if counts["tracked_apps"] >= 10 and unused_30_count >= 5:
            insights.append(
                UsageInsight(
                    severity="medium",
                    title="Potential app clutter",
                    message=(
                        f"You have {counts['tracked_apps']} tracked apps and {unused_30_count} "
                        f"of them have not been used in 30 days."
                    ),
                    recommendation="This may be a good time to audit older apps and remove tools you no longer use.",
                )
            )

        return self._build_result(counts, top_apps, unused_14, unused_30, insights)

    def _build_result(
        self,
        counts: dict,
        top_apps: list[dict],
        unused_14: list[dict],
        unused_30: list[dict],
        insights: list[UsageInsight],
    ) -> dict:
        return {
            "counts": counts,
            "top_apps": top_apps,
            "unused_14": unused_14,
            "unused_30": unused_30,
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
    analyzer = UsageInsightsAnalyzer()
    result = analyzer.analyze()

    print("USAGE INSIGHTS\n")
    for item in result["insights"]:
        print(f"[{item['severity'].upper()}] {item['title']}")
        print(f"Message: {item['message']}")
        print(f"Recommendation: {item['recommendation']}\n")