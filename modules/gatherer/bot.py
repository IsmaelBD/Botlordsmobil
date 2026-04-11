"""
modules/gatherer/bot.py — Resource Gathering Bot
Automatically sends troops to harvest resources from the map.
Phase 3 Anti-Detection: randomized timing throughout.
"""

import time
import json
from pathlib import Path

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard


class GathererBot:
    """Win32 macro-based resource gathering with anti-detection."""

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
        self.click_delay = self._cfg["timing"]["click_delay_ms"] / 1000
        self.march_wait = self._cfg["timing"]["march_wait_seconds"]

    def verify_ready(self) -> bool:
        """Check that game is running and accessible."""
        if not self.radar.clients:
            print("[!] Game not detected. Is Lords Mobile running?")
            return False
        if not self.hands.hwnd:
            print("[!] Game window not found.")
            return False
        return True

    def _click(self, x: int, y: int, delay_ms: float = None) -> None:
        """Click with anti-detection humanization."""
        delay = delay_ms or self.anti_detection.random_action_delay()
        self.hands.vClick(x, y, delay_ms=delay)

    def gather_at(self, x: int, y: int) -> bool:
        """Click sequence to send a march to coordinates (x, y)."""
        try:
            # Check rate limiting before acting
            if not self.session_guard.should_act("gather"):
                print("[*] GathererBot: Rate limit reached, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            # 1. Open global map
            self._click(80, 622)
            delay = self.anti_detection.human_delay(min_ms=1500, max_ms=3000)
            time.sleep(delay / 1000)

            # 2. Click resource node
            self._click(x, y)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 3. Click gather option
            self._click(528, 298)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 4. Select max troops
            self._click(583, 252)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 5. Deploy march
            self._click(787, 460)

            # Record action for rate limiting
            self.session_guard.record_action("gather")
            print(f"[+] March dispatched to ({x}, {y})")
            return True

        except Exception as e:
            print(f"[!] Gather failed: {e}")
            return False

    def run_cycle(self, targets: list[tuple[int, int]]) -> None:
        """Run one gathering cycle through a list of targets."""
        if not self.verify_ready():
            return

        # Check if we should cooldown between cycles
        if self.session_guard.enforced_cooldown():
            remaining = self.session_guard.cooldown_remaining
            print(f"[*] GathererBot: In cooldown, {remaining:.0f}s remaining")
            return

        print(f"[*] Starting gather cycle with {len(targets)} targets")
        for i, (x, y) in enumerate(targets):
            print(f"[*] Target {i+1}/{len(targets)}: ({x}, {y})")
            success = self.gather_at(x, y)
            if success and i < len(targets) - 1:
                # Use randomized cycle delay instead of fixed march_wait
                cycle_delay = self.anti_detection.random_cycle_delay()
                print(f"[*] Waiting {cycle_delay:.1f}s before next target...")
                time.sleep(cycle_delay)

        print("[+] Gather cycle complete")
