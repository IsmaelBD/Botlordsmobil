"""
ui/desktop/main_window.py — Lords Mobile Bot — PyQt5 Desktop UI
Professional multi-account management interface.
"""

import sys
import json
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QScrollArea, QStatusBar, QMenuBar, QMenu,
    QAction, QMessageBox, QFileDialog, QProgressBar, QTextEdit,
    QSplitter, QFrame, QStyle, QStyleFactory
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

from modules.gatherer.bot import GathererBot
from modules.attacker.bot import AttackerBot
from modules.redeemer.bot import RedeemerBot
from modules.explorer.bot import ExplorerBot
from brain.fsm.engine import FSMBotEngine


# ──────────────────────────────────────────────
#  Theme & Styling
# ──────────────────────────────────────────────
DARK_STYLE = """
QMainWindow {
    background-color: #1a1a2e;
}
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QPushButton {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 6px 16px;
    color: #e0e0e0;
}
QPushButton:hover {
    background-color: #0f3460;
}
QPushButton:pressed {
    background-color: #e94560;
}
QPushButton:disabled {
    background-color: #2a2a3e;
    color: #666;
}
QPushButton.primary {
    background-color: #e94560;
    font-weight: bold;
}
QPushButton.primary:hover {
    background-color: #ff6b6b;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 3px;
    padding: 4px 8px;
    color: #e0e0e0;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #0f3460;
}
QGroupBox {
    border: 1px solid #0f3460;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
    color: #e94560;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QTabWidget::pane {
    border: 1px solid #0f3460;
    border-radius: 4px;
    background-color: #16213e;
}
QTabBar::tab {
    background-color: #1a1a2e;
    border: 1px solid #0f3460;
    padding: 8px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #e94560;
    color: white;
}
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a1a2e;
    gridline-color: #0f3460;
    border: none;
}
QHeaderView::section {
    background-color: #0f3460;
    color: #e0e0e0;
    padding: 6px;
    border: none;
}
QStatusBar {
    background-color: #0f3460;
    color: #aaa;
}
QProgressBar {
    border: 1px solid #0f3460;
    border-radius: 4px;
    text-align: center;
    background-color: #16213e;
}
QProgressBar::chunk {
    background-color: #e94560;
}
QTextEdit {
    background-color: #0d0d1a;
    border: 1px solid #0f3460;
    color: #00ff88;
    font-family: 'Courier New', monospace;
    font-size: 9pt;
}
QScrollBar:vertical {
    background: #1a1a2e;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #0f3460;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #e94560;
}
QFrame.separator {
    background-color: #0f3460;
}
"""


# ──────────────────────────────────────────────
#  Worker Threads (non-blocking automation)
# ──────────────────────────────────────────────
class BotWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, str)

    def __init__(self, task_fn, *args, **kwargs):
        super().__init__()
        self.task_fn = task_fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.log_signal.emit(f"[*] Starting task...")
            result = self.task_fn(*self.args, **self.kwargs)
            self.log_signal.emit(f"[✅] Task completed: {result}")
        except Exception as e:
            self.log_signal.emit(f"[!] Error: {e}")
        finally:
            self.finished_signal.emit()


