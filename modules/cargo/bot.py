"""
modules/cargo/bot.py — Cargo Ship Bot
Automatically claims cargo ship resources at configurable intervals.
Phase 3 Anti-Detection: randomized timing throughout.
"""

import time
import json
from pathlib import Path

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard


# Default cargo button positions (adjust to game resolution)
DEFAULT_CARGO_POSITIONS = {
    "cargo_button": (850, 580),
    "claim_button": (540, 400),
    "close_button": (870, 155),
}


class CargoBot:
    """
    Win32 macro-based cargo ship claiming.
    Navigates to cargo UI and claims available resources.
    Phase 3 Anti-Detection: session guarding and randomized timing.
    """

    def __init__(self):
        self.radar = MemoryRadar()
        self.hands = Win32GhostClient()
        self.anti_detection = AntiDetection()
        self.session_guard = SessionGuard()
        self._load_config()
        self.active = False

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

        self.resolution = self._cfg["game"]["resolution"]
        self.refresh_interval = self._cfg.get("cargo", {}).get("refresh_interval_seconds", 300)
        self.auto_refresh = self._cfg.get("cargo", {}).get("auto_refresh", True)

        # Load positions from config or use defaults
        cargo_cfg = self._cfg.get("cargo", {}).get("positions", DEFAULT_CARGO_POSITIONS)
        self.cargo_btn = tuple(cargo_cfg.get("cargo_button", DEFAULT_CARGO_POSITIONS["cargo_button"]))
        self.claim_btn = tuple(cargo_cfg.get("claim_button", DEFAULT_CARGO_POSITIONS["claim_button"]))
        self.close_btn = tuple(cargo_cfg.get("close_button", DEFAULT_CARGO_POSITIONS["close_button"]))

    def verify_ready(self) -> bool:
        """Check that game is running and accessible."""
        if not self.radar.clients:
            print("[!] CargoBot: Game not detected. Is Lords Mobile running?")
            return False
        if not self.hands.hwnd:
            print("[!] CargoBot: Game window not found.")
            return False
        return True

    def _click(self, x: int, y: int, delay_ms: float = None) -> None:
        """Click with anti-detection humanization."""
        delay = delay_ms or self.anti_detection.random_action_delay()
        self.hands.vClick(x, y, delay_ms=delay)

    def claim_cargo(self) -> bool:
        """
        Navigate to cargo ship and claim available resources.
        Returns True if cargo was successfully claimed.
        """
        try:
            if not self.session_guard.should_act("cargo"):
                print("[*] CargoBot: Rate limit reached, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            # 1. Click cargo ship button
            self._click(*self.cargo_btn)
            delay = self.anti_detection.human_delay(min_ms=1200, max_ms=2500)
            time.sleep(delay / 1000)

            # 2. Check if cargo is available (look for claim button)
            # Click claim button
            self._click(*self.claim_btn)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 3. Confirm claim (might need second click depending on UI)
            self._click(*self.claim_btn)
            delay = self.anti_detection.human_delay(min_ms=600, max_ms=1200)
            time.sleep(delay / 1000)

            # 4. Close cargo UI
            self._click(*self.close_btn)
            delay = self.anti_detection.human_delay(min_ms=400, max_ms=800)
            time.sleep(delay / 1000)

            self.session_guard.record_action("cargo")
            print("[+] CargoBot: Cargo claimed successfully")
            return True

        except Exception as e:
            print(f"[!] Cargo claim failed: {e}")
            return False

    def run_cycle(self) -> None:
        """
        Run one cargo claiming cycle.
        Waits for refresh interval between cycles.
        """
        if not self.verify_ready():
            return

        if self.session_guard.enforced_cooldown():
            remaining = self.session_guard.cooldown_remaining
            print(f"[*] CargoBot: In cooldown, {remaining:.0f}s remaining")
            return

        print(f"[*] CargoBot: Claiming cargo (refresh interval: {self.refresh_interval}s)")
        success = self.claim_cargo()

        if success:
            if self.auto_refresh:
                # Add some jitter to the refresh interval
                jitter = self.anti_detection.jitter(
                    int(self.refresh_interval * 1000),
                    variance_pct=0.15
                )
                wait_seconds = jitter / 1000
                print(f"[*] Waiting {wait_seconds:.1f}s until next cargo claim...")
                time.sleep(wait_seconds)
        else:
            # Retry after a shorter delay on failure
            retry_delay = self.anti_detection.human_delay(min_ms=5000, max_ms=10000)
            print(f"[*] Retrying in {retry_delay / 1000:.1f}s...")
            time.sleep(retry_delay / 1000)

        print("[+] CargoBot: Cycle complete")
