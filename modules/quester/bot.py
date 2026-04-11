"""
modules/quester/bot.py — Daily Quest Bot
Automatically completes daily quests by priority.
Phase 3 Anti-Detection: randomized timing throughout.
"""

import time
import json
from pathlib import Path
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard


# Quest priorities: higher number = higher priority
DEFAULT_QUEST_PRIORITIES = {
    "gather_1000_food": 10,
    "gather_1000_wood": 10,
    "attack_monster": 8,
    "use_speed_up": 7,
    "donate_to_guild": 6,
    "complete_1_rally": 5,
    "send_march": 3,
    "login_daily": 9,  # Usually auto-completed
}


# Default quest UI positions
DEFAULT_QUEST_POSITIONS = {
    "quest_button": (950, 620),
    "daily_tab": (200, 200),
    "achievement_tab": (350, 200),
    "quest_item_base": (300, 280),  # Base position, offset by index
    "claim_btn_offset": (400, 0),
    "go_btn": (700, 450),
    "close_button": (870, 155),
}


class QuesterBot:
    """
    Win32 macro-based daily quest automation.
    Completes quests in priority order with configurable settings.
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
        self.quest_priorities = self._cfg.get("quester", {}).get("quest_priorities", DEFAULT_QUEST_PRIORITIES)
        self.max_quests_per_cycle = self._cfg.get("quester", {}).get("max_quests_per_cycle", 5)

        # Load positions
        pos_cfg = self._cfg.get("quester", {}).get("positions", DEFAULT_QUEST_POSITIONS)
        self.quest_btn = tuple(pos_cfg.get("quest_button", DEFAULT_QUEST_POSITIONS["quest_button"]))
        self.daily_tab = tuple(pos_cfg.get("daily_tab", DEFAULT_QUEST_POSITIONS["daily_tab"]))
        self.achievement_tab = tuple(pos_cfg.get("achievement_tab", DEFAULT_QUEST_POSITIONS["achievement_tab"]))
        self.quest_item_base = tuple(pos_cfg.get("quest_item_base", DEFAULT_QUEST_POSITIONS["quest_item_base"]))
        self.go_btn = tuple(pos_cfg.get("go_btn", DEFAULT_QUEST_POSITIONS["go_btn"]))
        self.close_btn = tuple(pos_cfg.get("close_button", DEFAULT_QUEST_POSITIONS["close_button"]))

    def verify_ready(self) -> bool:
        """Check that game is running and accessible."""
        if not self.radar.clients:
            print("[!] QuesterBot: Game not detected. Is Lords Mobile running?")
            return False
        if not self.hands.hwnd:
            print("[!] QuesterBot: Game window not found.")
            return False
        return True

    def _click(self, x: int, y: int, delay_ms: float = None) -> None:
        """Click with anti-detection humanization."""
        delay = delay_ms or self.anti_detection.random_action_delay()
        self.hands.vClick(x, y, delay_ms=delay)

    def _get_quest_position(self, index: int) -> tuple[int, int]:
        """Get the position of a quest item by index."""
        base_x, base_y = self.quest_item_base
        return (base_x + index * 60, base_y)

    def complete_quest(self, quest_id: str) -> bool:
        """
        Attempt to complete a specific quest by ID.
        Navigates to quest, performs required action, claims reward.
        Returns True if quest was completed.
        """
        try:
            if not self.session_guard.should_act("quest"):
                print("[*] QuesterBot: Rate limit reached, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            # 1. Open quest panel
            self._click(*self.quest_btn)
            delay = self.anti_detection.human_delay(min_ms=1500, max_ms=3000)
            time.sleep(delay / 1000)

            # 2. Click daily tab
            self._click(*self.daily_tab)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 3. Find and click on the quest by priority
            quest_index = self._get_quest_index(quest_id)
            quest_pos = self._get_quest_position(quest_index)

            # Click on quest item
            self._click(*quest_pos)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 4. Click "Go" button to travel/complete
            self._click(*self.go_btn)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 5. Claim quest reward
            self._click(*quest_pos)  # Re-click to claim
            delay = self.anti_detection.human_delay(min_ms=600, max_ms=1200)
            time.sleep(delay / 1000)

            # 6. Close quest panel
            self._click(*self.close_btn)
            delay = self.anti_detection.human_delay(min_ms=400, max_ms=800)
            time.sleep(delay / 1000)

            self.session_guard.record_action("quest")
            print(f"[+] QuesterBot: Completed quest '{quest_id}'")
            return True

        except Exception as e:
            print(f"[!] Quest completion failed for '{quest_id}': {e}")
            return False

    def _get_quest_index(self, quest_id: str) -> int:
        """Map quest_id to UI index based on priorities."""
        # Sort quests by priority and find index
        sorted_quests = sorted(
            self.quest_priorities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for index, (qid, _) in enumerate(sorted_quests):
            if qid == quest_id:
                return index
        return 0

    def get_sorted_quests(self) -> list[tuple[str, int]]:
        """Return quests sorted by priority (highest first)."""
        return sorted(
            self.quest_priorities.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def run_cycle(self) -> None:
        """
        Run one quest completion cycle.
        Completes quests in priority order up to max_quests_per_cycle.
        """
        if not self.verify_ready():
            return

        if self.session_guard.enforced_cooldown():
            remaining = self.session_guard.cooldown_remaining
            print(f"[*] QuesterBot: In cooldown, {remaining:.0f}s remaining")
            return

        sorted_quests = self.get_sorted_quests()
        completed = 0

        print(f"[*] QuesterBot: Starting quest cycle ({len(sorted_quests)} quests available)")

        for quest_id, priority in sorted_quests:
            if completed >= self.max_quests_per_cycle:
                print(f"[*] QuesterBot: Reached max quests per cycle ({self.max_quests_per_cycle})")
                break

            print(f"[*] QuesterBot: Processing quest '{quest_id}' (priority={priority})")
            success = self.complete_quest(quest_id)

            if success:
                completed += 1

            # Delay between quests
            if completed < len(sorted_quests):
                cycle_delay = self.anti_detection.random_cycle_delay()
                print(f"[*] Waiting {cycle_delay:.1f}s before next quest...")
                time.sleep(cycle_delay)

        print(f"[+] QuesterBot: Cycle complete — {completed} quests completed")
