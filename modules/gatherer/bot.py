"""
modules/gatherer/bot.py — Resource Gathering Bot
Automatically sends troops to harvest resources from the map.
"""

import time
import json
from pathlib import Path

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient


class GathererBot:
    """Win32 macro-based resource gathering."""

    def __init__(self):
        self.radar = MemoryRadar()
        self.hands = Win32GhostClient()
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

    def gather_at(self, x: int, y: int) -> bool:
        """Click sequence to send a march to coordinates (x, y)."""
        try:
            # 1. Open global map
            self.hands.vClick(80, 622)
            time.sleep(2.5)

            # 2. Click resource node
            self.hands.vClick(x, y)
            time.sleep(1.2)

            # 3. Click gather option
            self.hands.vClick(528, 298)
            time.sleep(1.2)

            # 4. Select max troops
            self.hands.vClick(583, 252)
            time.sleep(1.5)

            # 5. Deploy march
            self.hands.vClick(787, 460)
            print(f"[+] March dispatched to ({x}, {y})")
            return True

        except Exception as e:
            print(f"[!] Gather failed: {e}")
            return False

    def run_cycle(self, targets: list[tuple[int, int]]) -> None:
        """Run one gathering cycle through a list of targets."""
        if not self.verify_ready():
            return

        print(f"[*] Starting gather cycle with {len(targets)} targets")
        for i, (x, y) in enumerate(targets):
            print(f"[*] Target {i+1}/{len(targets)}: ({x}, {y})")
            self.gather_at(x, y)
            if i < len(targets) - 1:
                print(f"[*] Waiting {self.march_wait}s before next target...")
                time.sleep(self.march_wait)

        print("[+] Gather cycle complete")
