from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QPlainTextEdit,
    QGroupBox,
    QGridLayout,
    QTextBrowser,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from datetime import datetime

from gui.workers import StartupCheckWorker
from config import DEFAULT_SYMBOL


class MainWindow(QMainWindow):
    """Main application window for NeuroTrade AI."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NeuroTrade AI")
        self.resize(1150, 720)

        self._worker = None

        self._build_ui()
        self._build_menu()
        self._build_status_bar()

        self.append_log("GUI skeleton initialized.")
        self.start_system_checks()

    def _build_ui(self):
        central_widget = QWidget()
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._create_logs_tab(), "Logs")
        self.tabs.addTab(self._create_about_tab(), "About")

        root_layout.addWidget(self.tabs)
        self.setCentralWidget(central_widget)

    def _create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # System status group
        status_group = QGroupBox("System Status")
        status_grid = QGridLayout(status_group)
        status_grid.setHorizontalSpacing(18)
        status_grid.setVerticalSpacing(8)

        self.db_value = self._make_value_label("Checking...")
        self.mt5_value = self._make_value_label("Checking...")
        self.account_value = self._make_value_label("--")
        self.server_value = self._make_value_label("--")
        self.mode_value = self._make_value_label("--")
        self.symbol_value = self._make_value_label("Checking...")
        self.digits_value = self._make_value_label("--")
        self.volume_min_value = self._make_value_label("--")
        self.volume_max_value = self._make_value_label("--")

        rows = [
            ("SQLite Database:", self.db_value),
            ("MT5 Connection:", self.mt5_value),
            ("Account:", self.account_value),
            ("Server:", self.server_value),
            ("Account Mode:", self.mode_value),
            ("Symbol:", self.symbol_value),
            ("Digits:", self.digits_value),
            ("Volume Min:", self.volume_min_value),
            ("Volume Max:", self.volume_max_value),
        ]

        for row, (title, value_label) in enumerate(rows):
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #9aa0a6;")
            status_grid.addWidget(title_label, row, 0)
            status_grid.addWidget(value_label, row, 1)

        status_grid.setColumnStretch(1, 1)
        layout.addWidget(status_group)

        # Trading placeholder group
        trading_group = QGroupBox("Trading")
        trading_layout = QVBoxLayout(trading_group)
        trading_label = QLabel("Trading controls will be added in a future part.")
        trading_label.setStyleSheet("color: #9aa0a6;")
        trading_layout.addWidget(trading_label)
        layout.addWidget(trading_group)

        # Chart placeholder group
        chart_group = QGroupBox("Chart")
        chart_layout = QVBoxLayout(chart_group)
        chart_placeholder = QLabel("XAUUSD chart placeholder")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setMinimumHeight(240)
        chart_placeholder.setStyleSheet(
            "color: #9aa0a6; border: 1px dashed #3a4048; background-color: #0d1013;"
        )
        chart_layout.addWidget(chart_placeholder)
        layout.addWidget(chart_group)

        layout.addStretch()
        return tab

    def _create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(10000)

        layout.addWidget(self.log_text)
        return tab

    def _create_about_tab(self):
        tab = QTextBrowser()
        tab.setOpenExternalLinks(False)
        tab.setHtml(
            "<h2>NeuroTrade AI</h2>"
            "<p>Personal-use self-learning trading system skeleton.</p>"
            "<p>Part 2 provides the GUI skeleton only. No trading operations are executed.</p>"
            "<p>DEMO only.</p>"
        )
        return tab

    def _build_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Exit", self.close)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About", self._show_about)

    def _build_status_bar(self):
        status_bar = self.statusBar()
        status_bar.showMessage("Starting...")

        self.db_status_label = QLabel("DB: Checking")
        self.mt5_status_label = QLabel("MT5: Checking")
        self.symbol_status_label = QLabel(f"Symbol: {DEFAULT_SYMBOL}")

        for widget in (
            self.db_status_label,
            self.mt5_status_label,
            self.symbol_status_label,
        ):
            widget.setContentsMargins(8, 0, 8, 0)
            status_bar.addPermanentWidget(widget)

    def _make_value_label(self, text: str):
        label = QLabel(text)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("color: #d5d8dc; font-weight: bold;")
        return label

    def _set_label_state(self, label, text: str, state: str):
        colors = {
            "ok": "#2ecc71",
            "fail": "#e74c3c",
            "checking": "#f1c40f",
            "neutral": "#d5d8dc",
        }

        color = colors.get(state, colors["neutral"])
        label.setText(text)
        label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def start_system_checks(self):
        if self._worker is not None and self._worker.isRunning():
            return

        self._set_checking_state()
        self.append_log("Starting background system checks...")

        self._worker = StartupCheckWorker()
        self._worker.log.connect(self.append_log)
        self._worker.status.connect(self._on_system_status)
        self._worker.finished_check.connect(self._on_checks_finished)
        self._worker.start()

    def _set_checking_state(self):
        self._set_label_state(self.db_value, "Checking...", "checking")
        self._set_label_state(self.mt5_value, "Checking...", "checking")
        self._set_label_state(self.account_value, "--", "neutral")
        self._set_label_state(self.server_value, "--", "neutral")
        self._set_label_state(self.mode_value, "--", "neutral")
        self._set_label_state(self.symbol_value, "Checking...", "checking")
        self._set_label_state(self.digits_value, "--", "neutral")
        self._set_label_state(self.volume_min_value, "--", "neutral")
        self._set_label_state(self.volume_max_value, "--", "neutral")

        self._set_label_state(self.db_status_label, "DB: Checking", "checking")
        self._set_label_state(self.mt5_status_label, "MT5: Checking", "checking")
        self._set_label_state(
            self.symbol_status_label,
            f"Symbol: {DEFAULT_SYMBOL}",
            "checking",
        )

    def _on_system_status(self, status):
        db_status = status.get("db", "UNKNOWN")
        mt5_status = status.get("mt5", "UNKNOWN")
        account = status.get("account", "--")
        server = status.get("server", "--")
        mode = status.get("mode", "--")
        symbol = status.get("symbol", "--")
        digits = status.get("digits", "--")
        volume_min = status.get("volume_min", "--")
        volume_max = status.get("volume_max", "--")

        db_state = "ok" if db_status == "OK" else "fail"
        mt5_state = "ok" if mt5_status == "OK" else "fail"
        symbol_state = "ok" if symbol not in ("", "--", None) else "fail"

        self._set_label_state(self.db_value, db_status, db_state)
        self._set_label_state(self.mt5_value, mt5_status, mt5_state)
        self._set_label_state(self.account_value, account, "neutral")
        self._set_label_state(self.server_value, server, "neutral")
        self._set_label_state(self.mode_value, mode, "neutral")
        self._set_label_state(self.symbol_value, symbol, symbol_state)
        self._set_label_state(self.digits_value, digits, "neutral")
        self._set_label_state(self.volume_min_value, volume_min, "neutral")
        self._set_label_state(self.volume_max_value, volume_max, "neutral")

        self._set_label_state(self.db_status_label, f"DB: {db_status}", db_state)
        self._set_label_state(
            self.mt5_status_label,
            f"MT5: {mt5_status}",
            mt5_state,
        )
        self._set_label_state(
            self.symbol_status_label,
            f"Symbol: {symbol}",
            symbol_state,
        )

    def _on_checks_finished(self):
        self.append_log("System checks finished.")
        self.statusBar().showMessage("Ready", 5000)

    def append_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")

    def _show_about(self):
        QMessageBox.about(
            self,
            "NeuroTrade AI",
            "<h3>NeuroTrade AI</h3>"
            "<p>Personal-use self-learning trading system.</p>"
            "<p>Part 2: GUI skeleton only. No trading operations are executed.</p>"
            "<p>DEMO only.</p>",
        )

    def closeEvent(self, event):
        # Wait briefly for the background worker to avoid signals being
        # delivered to a window that is being destroyed.
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(3000)

        event.accept()