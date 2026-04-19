"""Main desktop window for Desktop Agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_agent.analyzers.health_rules import HealthAnalyzer
from desktop_agent.collectors.system_collector import SystemCollector
from desktop_agent.config.app_settings import AppSettings
from desktop_agent.config.app_version import APP_DISPLAY_NAME
from desktop_agent.reports.generator import ReportGenerator
from desktop_agent.services.network_runtime import NetworkTrackingRuntime
from desktop_agent.services.speedtest_runtime import SpeedTestRuntime
from desktop_agent.services.usage_runtime import UsageTrackingRuntime
from desktop_agent.storage.db import DatabaseManager
from desktop_agent.ui.network_page import NetworkPage
from desktop_agent.ui.usage_page import UsagePage


class MainWindow(QMainWindow):
    """Desktop UI with Overview, Usage, and Network tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1250, 850)

        self.collector = SystemCollector()
        self.analyzer = HealthAnalyzer()
        self.db = DatabaseManager()
        self.report_generator = ReportGenerator()

        self.app_settings = AppSettings()
        self.usage_runtime = UsageTrackingRuntime(poll_interval=5, idle_threshold=60)
        self.network_runtime = NetworkTrackingRuntime(poll_interval=2)
        self.speedtest_runtime = SpeedTestRuntime()

        self.current_snapshot: dict[str, Any] = {}
        self.current_processes: list[dict[str, Any]] = []
        self.current_analysis: dict[str, Any] = {}

        self._allow_real_exit = False
        self._tray_icon: QSystemTrayIcon | None = None
        self._tray_message_shown = False

        self._build_ui()
        self._setup_tray()
        self._configure_timer()
        self.refresh_data()

        if self.app_settings.get_auto_start_usage_tracking():
            self.usage_runtime.start()
            self.usage_tab.refresh_usage()

        if self.app_settings.get_start_minimized_to_tray():
            QTimer.singleShot(250, self.start_hidden_in_tray)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        self.overview_tab = QWidget()
        self.usage_tab = UsagePage(self.usage_runtime, self.app_settings)
        self.network_tab = NetworkPage(self.network_runtime, self.speedtest_runtime)

        self.tabs.addTab(self.overview_tab, "Overview")
        self.tabs.addTab(self.usage_tab, "Usage")
        self.tabs.addTab(self.network_tab, "Network")

        overview_layout = QVBoxLayout(self.overview_tab)

        self.health_label = QLabel("AppJoos Desktop Agent | Health Score: --")
        self.health_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        overview_layout.addWidget(self.health_label)

        metrics_grid = QGridLayout()
        self.cpu_box, self.cpu_value = self._metric_box("CPU Usage")
        self.memory_box, self.memory_value = self._metric_box("Memory Usage")
        self.disk_box, self.disk_value = self._metric_box("Disk Usage")
        self.uptime_box, self.uptime_value = self._metric_box("Uptime")

        metrics_grid.addWidget(self.cpu_box, 0, 0)
        metrics_grid.addWidget(self.memory_box, 0, 1)
        metrics_grid.addWidget(self.disk_box, 1, 0)
        metrics_grid.addWidget(self.uptime_box, 1, 1)
        overview_layout.addLayout(metrics_grid)

        buttons_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self.refresh_data)
        buttons_layout.addWidget(self.refresh_button)

        self.save_button = QPushButton("Save Snapshot")
        self.save_button.clicked.connect(self.save_snapshot)
        buttons_layout.addWidget(self.save_button)

        self.report_button = QPushButton("Generate Report")
        self.report_button.clicked.connect(self.generate_report)
        buttons_layout.addWidget(self.report_button)

        buttons_layout.addStretch()
        overview_layout.addLayout(buttons_layout)

        self.findings_box = QTextEdit()
        self.findings_box.setReadOnly(True)
        self.findings_box.setPlaceholderText("Findings and recommendations will appear here.")
        overview_layout.addWidget(
            self._wrap_widget("Findings and Recommendations", self.findings_box),
            stretch=2,
        )

        self.process_table = QTableWidget(0, 4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Process", "CPU %", "Memory MB"])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        overview_layout.addWidget(self._wrap_widget("Top Processes", self.process_table), stretch=3)

        self.history_box = QTextEdit()
        self.history_box.setReadOnly(True)
        overview_layout.addWidget(self._wrap_widget("Recent Snapshot History", self.history_box), stretch=2)

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon_path = Path(__file__).resolve().parents[2] / "app_icon.ico"
        icon = QIcon(str(icon_path)) if icon_path.exists() else self.windowIcon()

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        self._tray_icon.setToolTip(APP_DISPLAY_NAME)

        tray_menu = QMenu(self)

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_normal_from_tray)
        tray_menu.addAction(show_action)

        start_action = QAction("Start Tracking", self)
        start_action.triggered.connect(self._tray_start_tracking)
        tray_menu.addAction(start_action)

        stop_action = QAction("Stop Tracking", self)
        stop_action.triggered.connect(self._tray_stop_tracking)
        tray_menu.addAction(stop_action)

        tray_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_from_tray)
        tray_menu.addAction(exit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _metric_box(self, title: str) -> tuple[QGroupBox, QLabel]:
        label = QLabel("--")
        label.setStyleSheet("font-size: 18px; font-weight: 600;")
        box = self._wrap_widget(title, label)
        return box, label

    def _wrap_widget(self, title: str, child: QWidget) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(child)
        return group

    def _configure_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)

    def refresh_data(self) -> None:
        self.current_snapshot = self.collector.get_snapshot()
        self.current_processes = self.collector.get_top_processes(limit=10)
        self.current_analysis = self.analyzer.analyze(self.current_snapshot, self.current_processes)

        self._update_dashboard()
        self._update_process_table()
        self._load_recent_history()

        if hasattr(self, "usage_tab"):
            self.usage_tab.refresh_usage()

        if hasattr(self, "network_tab"):
            self.network_tab.refresh_network()

    def _update_dashboard(self) -> None:
        score = self.current_analysis["health_score"]
        self.health_label.setText(f"AppJoos Desktop Agent | Health Score: {score}/100")

        self.cpu_value.setText(f"{self.current_snapshot['cpu_percent']:.1f}%")
        self.memory_value.setText(
            f"{self.current_snapshot['memory_percent']:.1f}%\n"
            f"{self.current_snapshot['memory_used_gb']} / {self.current_snapshot['memory_total_gb']} GB"
        )
        self.disk_value.setText(
            f"{self.current_snapshot['disk_percent']:.1f}% used\n"
            f"{self.current_snapshot['disk_free_gb']} GB free"
        )
        self.uptime_value.setText(f"{self.current_snapshot['uptime_hours']} hours")

        findings_text = []
        for item in self.current_analysis["findings"]:
            findings_text.append(
                f"[{item['severity'].upper()}] {item['category']}\n"
                f"Message: {item['message']}\n"
                f"Recommendation: {item['recommendation']}\n"
            )

        self.findings_box.setPlainText("\n".join(findings_text))

    def _update_process_table(self) -> None:
        self.process_table.setRowCount(len(self.current_processes))
        for row, proc in enumerate(self.current_processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(str(proc["pid"])))
            self.process_table.setItem(row, 1, QTableWidgetItem(proc["name"]))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{proc['cpu_percent']:.1f}"))
            self.process_table.setItem(row, 3, QTableWidgetItem(f"{proc['memory_mb']:.1f}"))

    def _load_recent_history(self) -> None:
        rows = self.db.get_recent_snapshots(limit=5)
        if not rows:
            self.history_box.setPlainText("No saved snapshots yet. Click 'Save Snapshot' to begin building history.")
            return

        lines = []
        for row in rows:
            lines.append(
                f"{row['timestamp']} | Score {row['health_score']} | CPU {row['cpu_percent']:.1f}% | "
                f"Memory {row['memory_percent']:.1f}% | Disk {row['disk_percent']:.1f}%\n"
                f"Summary: {row['summary']}\n"
            )
        self.history_box.setPlainText("\n".join(lines))

    def save_snapshot(self) -> None:
        snapshot_id = self.db.save_snapshot(
            self.current_snapshot,
            self.current_analysis,
            self.current_processes,
        )
        self._load_recent_history()
        QMessageBox.information(self, "Snapshot Saved", f"Snapshot {snapshot_id} was saved to SQLite.")

    def generate_report(self) -> None:
        report_path: Path = self.report_generator.write_markdown_report(
            self.current_snapshot,
            self.current_analysis,
            self.current_processes,
        )
        QMessageBox.information(self, "Report Generated", f"Report saved to:\n{report_path}")

    def start_hidden_in_tray(self) -> None:
        if self._tray_icon is None:
            return
        self.hide()
        if not self._tray_message_shown:
            self._tray_icon.showMessage(
                "AppJoos Desktop Agent",
                "The app started minimized in the system tray.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self._tray_message_shown = True

    def show_normal_from_tray(self) -> None:
        self.show()
        self.setWindowState(self.windowState() & ~self.windowState().WindowMinimized)
        self.raise_()
        self.activateWindow()

    def _tray_start_tracking(self) -> None:
        self.usage_runtime.start()
        self.usage_tab.refresh_usage()

    def _tray_stop_tracking(self) -> None:
        self.usage_runtime.stop()
        self.usage_tab.refresh_usage()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal_from_tray()

    def exit_from_tray(self) -> None:
        self._allow_real_exit = True

        if self.usage_runtime.is_running:
            self.usage_runtime.stop()

        if self.network_runtime.is_running:
            self.network_runtime.stop()

        if self._tray_icon is not None:
            self._tray_icon.hide()

        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        minimize_to_tray = self.app_settings.get_minimize_to_tray()

        if (
            minimize_to_tray
            and not self._allow_real_exit
            and self._tray_icon is not None
            and self._tray_icon.isVisible()
        ):
            self.hide()
            if not self._tray_message_shown:
                self._tray_icon.showMessage(
                    "AppJoos Desktop Agent",
                    "The app is still running in the system tray.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )
                self._tray_message_shown = True
            event.ignore()
            return

        if hasattr(self, "usage_runtime") and self.usage_runtime.is_running:
            self.usage_runtime.stop()

        if hasattr(self, "network_runtime") and self.network_runtime.is_running:
            self.network_runtime.stop()

        if self._tray_icon is not None:
            self._tray_icon.hide()

        event.accept()
        super().closeEvent(event)