# ──────────────────────────────────────────────
#  Account Manager
# ──────────────────────────────────────────────
class AccountManager(QWidget):
    """Manages multiple Lords Mobile accounts."""

    accounts_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.accounts = self._load_accounts()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Account table
        self.table = QTableWidget()
        self.table.setColumns = ["Name", "Window Title", "Status", "Actions"]
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Window Title", "Status", "Actions"])
        self.table.setRowCount(len(self.accounts))
        self.populate_table()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Account")
        self.btn_add.clicked.connect(self.add_account)
        self.btn_remove = QPushButton("🗑️ Remove")
        self.btn_remove.clicked.connect(self.remove_account)
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_status)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()

        layout.addWidget(QLabel("<b>Account Profiles</b>"))
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.accounts))
        for row, acc in enumerate(self.accounts):
            self.table.setItem(row, 0, QTableWidgetItem(acc.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(acc.get("window_title", "Lords Mobile PC")))
            status = "🟢 Active" if acc.get("active", False) else "⚪ Inactive"
            self.table.setItem(row, 2, QTableWidgetItem(status))

            # Actions
            btn_frame = QWidget()
            btn_layout = QHBoxLayout(btn_frame)
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, r=row: self.edit_account(r))
            btn_layout.addWidget(edit_btn)
            self.table.setCellWidget(row, 3, btn_frame)

    def _load_accounts(self) -> list:
        cfg_path = Path(__file__).parent.parent.parent / "config" / "accounts.json"
        if cfg_path.exists():
            with open(cfg_path) as f:
                return json.load(f).get("accounts", [])
        return [{"name": "Default", "window_title": "Lords Mobile PC", "active": True}]

    def _save_accounts(self):
        cfg_path = Path(__file__).parent.parent.parent / "config" / "accounts.json"
        with open(cfg_path, "w") as f:
            json.dump({"accounts": self.accounts}, f, indent=2)
        self.accounts_changed.emit(self.accounts)

    def add_account(self):
        self.accounts.append({
            "name": f"Account {len(self.accounts)+1}",
            "window_title": "Lords Mobile PC",
            "active": False
        })
        self.populate_table()
        self._save_accounts()

    def remove_account(self):
        row = self.table.currentRow()
        if row >= 0:
            self.accounts.pop(row)
            self.populate_table()
            self._save_accounts()

    def edit_account(self, row):
        # Simple inline edit for now
        pass

    def refresh_status(self):
        # Check which game windows are actually running
        # Would use win32 API in real implementation
        self.populate_table()


# ──────────────────────────────────────────────
#  Automation Panels
# ──────────────────────────────────────────────
class GathererPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.bot = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Enable group
        enable_grp = QGroupBox("Enable Gatherer")
        enable_layout = QHBoxLayout(enable_grp)
        self.enable_cb = QCheckBox("Enable Resource Gathering")
        self.enable_cb.setStyleSheet("font-size: 12pt;")
        enable_layout.addWidget(self.enable_cb)
        layout.addWidget(enable_grp)

        # Settings
        settings_grp = QGroupBox("Gathering Settings")
        form = QFormLayout(settings_grp)

        self.target_x = QSpinBox()
        self.target_x.setRange(0, 9999)
        self.target_x.setValue(522)
        form.addRow("Target X:", self.target_x)

        self.target_y = QSpinBox()
        self.target_y.setRange(0, 9999)
        self.target_y.setValue(356)
        form.addRow("Target Y:", self.target_y)

        self.march_wait = QSpinBox()
        self.march_wait.setRange(30, 3600)
        self.march_wait.setValue(300)
        form.addRow("March Wait (s):", self.march_wait)

        self.loop_cb = QCheckBox("Loop indefinitely")
        self.loop_cb.setChecked(True)
        form.addRow("Loop:", self.loop_cb)

        layout.addWidget(settings_grp)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start", objectName="primary")
        self.btn_start.setStyleSheet("QPushButton#primary { background: #e94560; font-size: 11pt; }")
        self.btn_start.clicked.connect(self.start_gathering)
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_gathering)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Log
        layout.addWidget(QLabel("<b>Activity Log</b>"))
        self.log = QTextEdit()
        self.log.setMaximumHeight(150)
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        layout.addStretch()

    def log_msg(self, msg):
        self.log.append(msg)

    def start_gathering(self):
        self.log_msg("[*] Initializing gatherer...")
        self.bot = GathererBot()
        if not self.bot.verify_ready():
            self.log_msg("[!] Game not detected. Is Lords Mobile running?")
            return

        targets = [(self.target_x.value(), self.target_y.value())]
        loop = self.loop_cb.isChecked()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log_msg(f"[*] Starting gather cycle — target ({self.target_x.value()}, {self.target_y.value()})")

        def task():
            if loop:
                while True:
                    self.bot.gather_at(*targets[0])
                    import time
                    time.sleep(self.march_wait.value())
            else:
                self.bot.gather_at(*targets[0])

        self.worker = BotWorker(task)
        self.worker.log_signal.connect(self.log_msg)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def stop_gathering(self):
        if self.worker:
            self.worker.terminate()
            self.log_msg("[*] Gathering stopped")
        self.on_finished()

    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)


class AttackerPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.bot = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        enable_grp = QGroupBox("Enable Attack Module")
        enable_layout = QHBoxLayout(enable_grp)
        self.enable_cb = QCheckBox("Enable Attack Automation")
        self.enable_cb.setStyleSheet("font-size: 12pt;")
        enable_layout.addWidget(self.enable_cb)
        layout.addWidget(enable_grp)

        settings_grp = QGroupBox("Target Settings")
        form = QFormLayout(settings_grp)

        self.zone_id = QSpinBox()
        self.zone_id.setRange(1, 9999)
        self.zone_id.setValue(507)
        form.addRow("Zone ID:", self.zone_id)

        self.point_id = QSpinBox()
        self.point_id.setRange(1, 255)
        self.point_id.setValue(59)
        form.addRow("Point ID:", self.point_id)

        self.cooldown = QSpinBox()
        self.cooldown.setRange(30, 3600)
        self.cooldown.setValue(300)
        form.addRow("Cooldown (s):", self.cooldown)

        self.rally_cb = QCheckBox("Rally Mode")
        form.addRow("Rally:", self.rally_cb)

        self.loop_cb = QCheckBox("Loop indefinitely")
        self.loop_cb.setChecked(False)
        form.addRow("Loop:", self.loop_cb)

        layout.addWidget(settings_grp)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("⚔️ Attack", objectName="primary")
        self.btn_start.setStyleSheet("QPushButton#primary { background: #e94560; }")
        self.btn_start.clicked.connect(self.start_attack)
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_attack)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.log = QTextEdit()
        self.log.setMaximumHeight(150)
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("<b>Battle Log</b>"))
        layout.addWidget(self.log)
        layout.addStretch()

    def log_msg(self, msg):
        self.log.append(msg)

    def start_attack(self):
        self.log_msg("[*] Initializing attacker...")
        try:
            self.bot = AttackerBot()
        except RuntimeError as e:
            self.log_msg(f"[!] {e}")
            return

        zone = self.zone_id.value()
        point = self.point_id.value()
        loop = self.loop_cb.isChecked()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log_msg(f"[*] Attacking zone={zone}, point={point}")

        def task():
            if loop:
                while True:
                    self.bot.attack(zone, point)
                    import time
                    time.sleep(self.cooldown.value())
            else:
                self.bot.attack(zone, point)

        self.worker = BotWorker(task)
        self.worker.log_signal.connect(self.log_msg)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def stop_attack(self):
        if self.worker:
            self.worker.terminate()
            self.log_msg("[*] Attack stopped")
        self.on_finished()

    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)


class RedeemerPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.bot = RedeemerBot()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        enable_grp = QGroupBox("Gift Code Redemption")
        form = QFormLayout(enable_grp)

        self.gift_code = QLineEdit()
        self.gift_code.setPlaceholderText("Enter gift code...")
        self.gift_code.setText("LM2026")
        form.addRow("Gift Code:", self.gift_code)

        self.batch_codes = QTextEdit()
        self.batch_codes.setPlaceholderText("One code per line for batch redemption...")
        self.batch_codes.setMaximumHeight(80)
        form.addRow("Batch Codes:", self.batch_codes)

        btn_layout = QHBoxLayout()
        self.btn_redeem = QPushButton("🎁 Redeem Single", objectName="primary")
        self.btn_redeem.setStyleSheet("QPushButton#primary { background: #e94560; }")
        self.btn_redeem.clicked.connect(self.redeem_single)
        self.btn_batch = QPushButton("🎁🎁 Redeem Batch")
        self.btn_batch.clicked.connect(self.redeem_batch)
        btn_layout.addWidget(self.btn_redeem)
        btn_layout.addWidget(self.btn_batch)
        btn_layout.addStretch()
        form.addRow("", btn_layout)

        layout.addWidget(enable_grp)

        self.log = QTextEdit()
        self.log.setMaximumHeight(200)
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("<b>Redemption Log</b>"))
        layout.addWidget(self.log)
        layout.addStretch()

    def log_msg(self, msg):
        self.log.append(msg)

    def redeem_single(self):
        code = self.gift_code.text().strip()
        if not code:
            self.log_msg("[!] Please enter a gift code")
            return
        self.log_msg(f"[*] Redeeming: {code}")
        success = self.bot.redeem(code)
        self.log_msg(f"{'✅' if success else '❌'} Result: {'Success' if success else 'Failed'}")

    def redeem_batch(self):
        codes = [c.strip() for c in self.batch_codes.toPlainText().split("\n") if c.strip()]
        if not codes:
            self.log_msg("[!] No codes entered")
            return
        self.log_msg(f"[*] Batch redemption: {len(codes)} codes")
        results = self.bot.batch_redeem(codes)
        for code, success in results.items():
            self.log_msg(f"{'✅' if success else '❌'} {code}: {'Success' if success else 'Failed'}")


class ExplorerPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.bot = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        enable_grp = QGroupBox("Map Explorer")
        form = QFormLayout(enable_grp)

        self.start_x = QSpinBox()
        self.start_x.setRange(0, 9999)
        self.start_x.setValue(400)
        form.addRow("Start X:", self.start_x)

        self.start_y = QSpinBox()
        self.start_y.setRange(0, 9999)
        self.start_y.setValue(300)
        form.addRow("Start Y:", self.start_y)

        self.grid_size = QSpinBox()
        self.grid_size.setRange(2, 10)
        self.grid_size.setValue(3)
        form.addRow("Grid Size:", self.grid_size)

        btn_layout = QHBoxLayout()
        self.btn_scan = QPushButton("🗺️ Start Scan", objectName="primary")
        self.btn_scan.setStyleSheet("QPushButton#primary { background: #e94560; }")
        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addStretch()
        form.addRow("", btn_layout)

        layout.addWidget(enable_grp)

        self.log = QTextEdit()
        self.log.setMaximumHeight(200)
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("<b>Scan Log</b>"))
        layout.addWidget(self.log)
        layout.addStretch()

    def log_msg(self, msg):
        self.log.append(msg)

    def start_scan(self):
        self.bot = ExplorerBot()
        sx, sy = self.start_x.value(), self.start_y.value()
        gs = self.grid_size.value()

        self.btn_scan.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log_msg(f"[*] Starting exploration: grid={gs}x{gs} from ({sx}, {sy})")

        def task():
            return self.bot.run_exploration(sx, sy, gs)

        self.worker = BotWorker(task)
        self.worker.log_signal.connect(self.log_msg)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def stop_scan(self):
        if self.worker:
            self.worker.terminate()
            self.log_msg("[*] Scan stopped")
        self.on_finished()

    def on_finished(self):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)


