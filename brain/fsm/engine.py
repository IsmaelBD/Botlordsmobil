"""
brain/fsm/engine.py — Finite State Machine Engine
Central decision loop that orchestrates all bot modules.
Phase 3 Anti-Detection: randomized polling and session guarding.
Phase 4 Analytics: state tracking, snapshots, and reporting.
"""

import time
import threading
import json
from enum import Enum
from pathlib import Path
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard
from utils.analytics import BotAnalytics


class BotState(Enum):
    IDLE = "idle"
    TUTORIAL = "tutorial"
    GATHERING = "gathering"
    ATTACKING = "attacking"
    EXPLORING = "exploring"
    WAITING = "waiting"
    ERROR = "error"


class FSMBotEngine:
    """
    Finite State Machine that:
    1. Reads game state from memory
    2. Decides the next state based on rules
    3. Executes the corresponding module
    4. Loops with anti-detection randomized timing
    5. Tracks all activity for analytics reporting
    """

    def __init__(self, account_name: str = "default"):
        self.state = BotState.IDLE
        self.radar = MemoryRadar()
        self.hands = Win32GhostClient()
        self.anti_detection = AntiDetection()
        self.session_guard = SessionGuard()
        self._load_config()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Phase 4: Analytics integration
        self.analytics = BotAnalytics(account_name)
        self._previous_state = None

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)
        self.polling_interval = self._cfg["timing"]["polling_interval"]
        self.features = self._cfg["features"]

    def start(self) -> None:
        """Start the FSM loop in a background thread."""
        if self._running:
            return

        if not self.radar.clients:
            print("[!] Game not detected. Start Lords Mobile first.")
            return

        if not self.hands.hwnd:
            print("[!] Game window not found.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[*] FSM Engine started — initial state: {self.state.value}")

        # Phase 4: Take initial state snapshot
        state = self._read_state()
        if state:
            self.analytics.snapshot_player_state(state)
            self.analytics.record_action("engine_start", state)

    def stop(self) -> None:
        """Stop the FSM loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

        # Phase 4: Take final state snapshot and generate session report
        state = self._read_state()
        if state:
            self.analytics.snapshot_player_state(state)
            self.analytics.record_action("engine_stop", state)

        self.analytics.save()
        print("[*] FSM Engine stopped")
        print("\n" + self.analytics.generate_session_report())

    def _loop(self) -> None:
        """Main FSM loop — randomized polling interval to avoid pattern detection."""
        while self._running:
            try:
                # Check cooldown before each iteration
                if self.session_guard.enforced_cooldown():
                    remaining = self.session_guard.cooldown_remaining
                    print(f"[*] FSM: In cooldown, {remaining:.0f}s remaining")
                    time.sleep(min(self.polling_interval, remaining))
                    continue

                state = self._read_state()
                new_state = self._decide_state(state)
                self._execute_state(new_state, state)
                self.state = new_state

            except Exception as e:
                print(f"[!] FSM loop error: {e}")
                self.state = BotState.ERROR

            # Randomized polling interval instead of fixed interval
            jitter = self.anti_detection.jitter(
                int(self.polling_interval * 1000),
                variance_pct=0.25
            )
            sleep_seconds = jitter / 1000
            time.sleep(sleep_seconds)

    def _read_state(self) -> Optional[dict]:
        """Read current player state from memory."""
        if not self.radar.clients:
            return None
        client = self.radar.clients[0]
        return self.radar.get_player_state(client["handle"], client["assembly_base"])

    def _decide_state(self, state: Optional[dict]) -> BotState:
        """Decision matrix — maps game state to bot action."""
        if not state:
            return BotState.IDLE

        tutorial = state.get("TutorialStep", 0)
        level = state.get("Level", 0)

        # Tutorial evasion has highest priority
        if 0 < tutorial < 999 and self.features.get("auto_evade_tutorial"):
            return BotState.TUTORIAL

        if self.features.get("auto_gather") and level >= 2:
            return BotState.GATHERING

        if self.features.get("auto_attack") and level >= 5:
            return BotState.ATTACKING

        if self.features.get("auto_explore"):
            return BotState.EXPLORING

        return BotState.IDLE

    def _execute_state(self, state: BotState, game_state: Optional[dict]) -> None:
        """Execute actions for the given state."""
        # Phase 4: Record state transition
        if self._previous_state != state:
            from_state = self._previous_state.value if self._previous_state else "start"
            self.analytics.record_state_transition(from_state, state.value)
            self._previous_state = state

        # Phase 4: Take periodic snapshots during active states
        if game_state:
            self.analytics.snapshot_player_state(game_state)

        if state == BotState.IDLE:
            print("[IDLE] No action needed")

        elif state == BotState.TUTORIAL:
            print(f"[TUTORIAL] Evading tutorial step {game_state.get('TutorialStep')}")
            # TODO: Implement tutorial evasion clicks
            self.hands.vClick(300, 400)

        elif state == BotState.GATHERING:
            print("[GATHERING] Resource gathering not yet dispatched")
            # Phase 4: When gatherer module is integrated:
            # self.analytics.record_resource_gather("food", gathered_amount)

        elif state == BotState.ATTACKING:
            print("[ATTACKING] Attack module not yet connected")
            # Phase 4: When attacker module is integrated:
            # self.analytics.record_attack(zone, point, result, ...)

        elif state == BotState.EXPLORING:
            print("[EXPLORING] Explorer module not yet connected")

        elif state == BotState.ERROR:
            print("[ERROR] Waiting for recovery...")

    # Phase 4: Analytics helper methods for modules
    def record_gather(self, resource: str, amount: int) -> None:
        """Record resource gathering (call from gatherer module)."""
        self.analytics.record_resource_gather(resource, amount)

    def record_attack(self, zone: int, point: int, result: str,
                      troops: int = 0, kills: int = 0, losses: int = 0) -> None:
        """Record attack result (call from attacker module)."""
        self.analytics.record_attack(zone, point, result, troops, kills, losses)

    def record_march(self, duration: float, troops: int, resources: dict = None) -> None:
        """Record march return (call from gatherer/attacker module)."""
        self.analytics.record_march_return(duration, troops, resources)

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "state": self.state.value,
            "game_detected": bool(self.radar.clients),
            "window_found": bool(self.hands.hwnd),
            "analytics": self.analytics.get_session_stats(),
        }
