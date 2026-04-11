"""
modules/monster/bot.py — Monster Hunting Bot
Automatically sends marches to attack monsters on the map.
Phase 3 Anti-Detection: randomized timing throughout.
"""

import time
import json
from pathlib import Path
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard


# Known monster spawn points by zone
# Format: zone_id -> list of (point_id, monster_level) tuples
DEFAULT_MONSTER_SPAWNS = {
    101: [(12, 1), (25, 2), (38, 3), (51, 4)],
    102: [(7, 1), (19, 2), (33, 3), (47, 4), (61, 5)],
    103: [(14, 2), (28, 3), (42, 4), (56, 5)],
    104: [(9, 3), (22, 4), (35, 5), (48, 6)],
    105: [(3, 4), (17, 5), (31, 6), (45, 7)],
}


class MonsterBot:
    """
    Win32 macro-based monster hunting with march injection.
    Navigates to monster spawn points and dispatches attack marches.
    Phase 3 Anti-Detection: session guarding and randomized timing.
    """

    def __init__(self):
        self.radar = MemoryRadar()
        self.hands = Win32GhostClient()
        self.anti_detection = AntiDetection()
        self.session_guard = SessionGuard()
        self._load_config()
        self._load_spawns()
        self.active = False

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

        self.resolution = self._cfg["game"]["resolution"]
        self.click_delay = self._cfg["timing"]["click_delay_ms"] / 1000
        self.march_wait = self._cfg["timing"]["march_wait_seconds"]
        self.monster_level = self._cfg.get("monster", {}).get("target_level", 5)
        self.zones = self._cfg.get("monster", {}).get("zones", list(DEFAULT_MONSTER_SPAWNS.keys()))

    def _load_spawns(self) -> None:
        """Load monster spawn points from config or use defaults."""
        cfg_path = Path(__file__).parent.parent.parent / "config" / "monsters.json"
        if cfg_path.exists():
            with open(cfg_path) as f:
                self.spawns = json.load(f)
        else:
            self.spawns = DEFAULT_MONSTER_SPAWNS

    def verify_ready(self) -> bool:
        """Check that game is running and accessible."""
        if not self.radar.clients:
            print("[!] MonsterBot: Game not detected. Is Lords Mobile running?")
            return False
        if not self.hands.hwnd:
            print("[!] MonsterBot: Game window not found.")
            return False
        return True

    def _click(self, x: int, y: int, delay_ms: float = None) -> None:
        """Click with anti-detection humanization."""
        delay = delay_ms or self.anti_detection.random_action_delay()
        self.hands.vClick(x, y, delay_ms=delay)

    def find_nearest_monster(self) -> tuple[int, int, int]:
        """
        Scan known spawn points and return (zone_id, point_id, monster_level)
        of the nearest available monster.
        """
        for zone_id in sorted(self.zones):
            if zone_id not in self.spawns:
                continue
            for point_id, level in self.spawns[zone_id]:
                if level <= self.monster_level:
                    return zone_id, point_id, level
        return 0, 0, 0

    def hunt(self, zone_id: int, point_id: int, monster_level: int = 1) -> bool:
        """
        Click sequence to send a march to attack a monster.
        Returns True if march was dispatched successfully.
        """
        try:
            if not self.session_guard.should_act("monster"):
                print("[*] MonsterBot: Rate limit reached, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            # 1. Open global map
            self._click(80, 622)
            delay = self.anti_detection.human_delay(min_ms=1500, max_ms=3000)
            time.sleep(delay / 1000)

            # 2. Navigate to zone
            self._click(640, 360)  # Zone input area
            delay = self.anti_detection.human_delay(min_ms=500, max_ms=1000)
            time.sleep(delay / 1000)

            # 3. Enter zone coordinates
            # Use fast click for numeric input
            self.hands.vClickFast(640, 360)
            delay = self.anti_detection.human_delay(min_ms=200, max_ms=500)
            time.sleep(delay / 1000)

            # 4. Click the monster point on map
            self._click(400 + (point_id % 10) * 40, 300 + (point_id // 10) * 40)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 5. Click attack/march button
            self._click(528, 348)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 6. Select troops (use max)
            self._click(583, 252)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 7. Deploy march
            self._click(787, 460)

            self.session_guard.record_action("monster")
            print(f"[+] MonsterBot: March dispatched to zone={zone_id}, point={point_id}, level={monster_level}")
            return True

        except Exception as e:
            print(f"[!] Monster hunt failed: {e}")
            return False

    def run_cycle(self) -> None:
        """
        Run one monster hunting cycle.
        Finds the nearest suitable monster and attacks it.
        """
        if not self.verify_ready():
            return

        if self.session_guard.enforced_cooldown():
            remaining = self.session_guard.cooldown_remaining
            print(f"[*] MonsterBot: In cooldown, {remaining:.0f}s remaining")
            return

        zone_id, point_id, level = self.find_nearest_monster()
        if zone_id == 0:
            print("[*] MonsterBot: No suitable monsters found in configured zones/levels")
            return

        print(f"[*] MonsterBot: Hunting monster — zone={zone_id}, point={point_id}, level={level}")
        success = self.hunt(zone_id, point_id, level)

        if success:
            cycle_delay = self.anti_detection.random_cycle_delay()
            print(f"[*] Waiting {cycle_delay:.1f}s before next hunt...")
            time.sleep(cycle_delay)

        print("[+] MonsterBot: Cycle complete")
