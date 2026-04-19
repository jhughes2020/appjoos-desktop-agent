"""Network tab UI for Desktop Agent."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_agent.analyzers.network_insights import NetworkInsightsAnalyzer
from desktop_agent.analyzers.speedtest_insights import SpeedTestInsightsAnalyzer
from desktop_agent.storage.network_repo import NetworkRepository
from desktop_agent.storage.speedtest_repo import SpeedTestRepository
from desktop_agent.ui.speedtest_charts import SpeedTestChartWidget


class NetworkPage(QWidget):
    def __init__(self, network_runtime=None, speedtest_runtime=None) -> None:
        super().__init__()
        self.repo = NetworkRepository()
        self.speedtest_repo = SpeedTestRepository()
        self.insights_analyzer = NetworkInsightsAnalyzer(self.repo)
        self.speedtest_insights_analyzer = SpeedTestInsightsAnalyzer(self.speedtest_repo)
        self.network_runtime = network_runtime
        self.speedtest_runtime = speedtest_runtime
        self._build_ui()
        self.refresh_network()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setSpacing(12)

        header_row = QHBoxLayout()
        self.title_label = QLabel("Network Monitor and Speed Test")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_row.addWidget(self.title_label)

        header_row.addStretch()

        self.start_button = QPushButton("Start Passive Monitor")
        self.start_button.clicked.connect(self.start_monitoring)
        header_row.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Passive Monitor")
        self.stop_button.clicked.connect(self.stop_monitoring)
        header_row.addWidget(self.stop_button)

        self.run_speedtest_button = QPushButton("Run Speed Test")
        self.run_speedtest_button.clicked.connect(self.run_speed_test)
        header_row.addWidget(self.run_speedtest_button)

        root.addLayout(header_row)

        self.status_label = QLabel("Network monitor status: Stopped")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(self.status_label)

        self.speedtest_status_label = QLabel("Speed test status: Idle")
        self.speedtest_status_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(self.speedtest_status_label)

        self.summary_label = QLabel("Samples: -- | Avg Down: -- | Avg Up: -- | Peak Down: -- | Peak Up: --")
        self.summary_label.setStyleSheet("font-size: 14px;")
        root.addWidget(self.summary_label)

        stats_row = QHBoxLayout()

        self.latest_down_label = QLabel("-- Mbps")
        self.latest_down_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.latest_up_label = QLabel("-- Mbps")
        self.latest_up_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.latest_time_label = QLabel("--")
        self.latest_time_label.setStyleSheet("font-size: 16px; font-weight: 500;")

        stats_row.addWidget(self._wrap_widget("Latest Download", self.latest_down_label))
        stats_row.addWidget(self._wrap_widget("Latest Upload", self.latest_up_label))
        stats_row.addWidget(self._wrap_widget("Latest Sample Time", self.latest_time_label))

        root.addLayout(stats_row)

        top_grid = QGridLayout()
        top_grid.setSpacing(12)

        self.latest_speedtest_box = QTextEdit()
        self.latest_speedtest_box.setReadOnly(True)
        self.latest_speedtest_box.setMinimumHeight(220)

        self.speedtest_insights_box = QTextEdit()
        self.speedtest_insights_box.setReadOnly(True)
        self.speedtest_insights_box.setMinimumHeight(220)

        top_grid.addWidget(self._wrap_widget("Latest Speed Test Result", self.latest_speedtest_box), 0, 0)
        top_grid.addWidget(self._wrap_widget("Speed Test Insights", self.speedtest_insights_box), 0, 1)

        root.addLayout(top_grid)

        self.speedtest_chart = SpeedTestChartWidget()
        self.speedtest_chart.setMinimumHeight(320)
        root.addWidget(self._wrap_widget("Recent Speed Test Chart", self.speedtest_chart))

        middle_grid = QGridLayout()
        middle_grid.setSpacing(12)

        self.insights_box = QTextEdit()
        self.insights_box.setReadOnly(True)
        self.insights_box.setMinimumHeight(220)

        self.speedtest_history_box = QTextEdit()
        self.speedtest_history_box.setReadOnly(True)
        self.speedtest_history_box.setMinimumHeight(220)

        middle_grid.addWidget(self._wrap_widget("Network Insights", self.insights_box), 0, 0)
        middle_grid.addWidget(self._wrap_widget("Recent Speed Test Results", self.speedtest_history_box), 0, 1)

        root.addLayout(middle_grid)

        self.history_box = QTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setMinimumHeight(260)
        root.addWidget(self._wrap_widget("Recent Passive Network Samples", self.history_box))

        root.addStretch()

        self._update_runtime_status()
        self._update_speedtest_status()

    def _wrap_widget(self, title: str, child: QWidget) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(child)
        return group

    def start_monitoring(self) -> None:
        if self.network_runtime is None:
            self.status_label.setText("Network monitor status: Runtime not connected")
            return

        started = self.network_runtime.start()
        if started:
            self.status_label.setText("Network monitor status: Running")
        else:
            self.status_label.setText("Network monitor status: Already running")

        self.refresh_network()

    def stop_monitoring(self) -> None:
        if self.network_runtime is None:
            self.status_label.setText("Network monitor status: Runtime not connected")
            return

        stopped = self.network_runtime.stop()
        if stopped:
            self.status_label.setText("Network monitor status: Stopped")
        else:
            self.status_label.setText("Network monitor status: Already stopped")

        self.refresh_network()

    def run_speed_test(self) -> None:
        if self.speedtest_runtime is None:
            self.speedtest_status_label.setText("Speed test status: Runtime not connected")
            return

        started = self.speedtest_runtime.start()
        if started:
            self.speedtest_status_label.setText("Speed test status: Running...")
        else:
            self.speedtest_status_label.setText("Speed test status: Already running")

        self._update_speedtest_status()

    def _update_runtime_status(self) -> None:
        running = bool(self.network_runtime and self.network_runtime.is_running)

        if running:
            self.status_label.setText("Network monitor status: Running")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("Network monitor status: Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def _update_speedtest_status(self) -> None:
        if self.speedtest_runtime is None:
            self.speedtest_status_label.setText("Speed test status: Runtime not connected")
            self.run_speedtest_button.setEnabled(False)
            return

        if self.speedtest_runtime.is_running:
            self.speedtest_status_label.setText("Speed test status: Running...")
            self.run_speedtest_button.setEnabled(False)
            return

        self.run_speedtest_button.setEnabled(True)

        status = self.speedtest_runtime.status
        if status == "success":
            self.speedtest_status_label.setText("Speed test status: Completed")
        elif status == "error":
            self.speedtest_status_label.setText("Speed test status: Error")
        else:
            self.speedtest_status_label.setText("Speed test status: Idle")

    def refresh_network(self) -> None:
        summary = self.repo.get_summary()
        latest = self.repo.get_latest_sample()

        self.summary_label.setText(
            f"Samples: {summary['sample_count']} | "
            f"Avg Down: {summary['avg_download_mbps']:.3f} Mbps | "
            f"Avg Up: {summary['avg_upload_mbps']:.3f} Mbps | "
            f"Peak Down: {summary['peak_download_mbps']:.3f} Mbps | "
            f"Peak Up: {summary['peak_upload_mbps']:.3f} Mbps"
        )

        if latest is None:
            self.latest_down_label.setText("-- Mbps")
            self.latest_up_label.setText("-- Mbps")
            self.latest_time_label.setText("--")
        else:
            self.latest_down_label.setText(f"{latest['download_mbps']:.3f} Mbps")
            self.latest_up_label.setText(f"{latest['upload_mbps']:.3f} Mbps")
            self.latest_time_label.setText(latest["timestamp"])

        self.latest_speedtest_box.setPlainText(self._build_latest_speedtest_text())
        self.speedtest_insights_box.setPlainText(self._build_speedtest_insights_text())
        self.insights_box.setPlainText(self._build_insights_text())
        self.history_box.setPlainText(self._build_history_text())
        self.speedtest_history_box.setPlainText(self._build_speedtest_history_text())
        self.speedtest_chart.plot_speedtest_history(self.speedtest_repo.get_chart_data(limit=7))

        self._update_runtime_status()
        self._update_speedtest_status()

    def _build_latest_speedtest_text(self) -> str:
        latest = self.speedtest_repo.get_latest_successful_result()
        previous = self.speedtest_repo.get_previous_successful_result()

        if not latest:
            row = self.speedtest_repo.get_latest_result()
            if not row:
                return "No saved speed test results yet."

            return (
                f"Status: {row['status']}\n"
                f"Timestamp: {row['timestamp']}\n"
                f"Error: {row['error_message'] or '(unknown error)'}"
            )

        lines = [
            f"Timestamp: {latest['timestamp']}",
            f"Ping: {latest['ping_ms']} ms",
            f"Download: {latest['download_mbps']:.3f} Mbps",
            f"Upload: {latest['upload_mbps']:.3f} Mbps",
            f"Packet Loss: {latest['packet_loss']}",
            f"ISP: {latest['isp'] or '(unknown)'}",
            f"External IP: {latest['external_ip'] or '(unknown)'}",
            f"Server: {latest['server_name'] or '(unknown)'}",
            f"Location: {latest['server_location'] or '(unknown)'}",
            f"Result URL: {latest['result_url'] or '(none)'}",
        ]

        if previous:
            delta_down = float(latest["download_mbps"] or 0) - float(previous["download_mbps"] or 0)
            delta_up = float(latest["upload_mbps"] or 0) - float(previous["upload_mbps"] or 0)
            delta_ping = float(latest["ping_ms"] or 0) - float(previous["ping_ms"] or 0)

            lines.extend(
                [
                    "",
                    "Compared with previous successful test:",
                    f"Download change: {delta_down:+.3f} Mbps",
                    f"Upload change: {delta_up:+.3f} Mbps",
                    f"Ping change: {delta_ping:+.3f} ms",
                ]
            )

        return "\n".join(lines)

    def _build_speedtest_insights_text(self) -> str:
        result = self.speedtest_insights_analyzer.analyze()
        rows = result["insights"]

        if not rows:
            return "No speed test insights available yet."

        lines = []
        for item in rows:
            lines.append(
                f"[{item['severity'].upper()}] {item['title']}\n"
                f"Message: {item['message']}\n"
                f"Recommendation: {item['recommendation']}\n"
            )
        return "\n".join(lines)

    def _build_insights_text(self) -> str:
        result = self.insights_analyzer.analyze()
        rows = result["insights"]

        if not rows:
            return "No network insights available yet."

        lines = []
        for item in rows:
            lines.append(
                f"[{item['severity'].upper()}] {item['title']}\n"
                f"Message: {item['message']}\n"
                f"Recommendation: {item['recommendation']}\n"
            )
        return "\n".join(lines)

    def _build_history_text(self) -> str:
        rows = self.repo.get_recent_samples(limit=20)
        if not rows:
            return "No network samples collected yet. Start the passive monitor to begin collecting data."

        lines = []
        for index, row in enumerate(rows, start=1):
            lines.append(
                f"{index}. {row['timestamp']}\n"
                f"   Down: {row['download_mbps']:.3f} Mbps\n"
                f"   Up:   {row['upload_mbps']:.3f} Mbps\n"
                f"   Total Recv: {row['bytes_recv']}\n"
                f"   Total Sent: {row['bytes_sent']}\n"
            )
        return "\n".join(lines)

    def _build_speedtest_history_text(self) -> str:
        rows = self.speedtest_repo.get_recent_results(limit=10)
        if not rows:
            return "No saved speed test results yet."

        lines = []
        for index, row in enumerate(rows, start=1):
            if row["status"] == "success":
                lines.append(
                    f"{index}. {row['timestamp']} | SUCCESS\n"
                    f"   Ping: {row['ping_ms']} ms\n"
                    f"   Download: {row['download_mbps']:.3f} Mbps\n"
                    f"   Upload: {row['upload_mbps']:.3f} Mbps\n"
                    f"   Server: {row['server_name'] or '(unknown)'}\n"
                    f"   ISP: {row['isp'] or '(unknown)'}\n"
                )
            else:
                lines.append(
                    f"{index}. {row['timestamp']} | ERROR\n"
                    f"   Error: {row['error_message'] or '(unknown error)'}\n"
                )
        return "\n".join(lines)