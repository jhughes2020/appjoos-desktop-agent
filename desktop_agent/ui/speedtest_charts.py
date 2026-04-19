from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SpeedTestChartWidget(FigureCanvas):
    def __init__(self) -> None:
        self.figure = Figure(figsize=(6, 3))
        super().__init__(self.figure)
        self.setMinimumHeight(260)

    def plot_speedtest_history(self, rows: list[dict]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = [row["timestamp"][-8:] for row in rows]
        download_values = [row["download_mbps"] for row in rows]
        upload_values = [row["upload_mbps"] for row in rows]

        if not labels:
            ax.text(0.5, 0.5, "No speed test history yet", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            self.draw()
            return

        ax.plot(labels, download_values, marker="o", label="Download Mbps")
        ax.plot(labels, upload_values, marker="o", label="Upload Mbps")
        ax.set_title("Recent Speed Test Results")
        ax.set_ylabel("Mbps")
        ax.tick_params(axis="x", rotation=25)
        ax.legend()

        self.figure.tight_layout()
        self.draw()