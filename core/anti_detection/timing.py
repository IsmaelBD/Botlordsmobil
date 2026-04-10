"""
core/anti_detection/timing.py — Randomized Timing System
Human-like random delays to avoid pattern detection.
"""

import random
import time
import json
from pathlib import Path
from typing import Optional


class AntiDetection:
    """
    Generates human-like randomized timing for actions and cycles.
    All delays use random.uniform for proper float precision.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            cfg_path = Path(config_path)
        else:
            cfg_path = Path(__file__).parent.parent.parent / "config" / "settings.json"

        self._cfg = self._load_config(cfg_path)
        ad = self._cfg.get("anti_detection", {})

        self.min_action_delay_ms = ad.get("min_action_delay_ms", 50)
        self.max_action_delay_ms = ad.get("max_action_delay_ms", 500)
        self.min_cycle_delay = ad.get("min_cycle_delay", 180)
        self.max_cycle_delay = ad.get("max_cycle_delay", 600)
        self.min_jitter_ms = ad.get("min_jitter_ms", 10)
        self.max_jitter_ms = ad.get("max_jitter_ms", 50)

    def _load_config(self, cfg_path: Path) -> dict:
        with open(cfg_path) as f:
            return json.load(f)

    def random_action_delay(self) -> float:
        """
        Random ms delay between actions (human-like).
        Returns float in milliseconds.
        """
        return random.uniform(self.min_action_delay_ms, self.max_action_delay_ms)

    def random_cycle_delay(self) -> float:
        """
        Random seconds between automation cycles.
        Returns float in seconds.
        """
        return random.uniform(self.min_cycle_delay, self.max_cycle_delay)

    def jitter(self, base_ms: int, variance_pct: float = 0.2) -> float:
        """
        Add jitter to a base timing.
        variance_pct: fraction of base_ms to vary by (e.g. 0.2 = ±20%)
        Returns float in milliseconds.
        """
        variance = base_ms * variance_pct
        return random.uniform(base_ms - variance, base_ms + variance)

    def human_delay(self, min_ms: float = 100, max_ms: float = 400) -> float:
        """
        Generic human-like delay between min and max milliseconds.
        Use this for pauses that should feel unpredictable.
        """
        return random.uniform(min_ms, max_ms)
