"""
core/anti_detection/session_guard.py — Session Rotation & Cooldown
Prevents detection through behavioral pattern rate-limiting.
Uses a sliding window for accurate action tracking.
"""

import time
import random
import json
import collections
from pathlib import Path
from typing import Optional, Deque


class SessionGuard:
    """
    Rate limiter and session guard using sliding window tracking.
    Prevents the bot from looking too robotic by enforcing:
    - Max actions per minute (sliding window)
    - Max consecutive cycles before forced pause
    - Random cooldown breaks

    The sliding window tracks exact timestamps of each action,
    so rate limiting is accurate rather than a simple counter.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            cfg_path = Path(config_path)
        else:
            cfg_path = Path(__file__).parent.parent.parent / "config" / "settings.json"

        self._cfg = self._load_config(cfg_path)
        ad = self._cfg.get("anti_detection", {})

        self.max_actions_per_minute = ad.get("max_actions_per_minute", 10)
        self.max_consecutive_cycles = ad.get("max_consecutive_cycles", 5)
        self.cooldown_after_max = ad.get("cooldown_after_max", 300)
        self.min_pause_seconds = ad.get("min_pause_seconds", 30)
        self.max_pause_seconds = ad.get("max_pause_seconds", 120)

        # Sliding window: timestamps of recent actions per type
        # Using a deque per action type to track time-ordered actions
        self._action_log: dict[str, Deque[float]] = collections.defaultdict(
            lambda: collections.deque(maxlen=self.max_actions_per_minute * 2)
        )
        self._cycle_count = 0
        self._in_cooldown = False
        self._cooldown_start: Optional[float] = None

    def _load_config(self, cfg_path: Path) -> dict:
        with open(cfg_path) as f:
            return json.load(f)

    def should_act(self, action_type: str = "default") -> bool:
        """
        Check if an action is allowed based on rate limiting.
        Uses a 60-second sliding window — only actions within
        the last 60 seconds count toward the limit.
        """
        if self._in_cooldown:
            return False

        now = time.time()
        window_seconds = 60

        # Prune old entries outside the sliding window
        log = self._action_log[action_type]
        cutoff = now - window_seconds

        while log and log[0] < cutoff:
            log.popleft()

        # Check if we're at the limit
        if len(log) >= self.max_actions_per_minute:
            return False

        return True

    def record_action(self, action_type: str = "default") -> None:
        """
        Log an action with its timestamp for rate limiting.
        """
        now = time.time()
        self._action_log[action_type].append(now)
        self._cycle_count += 1

        # If we've hit max consecutive cycles, trigger cooldown
        if self._cycle_count >= self.max_consecutive_cycles:
            self._start_cooldown()

    def enforced_cooldown(self) -> bool:
        """
        Returns True if the bot should remain in cooldown.
        Checks if the cooldown period has elapsed.
        """
        if not self._in_cooldown:
            return False

        elapsed = time.time() - (self._cooldown_start or 0)
        if elapsed >= self.cooldown_after_max:
            self._in_cooldown = False
            self._cooldown_start = None
            self._cycle_count = 0
            return False

        return True

    def _start_cooldown(self) -> None:
        """Enter cooldown mode after max cycles reached."""
        self._in_cooldown = True
        self._cooldown_start = time.time()
        remaining = self.cooldown_after_max - (time.time() - self._cooldown_start)
        print(f"[*] SessionGuard: Max cycles ({self.max_consecutive_cycles}) reached. "
              f"Cooldown for {self.cooldown_after_max}s...")

    def random_pause(self) -> float:
        """
        Take a random human-like break to reset behavior pattern.
        Returns the actual pause duration in seconds.
        """
        duration = random.uniform(self.min_pause_seconds, self.max_pause_seconds)
        print(f"[*] SessionGuard: Random pause for {duration:.1f}s")
        time.sleep(duration)
        self._cycle_count = 0
        return duration

    def reset(self) -> None:
        """Reset all counters and logs."""
        self._action_log.clear()
        self._cycle_count = 0
        self._in_cooldown = False
        self._cooldown_start = None

    @property
    def cooldown_remaining(self) -> float:
        """Seconds remaining in current cooldown."""
        if not self._in_cooldown or self._cooldown_start is None:
            return 0
        return max(0, self.cooldown_after_max - (time.time() - self._cooldown_start))
