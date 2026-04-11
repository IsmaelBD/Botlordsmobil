"""
modules/shelter/bot.py — Shelter / Shield Management
Automatically shields troops when under attack or when troops are at risk.
Manages shelter: moves troops to/from shelter for protection.
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient


DEFAULT_SHELTER_UI = {
    "shield_button": (400, 600),          # Shield button in hero bar
    "shield_menu": (400, 580),            # Shield options dropdown
    "shield_1h": (400, 400),              # 1-hour shield option
    "shield_3h": (400, 450),              # 3-hour shield option
    "shield_8h": (400, 500),              # 8-hour shield option
    "shelter_button": (240, 600),         # Shelter button
    "shelter_deposit": (500, 400),        # Deposit troops to shelter
    "shelter_withdraw": (500, 480),       # Withdraw troops from shelter
    "select_all_troops": (300, 300),       # Select all troops
    "confirm_btn": (640, 430),            # Confirm action
    "close_btn": (860, 120),              # Close UI
}


class ShelterBot:
    """
    Win32 macro-based shelter and shield management.
    Configurable thresholds: shield when X% of troops are at risk.
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
        self.check_interval = self._cfg["timing"].get("shelter_check_seconds", 60)
        self.ui = self._cfg.get("ui_coords", {}).get("shelter", DEFAULT_SHELTER_UI)

        # Shield threshold: activate shield when this % of troops are at risk
        self.shield_threshold = self._cfg.get("shelter", {}).get("shield_threshold_pct", 30)
        # Default shield duration
        self.shield_duration = self._cfg.get("shelter", {}).get("default_shield_duration", "3h")
        # Auto-shelter: automatically move troops to shelter
        self.auto_shelter = self._cfg.get("shelter", {}).get("auto_shelter", True)

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

    def activate_shield(self, duration: str = None) -> bool:
        """
        Activate a shield of the given duration.
        duration: '1h', '3h', or '8h'
        """
        duration = duration or self.shield_duration
        duration_map = {
            "1h": self.ui["shield_1h"],
            "3h": self.ui["shield_3h"],
            "8h": self.ui["shield_8h"],
        }
        coords = duration_map.get(duration, self.ui["shield_3h"])

        try:
            self._click(self.ui["shield_button"])
            time.sleep(1.5)
            self._click(coords)
            time.sleep(1.0)
            print(f"[{datetime.now():%H:%M:%S}] [+] Shield activated ({duration})")
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Activate shield failed: {e}")
            return False

    def deactivate_shield(self) -> bool:
        """Turn off the active shield."""
        try:
            self._click(self.ui["shield_button"])
            time.sleep(1.5)
            # Click the "remove shield" option if visible
            self.hands.vClick(400, 550)  # Typically "remove" option
            time.sleep(1.0)
            print(f"[{datetime.now():%H:%M:%S}] [+] Shield deactivated")
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Deactivate shield failed: {e}")
            return False

    def move_to_shelter(self) -> bool:
        """
        Move all troops to shelter for protection.
        """
        try:
            self._click(self.ui["shelter_button"])
            time.sleep(2.0)
            self._click(self.ui["select_all_troops"])
            time.sleep(0.8)
            self._click(self.ui["shelter_deposit"])
            time.sleep(1.0)
            self._click(self.ui["confirm_btn"])
            time.sleep(1.5)
            print(f"[{datetime.now():%H:%M:%S}] [+] Troops moved to shelter")
            self.close_shelter()
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Move to shelter failed: {e}")
            return False

    def withdraw_from_shelter(self) -> bool:
        """
        Withdraw troops from shelter back to castle.
        """
        try:
            self._click(self.ui["shelter_button"])
            time.sleep(2.0)
            self._click(self.ui["shelter_withdraw"])
            time.sleep(1.0)
            self._click(self.ui["confirm_btn"])
            time.sleep(1.5)
            print(f"[{datetime.now():%H:%M:%S}] [+] Troops withdrawn from shelter")
            self.close_shelter()
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Withdraw from shelter failed: {e}")
            return False

    def close_shelter(self) -> bool:
        """Close the shelter UI."""
        try:
            self._click(self.ui["close_btn"])
            time.sleep(1.0)
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Close shelter failed: {e}")
            return False

    def check_risk(self) -> int:
        """
        Read troop risk percentage from game memory.
        Returns approximate % of troops at risk (0-100).
        """
        if not self.radar.clients:
            return 0

        try:
            client = self.radar.clients[0]
            state = self.radar.get_player_state(client["handle"], client["assembly_base"])
            # Estimate based on attack notifications / online status
            # This is a simplified placeholder — real impl would read actual troop state
            risk = state.get("TroopRiskPct", 0) if state else 0
            return risk
        except Exception:
            return 0

    def run_cycle(self) -> bool:
        """
        Run one shelter management cycle.
        Checks troop risk → decides whether to shield or shelter.
        """
        if not self.verify_ready():
            return False

        print(f"[{datetime.now():%H:%M:%S}] [*] Shelter cycle started")
        risk = self.check_risk()
        print(f"[{datetime.now():%H:%M:%S}] [*] Troop risk: {risk}%")

        if risk >= self.shield_threshold:
            if self.auto_shelter:
                print(f"[{datetime.now():%H:%M:%S}] [*] Moving troops to shelter (risk={risk}%)")
                self.move_to_shelter()
            else:
                print(f"[{datetime.now():%H:%M:%S}] [*] Activating shield (risk={risk}%)")
                self.activate_shield()

        print(f"[{datetime.now():%H:%M:%S}] [+] Shelter cycle complete")
        return True

    def run_loop(self, interval: int = None) -> None:
        """Run shelter monitoring in a continuous loop."""
        interval = interval or self.check_interval
        self.active = True
        print(f"[{datetime.now():%H:%M:%S}] [*] Shelter loop started — interval {interval}s")

        while self.active:
            self.run_cycle()
            for _ in range(interval):
                if not self.active:
                    break
                time.sleep(1)

        print(f"[{datetime.now():%H:%M:%S}] [*] Shelter loop stopped")

    def stop(self) -> None:
        """Stop the automation loop."""
        self.active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def start_loop(self, interval: int = None) -> None:
        """Start shelter loop in a background thread."""
        if self._thread and self._thread.is_alive():
            print(f"[{datetime.now():%H:%M:%S}] [!] Shelter loop already running")
            return
        self._thread = threading.Thread(
            target=self.run_loop,
            args=(interval,),
            daemon=True
        )
        self._thread.start()
