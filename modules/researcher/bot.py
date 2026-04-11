"""
modules/researcher/bot.py — Research Automation
Automates lab/research building upgrades via Win32 macro UI.
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient


# Default research UI click coordinates (relative to game window)
DEFAULT_UI = {
    "lab_button": (160, 615),      # Lab/research building button
    "research_tab": (200, 300),    # Research tab in building
    "research_slot_1": (300, 350), # First research slot
    "research_slot_2": (300, 420), # Second research slot (if available)
    "upgrade_btn": (700, 450),     # Upgrade/Start button
    "speed_up_btn": (750, 450),    # Speed up button
    "close_btn": (860, 120),      # Close building UI
}


class ResearcherBot:
    """
    Win32 macro-based research automation.
    Configurable research queue priorities (attack, defense, resource, etc.)
    """

    def __init__(self):
        self.radar = MemoryRadar()
        self.hands = Win32GhostClient()
        self._load_config()
        self.active = False
        self._thread: threading.Thread = None

    def _load_config(self) -> None:
        cfg_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg_path) as f:
            self._cfg = json.load(f)

        self.click_delay = self._cfg["timing"]["click_delay_ms"] / 1000
        self.cycle_wait = self._cfg["timing"].get("research_cycle_seconds", 300)
        self.ui = self._cfg.get("ui_coords", {}).get("research", DEFAULT_UI)

        # Research priorities: list of research types in priority order
        self.priorities = self._cfg.get("research_priorities", [
            "attack", "defense", "resource", "trap", "life"
        ])

    def verify_ready(self) -> bool:
        """Check that game is running and window is accessible."""
        if not self.radar.clients:
            print(f"[{datetime.now():%H:%M:%S}] [!] Game not detected")
            return False
        if not self.hands.hwnd:
            print(f"[{datetime.now():%H:%M:%S}] [!] Game window not found")
            return False
        return True

    def _click(self, coords: tuple[int, int]) -> None:
        """Send a click with configured delay."""
        self.hands.vClick(*coords)
        time.sleep(self.click_delay)

    def open_lab(self) -> bool:
        """Open the research lab building UI."""
        try:
            self._click(self.ui["lab_button"])
            time.sleep(2.0)
            self._click(self.ui["research_tab"])
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Open lab failed: {e}")
            return False

    def start_research(self, slot: int = 1) -> bool:
        """
        Start research in the specified slot.
        slot: 1 or 2 (for dual research queue)
        """
        try:
            slot_coords = self.ui.get(
                f"research_slot_{slot}",
                (300, 350 if slot == 1 else 420)
            )
            self._click(slot_coords)
            time.sleep(1.0)
            self._click(self.ui["upgrade_btn"])
            print(f"[{datetime.now():%H:%M:%S}] [+] Research started in slot {slot}")
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Start research failed: {e}")
            return False

    def speed_up_research(self) -> bool:
        """Use gems/diamonds to speed up current research."""
        try:
            self._click(self.ui["speed_up_btn"])
            time.sleep(1.0)
            # Confirm speed up (click center or OK button)
            self.hands.vClick(640, 430)  # Typical OK button
            print(f"[{datetime.now():%H:%M:%S}] [+] Research speed-up triggered")
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Speed up failed: {e}")
            return False

    def close_lab(self) -> bool:
        """Close the research building UI."""
        try:
            self._click(self.ui["close_btn"])
            time.sleep(1.0)
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Close lab failed: {e}")
            return False

    def run_cycle(self, slot: int = 1) -> bool:
        """
        Run one research automation cycle.
        Opens lab, starts research in specified slot, closes lab.
        """
        if not self.verify_ready():
            return False

        print(f"[{datetime.now():%H:%M:%S}] [*] Research cycle started (slot {slot})")

        if not self.open_lab():
            return False

        if self.start_research(slot):
            pass  # Research started successfully

        self.close_lab()
        print(f"[{datetime.now():%H:%M:%S}] [+] Research cycle complete")
        return True

    def run_loop(self, slot: int = 1, interval: int = None) -> None:
        """
        Run research automation in a continuous loop.
        interval: seconds between cycles (defaults to config value)
        """
        interval = interval or self.cycle_wait
        self.active = True
        print(f"[{datetime.now():%H:%M:%S}] [*] Research loop started — interval {interval}s")

        while self.active:
            self.run_cycle(slot)
            for _ in range(interval):
                if not self.active:
                    break
                time.sleep(1)

        print(f"[{datetime.now():%H:%M:%S}] [*] Research loop stopped")

    def stop(self) -> None:
        """Stop the automation loop."""
        self.active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def start_loop(self, slot: int = 1, interval: int = None) -> None:
        """Start automation in a background thread."""
        if self._thread and self._thread.is_alive():
            print(f"[{datetime.now():%H:%M:%S}] [!] Research loop already running")
            return
        self._thread = threading.Thread(
            target=self.run_loop,
            args=(slot, interval),
            daemon=True
        )
        self._thread.start()
