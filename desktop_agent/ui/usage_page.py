"""Usage tab UI for Desktop Agent."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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

from desktop_agent.analyzers.usage_insights import UsageInsightsAnalyzer
from desktop_agent.storage.usage_repo import UsageRepository
from desktop_agent.ui.usage_charts import UsageChartWidget


class UsagePage(QWidget):
    """Shows usage insights from app_sessions and app_catalog."""

    def __init__(self, tracker_runtime=None, app_settings=None) -> None:
        super().__init__()
        self.repo = UsageRepository()
        self.insights_analyzer = UsageInsightsAnalyzer(self.repo)
        self.tracker_runtime = tracker_runtime
        self.app_settings = app_settings
        self._build_ui()
        self.refresh_usage()

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
        self.title_label = QLabel("App Usage Insights")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_row.addWidget(self.title_label)

        header_row.addStretch()

        self.start_button = QPushButton("Start Tracking")
        self.start_button.clicked.connect(self.start_tracking)
        header_row.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Tracking")
        self.stop_button.clicked.connect(self.stop_tracking)
        header_row.addWidget(self.stop_button)

        root.addLayout(header_row)

        self.status_label = QLabel("Tracker status: Stopped")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(self.status_label)

        self.counts_label = QLabel("Tracked apps: -- | Sessions: -- | Tracked time: --")
        self.counts_label.setStyleSheet("font-size: 14px;")
        root.addWidget(self.counts_label)

        self.auto_start_checkbox = QCheckBox("Auto-start usage tracking when the app launches")
        self.auto_start_checkbox.stateChanged.connect(self.on_auto_start_changed)

        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        self.start_minimized_checkbox.stateChanged.connect(self.on_start_minimized_changed)

        self.minimize_to_tray_checkbox = QCheckBox("Minimize/close to tray instead of exiting")
        self.minimize_to_tray_checkbox.stateChanged.connect(self.on_minimize_to_tray_changed)

        if self.app_settings is not None:
            self.auto_start_checkbox.setChecked(
                self.app_settings.get_auto_start_usage_tracking()
            )
            self.start_minimized_checkbox.setChecked(
                self.app_settings.get_start_minimized_to_tray()
            )
            self.minimize_to_tray_checkbox.setChecked(
                self.app_settings.get_minimize_to_tray()
            )

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.addWidget(self.auto_start_checkbox)
        settings_layout.addWidget(self.start_minimized_checkbox)
        settings_layout.addWidget(self.minimize_to_tray_checkbox)

        root.addWidget(self._wrap_widget("Tracking Settings", settings_widget))

        self.live_session_box = QTextEdit()
        self.live_session_box.setReadOnly(True)
        self.live_session_box.setMinimumHeight(150)

        self.insights_box = QTextEdit()
        self.insights_box.setReadOnly(True)
        self.insights_box.setMinimumHeight(180)

        top_grid = QGridLayout()
        top_grid.setSpacing(12)
        top_grid.addWidget(self._wrap_widget("Live Current Session", self.live_session_box), 0, 0)
        top_grid.addWidget(self._wrap_widget("Usage Insights", self.insights_box), 0, 1)
        root.addLayout(top_grid)

        charts_grid = QGridLayout()
        charts_grid.setSpacing(12)

        self.top_apps_chart = UsageChartWidget()
        self.top_apps_chart.setMinimumHeight(320)

        self.daily_trend_chart = UsageChartWidget()
        self.daily_trend_chart.setMinimumHeight(320)

        charts_grid.addWidget(self._wrap_widget("Top Apps Chart", self.top_apps_chart), 0, 0)
        charts_grid.addWidget(self._wrap_widget("Daily Usage Trend", self.daily_trend_chart), 0, 1)
        root.addLayout(charts_grid)

        self.top_apps_box = QTextEdit()
        self.top_apps_box.setReadOnly(True)
        self.top_apps_box.setMinimumHeight(220)

        self.unused_14_box = QTextEdit()
        self.unused_14_box.setReadOnly(True)
        self.unused_14_box.setMinimumHeight(220)

        self.unused_30_box = QTextEdit()
        self.unused_30_box.setReadOnly(True)
        self.unused_30_box.setMinimumHeight(220)

        bottom_grid = QGridLayout()
        bottom_grid.setSpacing(12)
        bottom_grid.addWidget(self._wrap_widget("Most Used Apps - Last 7 Days", self.top_apps_box), 0, 0, 1, 2)
        bottom_grid.addWidget(self._wrap_widget("Apps Not Used in Last 14 Days", self.unused_14_box), 1, 0)
        bottom_grid.addWidget(self._wrap_widget("Apps Not Used in Last 30 Days", self.unused_30_box), 1, 1)
        root.addLayout(bottom_grid)

        root.addStretch()
        self._update_tracker_status()

    def _wrap_widget(self, title: str, child: QWidget) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(child)
        return group

    def on_auto_start_changed(self, state: int) -> None:
        if self.app_settings is None:
            return
        enabled = state == Qt.CheckState.Checked.value
        self.app_settings.set_auto_start_usage_tracking(enabled)

    def on_start_minimized_changed(self, state: int) -> None:
        if self.app_settings is None:
            return
        enabled = state == Qt.CheckState.Checked.value
        self.app_settings.set_start_minimized_to_tray(enabled)

    def on_minimize_to_tray_changed(self, state: int) -> None:
        if self.app_settings is None:
            return
        enabled = state == Qt.CheckState.Checked.value
        self.app_settings.set_minimize_to_tray(enabled)

    def start_tracking(self) -> None:
        if self.tracker_runtime is None:
            self.status_label.setText("Tracker status: Runtime not connected")
            return

        started = self.tracker_runtime.start()
        if started:
            self.status_label.setText("Tracker status: Running")
        else:
            self.status_label.setText("Tracker status: Already running")

        self.refresh_usage()

    def stop_tracking(self) -> None:
        if self.tracker_runtime is None:
            self.status_label.setText("Tracker status: Runtime not connected")
            return

        stopped = self.tracker_runtime.stop()
        if stopped:
            self.status_label.setText("Tracker status: Stopped")
        else:
            self.status_label.setText("Tracker status: Already stopped")

        self.refresh_usage()

    def _update_tracker_status(self) -> None:
        running = bool(self.tracker_runtime and self.tracker_runtime.is_running)

        if running:
            self.status_label.setText("Tracker status: Running")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("Tracker status: Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def refresh_usage(self) -> None:
        counts = self.repo.get_usage_counts()
        tracked_time = self._format_duration(int(counts["tracked_seconds"]))

        self.counts_label.setText(
            f"Tracked apps: {counts['tracked_apps']} | "
            f"Sessions: {counts['session_count']} | "
            f"Tracked time: {tracked_time}"
        )

        self.live_session_box.setPlainText(self._build_live_session_text())
        self.insights_box.setPlainText(self._build_insights_text())
        self.top_apps_box.setPlainText(self._build_top_apps_text())
        self.unused_14_box.setPlainText(self._build_unused_text(days=14))
        self.unused_30_box.setPlainText(self._build_unused_text(days=30))

        self.top_apps_chart.plot_top_apps(
            self.repo.get_top_apps_chart_data(days=7, limit=5)
        )
        self.daily_trend_chart.plot_daily_trend(
            self.repo.get_daily_usage_trend(days=7)
        )

        self._update_tracker_status()

    def _build_live_session_text(self) -> str:
        if self.tracker_runtime is None:
            return "Usage runtime is not connected."

        session = self.tracker_runtime.get_live_session_snapshot()
        if session is None:
            return (
                "No live session is active right now.\n\n"
                "Notes:\n"
                "- Current usage is written to the database when you switch apps or stop tracking.\n"
                "- This live panel shows what is happening now."
            )

        duration = self._format_duration(int(session["active_seconds"]))
        return (
            f"Process: {session['process_name']}\n"
            f"Started: {session['started_at']}\n"
            f"Live duration: {duration}\n"
            f"Window title: {session['window_title'] or '(none)'}\n"
            f"Path: {session['exe_path'] or '(unknown)'}\n\n"
            f"Note: This session may not appear in the database-backed summaries until it is flushed."
        )

    def _build_insights_text(self) -> str:
        result = self.insights_analyzer.analyze()
        rows = result["insights"]

        if not rows:
            return "No usage insights available yet."

        lines = []
        for item in rows:
            lines.append(
                f"[{item['severity'].upper()}] {item['title']}\n"
                f"Message: {item['message']}\n"
                f"Recommendation: {item['recommendation']}\n"
            )
        return "\n".join(lines)

    def _build_top_apps_text(self) -> str:
        rows = self.repo.get_top_apps(days=7, limit=15)
        if not rows:
            return "No app usage data yet. Start tracking to begin collecting sessions."

        lines = []
        for index, row in enumerate(rows, start=1):
            duration = self._format_duration(int(row["total_seconds"]))
            lines.append(
                f"{index}. {row['process_name']}\n"
                f"   Time: {duration}\n"
                f"   Path: {row['exe_path']}\n"
            )
        return "\n".join(lines)

    def _build_unused_text(self, days: int) -> str:
        rows = self.repo.get_unused_apps(days=days, limit=50)
        if not rows:
            return f"No tracked apps have gone unused for {days} days yet."

        lines = []
        for index, row in enumerate(rows, start=1):
            lines.append(
                f"{index}. {row['process_name']}\n"
                f"   Last seen: {row['last_seen_at']}\n"
                f"   Path: {row['exe_path']}\n"
            )
        return "\n".join(lines)

    def _format_duration(self, total_seconds: int) -> str:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"