class FSMPanel(QWidget):
    """Autonomous FSM engine control."""

    def __init__(self):
        super().__init__()
        self.engine = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        status_grp = QGroupBox("FSM Engine Status")
        status_layout = QFormLayout(status_grp)

        self.status_label = QLabel("⚪ Stopped")
        self.status_label.setStyleSheet("font-size: 14pt; color: #aaa;")
        status_layout.addRow("Status:", self.status_label)

        self.state_label = QLabel("IDLE")
        self.state_label.setStyleSheet("font-size: 12pt; color: #00ff88;")
        status_layout.addRow("State:", self.state_label)

        self.game_label = QLabel("❓ Unknown")
        status_layout.addRow("Game:", self.game_label)

        layout.addWidget(status_grp)

        features_grp = QGroupBox("Enabled Features")
        features_layout = QVBoxLayout(features_grp)

        self.cb_gather = QCheckBox("Auto Gather Resources")
        self.cb_gather.setChecked(True)
        self.cb_attack = QCheckBox("Auto Attack")
        self.cb_tutorial = QCheckBox("Auto Evade Tutorial")
        self.cb_tutorial.setChecked(True)
        self.cb_explore = QCheckBox("Auto Explore")

        features_layout.addWidget(self.cb_gather)
        features_layout.addWidget(self.cb_attack)
        features_layout.addWidget(self.cb_tutorial)
        features_layout.addWidget(self.cb_explore)
        layout.addWidget(features_grp)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start Engine", objectName="primary")
        self.btn_start.setStyleSheet("QPushButton#primary { background: #e94560; font-size: 11pt; }")
        self.btn_start.clicked.connect(self.start_engine)
        self.btn_stop = QPushButton("■ Stop Engine")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_engine)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

        # Poll FSM status
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_status)
        self.timer.setInterval(2000)

        self.log = QTextEdit()
        self.log.setMaximumHeight(120)
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("<b>FSM Log</b>"))
        layout.addWidget(self.log)
        layout.addStretch()

    def log_msg(self, msg):
        self.log.append(msg)

    def poll_status(self):
        if self.engine:
            s = self.engine.status
            self.state_label.setText(s.get("state", "?").upper())
            self.game_label.setText("🟢 Detected" if s.get("game_detected") else "🔴 Not Found")

    def start_engine(self):
        try:
            self.engine = FSMBotEngine()
        except Exception as e:
            self.log_msg(f"[!] Engine init failed: {e}")
            return

        self.engine.start()
        self.timer.start()
        self.status_label.setText("🟢 Running")
        self.status_label.setStyleSheet("font-size: 14pt; color: #00ff88;")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log_msg("[*] FSM Engine started — autonomous mode active")

    def stop_engine(self):
        if self.engine:
            self.engine.stop()
        self.timer.stop()
        self.status_label.setText("⚪ Stopped")
        self.status_label.setStyleSheet("font-size: 14pt; color: #aaa;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.state_label.setText("IDLE")
        self.game_label.setText("❓ Unknown")
        self.log_msg("[*] FSM Engine stopped")


# ──────────────────────────────────────────────
#  Settings Window
# ──────────────────────────────────────────────
class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # General tab
        general = QWidget()
        gen_layout = QFormLayout(general)

        self.process_name = QLineEdit("Lords Mobile PC")
        gen_layout.addRow("Process Name:", self.process_name)

        self.resolution_w = QSpinBox()
        self.resolution_w.setRange(800, 3840)
        self.resolution_w.setValue(1280)
        self.resolution_h = QSpinBox()
        self.resolution_h.setRange(600, 2160)
        self.resolution_h.setValue(720)
        res_layout = QHBoxLayout()
        res_layout.addWidget(self.resolution_w)
        res_layout.addWidget(QLabel("×"))
        res_layout.addWidget(self.resolution_h)
        res_layout.addStretch()
        gen_layout.addRow("Resolution:", res_layout)

        self.click_delay = QSpinBox()
        self.click_delay.setRange(10, 500)
        self.click_delay.setValue(50)
        gen_layout.addRow("Click Delay (ms):", self.click_delay)

        self.network_timeout = QSpinBox()
        self.network_timeout.setRange(1, 60)
        self.network_timeout.setValue(5)
        gen_layout.addRow("Network Timeout (s):", self.network_timeout)

        tabs.addTab(general, "General")

        # Anti-ban tab
        antiban = QWidget()
        ab_layout = QFormLayout(antiban)

        self.randomize_cb = QCheckBox()
        self.randomize_cb.setChecked(True)
        ab_layout.addRow("Randomize Clicks:", self.randomize_cb)

        self.max_actions = QSpinBox()
        self.max_actions.setRange(1, 100)
        self.max_actions.setValue(10)
        ab_layout.addRow("Max Actions/Min:", self.max_actions)

        self.cooldown = QSpinBox()
        self.cooldown.setRange(60, 3600)
        self.cooldown.setValue(300)
        ab_layout.addRow("Cycle Cooldown (s):", self.cooldown)

        tabs.addTab(antiban, "Anti-Ban")

        # Network tab
        network = QWidget()
        net_layout = QFormLayout(network)

        self.server_host = QLineEdit("205.252.125.129")
        net_layout.addRow("Server Host:", self.server_host)

        self.server_port = QSpinBox()
        self.server_port.setRange(1, 65535)
        self.server_port.setValue(11977)
        net_layout.addRow("Server Port:", self.server_port)

        tabs.addTab(network, "Network")

        layout.addWidget(tabs)

        # Save/Cancel
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        settings = {
            "game": {
                "window_title": self.process_name.text(),
                "resolution": {
                    "width": self.resolution_w.value(),
                    "height": self.resolution_h.value()
                }
            },
            "timing": {
                "click_delay_ms": self.click_delay.value(),
                "network_timeout": self.network_timeout.value(),
                "march_wait_seconds": self.cooldown.value()
            },
            "anti_ban": {
                "randomize_clicks": self.randomize_cb.isChecked(),
                "max_actions_per_minute": self.max_actions.value(),
                "cooldown_between_cycles": self.cooldown.value()
            },
            "network": {
                "server": {
                    "host": self.server_host.text(),
                    "port": self.server_port.value()
                }
            }
        }

        cfg_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg_path, "w") as f:
            json.dump(settings, f, indent=2)

        QMessageBox.information(self, "Saved", "Settings saved successfully.")
        self.close()


