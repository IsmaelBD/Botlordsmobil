"""
modules/reporter/bot.py — Periodic Reporter
Runs in background, periodically takes snapshots and sends reports.
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List

from utils.analytics import BotAnalytics
from utils.report_generator import ReportGenerator


class ReporterBot:
    """
    Background reporter that periodically:
    - Takes player state snapshots
    - Logs resource changes
    - Sends notifications to configured channels
    """

    def __init__(self, account_name: str = "default"):
        self.analytics = BotAnalytics(account_name)
        self.reporter = ReportGenerator(self.analytics)
        self.enabled = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval = 3600  # Default: 1 hour
        self._callbacks: List[Callable] = []

        self._load_config()

    def _load_config(self) -> None:
        """Load reporter configuration from settings.json."""
        cfg_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
        if cfg_path.exists():
            try:
                with open(cfg_path) as f:
                    cfg = json.load(f)
                analytics_cfg = cfg.get("analytics", {})
                self._interval = analytics_cfg.get("snapshot_interval_seconds", 3600)
                self._report_channels = analytics_cfg.get("report_channels", ["local"])
                self.enabled = analytics_cfg.get("enabled", False)
            except (json.JSONDecodeError, IOError):
                self._report_channels = ["local"]
        else:
            self._report_channels = ["local"]

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback function to be called with report text."""
        self._callbacks.append(callback)

    def enable(self, interval_seconds: int = None) -> None:
        """Start periodic reporting in background thread."""
        if self.enabled and self._thread and self._thread.is_alive():
            return

        if interval_seconds is not None:
            self._interval = interval_seconds

        self.enabled = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._reporting_loop, daemon=True)
        self._thread.start()
        print(f"[*] Reporter started — interval: {self._interval}s, channels: {self._report_channels}")

    def disable(self) -> None:
        """Stop periodic reporting."""
        self.enabled = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("[*] Reporter stopped")

    def _reporting_loop(self) -> None:
        """Main reporting loop."""
        while not self._stop_event.is_set():
            try:
                self.take_snapshot()
                self._send_reports()
            except Exception as e:
                print(f"[!] Reporter error: {e}")

            # Wait for interval or stop signal
            self._stop_event.wait(timeout=self._interval)

    def take_snapshot(self) -> None:
        """Take a full player state snapshot now."""
        # This will be called by FSM engine with actual state
        # For now, just record the snapshot time
        print(f"[*] Snapshot taken at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def snapshot_player(self, player_state: dict) -> None:
        """Take a snapshot with actual player state data."""
        self.analytics.snapshot_player_state(player_state)
        self._notify_callbacks(f"Snapshot: Might {player_state.get('Might', 0):,}")

    def _send_reports(self) -> None:
        """Send reports to all configured channels."""
        report = self.reporter.daily_summary()

        for channel in self._report_channels:
            if channel == "local":
                self._save_local_report(report)
            elif channel == "discord":
                self._send_discord_report(report)
            elif channel == "webhook":
                self._send_webhook_report(report)

    def _save_local_report(self, report: str) -> None:
        """Save report to local file."""
        reports_dir = self.analytics.data_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        report_file = reports_dir / f"report_{today}.txt"

        with open(report_file, "a") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n")
            f.write(report)
            f.write("\n")

        print(f"[*] Local report saved: {report_file}")

    def _send_discord_report(self, report: str) -> None:
        """Send report to Discord (via callback)."""
        self._notify_callbacks(f"📊 **Daily Report**\n```\n{report}\n```")

    def _send_webhook_report(self, report: str) -> None:
        """Send report via webhook."""
        # Webhook URL would be loaded from config
        # For now, just notify via callback
        self._notify_callbacks(f"Webhook Report:\n{report}")

    def _notify_callbacks(self, message: str) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"[!] Callback error: {e}")

    def send_daily_report(self, channel: str = "local") -> str:
        """Send daily summary report to specified channel."""
        report = self.reporter.full_report()

        if channel == "local":
            self._save_local_report(report)
            return "Report saved locally"
        elif channel == "discord":
            self._notify_callbacks(f"📊 **Daily Report**\n```\n{report}\n```")
            return "Report sent to Discord"
        elif channel == "webhook":
            self._send_webhook_report(report)
            return "Report sent via webhook"
        else:
            return f"Unknown channel: {channel}"

    def send_custom_report(self, report_type: str = "daily") -> str:
        """Generate and send a specific type of report."""
        if report_type == "daily":
            report = self.reporter.daily_summary()
        elif report_type == "weekly":
            report = self.reporter.weekly_trends()
        elif report_type == "attacks":
            report = self.reporter.attack_log()
        elif report_type == "might":
            report = self.reporter.might_progress()
        elif report_type == "resources":
            report = self.reporter.resource_chart()
        elif report_type == "full":
            report = self.reporter.full_report()
        else:
            return f"Unknown report type: {report_type}"

        self._save_local_report(report)
        return report

    @property
    def status(self) -> dict:
        """Get reporter status."""
        return {
            "enabled": self.enabled,
            "interval_seconds": self._interval,
            "channels": self._report_channels,
            "running": self._thread.is_alive() if self._thread else False,
            "session_stats": self.analytics.get_session_stats(),
            "history_stats": self.analytics.get_history_stats(),
        }


# Standalone test
if __name__ == "__main__":
    reporter = ReporterBot()

    # Simulate some data
    reporter.analytics.record_resource_gather("gold", 1000)
    reporter.analytics.record_resource_gather("food", 500)
    reporter.analytics.record_attack(507, 59, "success", troops_deployed=100, kills=50, losses=10)
    reporter.analytics.record_march_return(300, 50, {"gold": 500, "food": 200})

    print(reporter.reporter.full_report())
