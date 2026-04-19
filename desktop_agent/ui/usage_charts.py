from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class UsageChartWidget(FigureCanvas):
    def __init__(self) -> None:
        self.figure = Figure(figsize=(6, 3))
        super().__init__(self.figure)
        self.setMinimumHeight(260)

    def plot_top_apps(self, rows: list[dict]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = [row["label"] for row in rows]
        values = [row["minutes"] for row in rows]

        if not labels:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            self.draw()
            return

        ax.bar(labels, values)
        ax.set_title("Top Apps by Minutes (Last 7 Days)")
        ax.set_ylabel("Minutes")
        ax.tick_params(axis="x", rotation=25)

        self.figure.tight_layout()
        self.draw()

    def plot_daily_trend(self, rows: list[dict]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = [row["day"] for row in rows]
        values = [row["minutes"] for row in rows]

        if not labels:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            self.draw()
            return

        ax.plot(labels, values, marker="o")
        ax.set_title("Daily Usage Trend (Last 7 Days)")
        ax.set_ylabel("Minutes")
        ax.tick_params(axis="x", rotation=25)

        self.figure.tight_layout()
        self.draw()