"""
modules/trainer/bot.py — Troop Training Automation
Automates troop training in barracks and stable via Win32 macro UI.
Supports T1–T5 troop types with queue management.
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient


# Default barracks UI coordinates
DEFAULT_BARRACKS_UI = {
    "barracks_button": (165, 610),       # Barracks building button
    "stable_button": (205, 610),         # Stable building button
    "troop_tab": (220, 300),             # Troop training tab
    "t1_btn": (280, 350),                # T1 troop button
    "t2_btn": (350, 350),                # T2 troop button
    "t3_btn": (420, 350),                # T3 troop button
    "t4_btn": (490, 350),                # T4 troop button
    "t5_btn": (560, 350),                # T5 troop button
    "train_btn": (700, 450),             # Train/Send button
    "max_btn": (580, 250),               # Max quantity button
    "queue_slot_1": (300, 500),          # Queue slot 1
    "queue_slot_2": (360, 500),          # Queue slot 2
    "queue_slot_3": (420, 500),          # Queue slot 3
    "close_btn": (860, 120),             # Close building UI
}


TROOP_TYPES = ["t1", "t2", "t3", "t4", "t5"]


class TrainerBot:
    """
    Win32 macro-based troop training automation.
    Configurable queue priorities and troop type selection.
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
        self.cycle_wait = self._cfg["timing"].get("train_cycle_seconds", 120)
        self.ui = self._cfg.get("ui_coords", {}).get("barracks", DEFAULT_BARRACKS_UI)

        # Default troop priorities: order in which to train troops
        self.troop_queue = self._cfg.get("troop_training_queue", ["t4", "t3", "t2"])
        self.building_type = self._cfg.get("training_building", "barracks")  # barracks or stable

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

    def open_building(self, building: str = None) -> bool:
        """Open barracks or stable building UI."""
        building = building or self.building_type
        try:
            btn = self.ui.get(f"{building}_button", self.ui["barracks_button"])
            self._click(btn)
            time.sleep(2.0)
            self._click(self.ui["troop_tab"])
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Open building failed: {e}")
            return False

    def select_troop(self, troop_type: str) -> bool:
        """
        Select a troop type for training.
        troop_type: 't1' through 't5'
        """
        if troop_type not in TROOP_TYPES:
            print(f"[{datetime.now():%H:%M:%S}] [!] Invalid troop type: {troop_type}")
            return False

        try:
            btn = self.ui.get(f"{troop_type}_btn")
            if not btn:
                print(f"[{datetime.now():%H:%M:%S}] [!] No coords for {troop_type}")
                return False
            self._click(btn)
            time.sleep(1.0)
            print(f"[{datetime.now():%H:%M:%S}] [+] Selected {troop_type.upper()}")
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Select troop failed: {e}")
            return False

    def train_troops(self, troop_type: str, max_quantity: bool = True) -> bool:
        """
        Train the specified troop type.
        max_quantity: if True, click max button before training
        """
        try:
            if not self.select_troop(troop_type):
                return False

            if max_quantity:
                self._click(self.ui["max_btn"])
                time.sleep(0.8)

            self._click(self.ui["train_btn"])
            print(f"[{datetime.now():%H:%M:%S}] [+] Training {troop_type.upper()} — {'max' if max_quantity else '1'}")
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Train troops failed: {e}")
            return False

    def train_queue(self, queue: list[str] = None) -> int:
        """
        Train troops in priority order from the queue.
        Returns number of successfully started trains.
        """
        queue = queue or self.troop_queue
        count = 0

        for troop_type in queue:
            if self.train_troops(troop_type, max_quantity=True):
                count += 1
                time.sleep(2.0)  # Cooldown between queue items

        return count

    def close_building(self) -> bool:
        """Close the building UI."""
        try:
            self._click(self.ui["close_btn"])
            time.sleep(1.0)
            return True
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] [!] Close building failed: {e}")
            return False

    def run_cycle(self, queue: list[str] = None) -> int:
        """
        Run one training cycle through the troop queue.
        Returns number of trains started.
        """
        if not self.verify_ready():
            return 0

        print(f"[{datetime.now():%H:%M:%S}] [*] Training cycle started")
        queue = queue or self.troop_queue

        if not self.open_building():
            return 0

        count = self.train_queue(queue)
        self.close_building()
        print(f"[{datetime.now():%H:%M:%S}] [+] Training cycle complete — {count} trains started")
        return count

    def run_loop(self, queue: list[str] = None, interval: int = None) -> None:
        """Run training automation in a continuous loop."""
        interval = interval or self.cycle_wait
        self.active = True
        print(f"[{datetime.now():%H:%M:%S}] [*] Training loop started — interval {interval}s")

        while self.active:
            self.run_cycle(queue)
            for _ in range(interval):
                if not self.active:
                    break
                time.sleep(1)

        print(f"[{datetime.now():%H:%M:%S}] [*] Training loop stopped")

    def stop(self) -> None:
        """Stop the automation loop."""
        self.active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def start_loop(self, queue: list[str] = None, interval: int = None) -> None:
        """Start training loop in a background thread."""
        if self._thread and self._thread.is_alive():
            print(f"[{datetime.now():%H:%M:%S}] [!] Training loop already running")
            return
        self._thread = threading.Thread(
            target=self.run_loop,
            args=(queue, interval),
            daemon=True
        )
        self._thread.start()
