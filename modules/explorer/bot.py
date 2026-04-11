"""
modules/explorer/bot.py — Map Explorer
Scans the game map to discover resource nodes, castles, and players.
Phase 3 Anti-Detection: randomized timing and human-like clicks.
"""

import json
import time
from pathlib import Path

from core.win32.hands import Win32GhostClient
from core.memory.radar import MemoryRadar
from core.anti_detection import AntiDetection, SessionGuard


class ExplorerBot:
    """Win32 macro + memory scanning based map exploration with anti-detection."""

    def __init__(self):
        self.hands = Win32GhostClient()
        self.radar = MemoryRadar()
        self.anti_detection = AntiDetection()
        self.session_guard = SessionGuard()
        self._load_config()

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

    def scan_area(self, center_x: int, center_y: int, radius: int = 5) -> list[dict]:
        """
        Scan an area of the map by moving the camera and reading coordinates.
        Returns a list of discovered points with their types.
        """
        discovered = []

        # Move camera to center
        self.hands.vClick(center_x, center_y)
        time.sleep(self.anti_detection.human_delay(800, 1500) / 1000)

        offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1), (1, 0), (1, 1),
        ]

        for dx, dy in offsets:
            # Rate limit check before each action
            if not self.session_guard.should_act("explore"):
                print("[*] ExplorerBot: Rate limit, pausing...")
                self.session_guard.random_pause()

            cx = center_x + dx * radius
            cy = center_y + dy * radius
            # Click to center map on this coordinate
            self.hands.vClick(cx, cy)
            time.sleep(self.anti_detection.human_delay(400, 900) / 1000)

            # Record action
            self.session_guard.record_action("explore")

            # Read potential target from memory
            # TODO: Hook into game's map rendering to get actual points
            discovered.append({"x": cx, "y": cy, "dx": dx, "dy": dy})

        return discovered

    def run_exploration(self, start_x: int, start_y: int, grid_size: int = 3) -> list[dict]:
        """
        Run a grid exploration starting from (start_x, start_y).
        """
        results = []
        step = 200  # Pixels between waypoints

        for row in range(grid_size):
            for col in range(grid_size):
                x = start_x + col * step
                y = start_y + row * step
                print(f"[*] Exploring cell ({col}, {row}) at ({x}, {y})")
                points = self.scan_area(x, y)
                results.extend(points)
                # Randomized inter-cell delay
                time.sleep(self.anti_detection.random_cycle_delay())

        print(f"[+] Exploration complete. {len(results)} points scanned")
        return results