# ──────────────────────────────────────────────
#  Main Window
# ──────────────────────────────────────────────
class LordsBotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lords Mobile Bot — Control Center")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(DARK_STYLE)

        self.init_ui()
        self.create_menu()

    def init_ui(self):
        # Central widget with tabs
        tabs = QTabWidget()

        # Tab 1: Dashboard
        dashboard = QWidget()
        dash_layout = QVBoxLayout(dashboard)

        # Top stats bar
        stats_layout = QHBoxLayout()
        self.stat_accounts = QLabel("Accounts: 1")
        self.stat_status = QLabel("Status: 🟡 Idle")
        self.stat_uptime = QLabel("Uptime: 00:00:00")
        for lbl in [self.stat_accounts, self.stat_status, self.stat_uptime]:
            lbl.setStyleSheet("padding: 6px 12px; background: #16213e; border-radius: 4px;")
        stats_layout.addWidget(self.stat_accounts)
        stats_layout.addWidget(self.stat_status)
        stats_layout.addWidget(self.stat_uptime)
        stats_layout.addStretch()
        dash_layout.addLayout(stats_layout)

        # Quick action buttons
        quick_layout = QHBoxLayout()
        for txt, icon in [("🚀 Quick Gather", "▶"), ("⚔️ Quick Attack", "⚔️"),
                          ("🎁 Quick Redeem", "🎁"), ("🗺️ Explore", "🗺️")]:
            btn = QPushButton(f"{icon} {txt}")
            btn.setMinimumHeight(50)
            btn.setStyleSheet("font-size: 11pt;")
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        dash_layout.addLayout(quick_layout)

        # FSM Control
        fsm_grp = QGroupBox("Autonomous Mode (FSM Engine)")
        fsm_layout = QHBoxLayout(fsm_grp)

        self.fsm_status = QLabel("⚠️ Engine Off")
        self.fsm_status.setStyleSheet("font-size: 13pt; color: #aaa;")
        self.fsm_btn = QPushButton("▶ Start Autonomous")
        self.fsm_btn.setStyleSheet("font-size: 11pt; background: #e94560;")
        self.fsm_btn.setMinimumHeight(40)
        fsm_layout.addWidget(self.fsm_status)
        fsm_layout.addWidget(self.fsm_btn)
        fsm_layout.addStretch()
        dash_layout.addWidget(fsm_grp)

        # Activity log
        dash_layout.addWidget(QLabel("<b>Global Activity Log</b>"))
        self.global_log = QTextEdit()
        self.global_log.setReadOnly(True)
        self.global_log.setStyleSheet("background: #0d0d1a; color: #00ff88; font-family: 'Courier New'; font-size: 9pt;")
        dash_layout.addWidget(self.global_log)

        tabs.addTab(dashboard, "🏠 Dashboard")

        # Tab 2: Accounts
        tabs.addTab(AccountManager(), "👥 Accounts")

        # Tab 3: Gatherer
        tabs.addTab(GathererPanel(), "🚜 Gatherer")

        # Tab 4: Attacker
        tabs.addTab(AttackerPanel(), "⚔️ Attacker")

        # Tab 5: Redeemer
        tabs.addTab(RedeemerPanel(), "🎁 Redeemer")

        # Tab 6: Explorer
        tabs.addTab(ExplorerPanel(), "🗺️ Explorer")

        # Tab 7: FSM
        tabs.addTab(FSMPanel(), "🤖 FSM Engine")

        self.setCentralWidget(tabs)

        # Status bar
        self.statusBar().showMessage("Ready")

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("Settings", self.open_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def open_settings(self):
        self.settings_win = SettingsWindow()
        self.settings_win.show()

    def show_about(self):
        QMessageBox.about(self, "About Lords Bot",
                          "<b>Lords Mobile Bot</b><br>"
                          "Version 2.0 — Refactored<br><br>"
                          "Advanced automation for Lords Mobile<br>"
                          "Multi-account, multi-feature support")


# ──────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    window = LordsBotWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
