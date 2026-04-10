"""
modules/guild/bot.py — Guild Bot
Automatically claims guild gifts and donates to guild bank.
Phase 3 Anti-Detection: randomized timing throughout.
"""

import time
import json
from pathlib import Path
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard


# Default guild UI positions
DEFAULT_GUILD_POSITIONS = {
    "guild_button": (920, 620),
    "gifts_button": (350, 280),
    "claim_gift_btn": (540, 420),
    "bank_button": (550, 280),
    "donate_food": (200, 320),
    "donate_wood": (200, 360),
    "donate_stone": (200, 400),
    "donate_gold": (200, 440),
    "donate_btn": (700, 500),
    "close_button": (870, 155),
}


class GuildBot:
    """
    Win32 macro-based guild gift claiming and bank donations.
    Supports configurable donation limits per resource type.
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

        # Load donation limits
        guild_cfg = self._cfg.get("guild", {})
        self.donation_limits = guild_cfg.get("donation_limits", {
            "food": 10000,
            "wood": 10000,
            "stone": 10000,
            "gold": 5000,
        })
        self.auto_claim_gifts = guild_cfg.get("auto_claim_gifts", True)
        self.auto_donate = guild_cfg.get("auto_donate", True)

        # Load positions
        pos_cfg = guild_cfg.get("positions", DEFAULT_GUILD_POSITIONS)
        self.guild_btn = tuple(pos_cfg.get("guild_button", DEFAULT_GUILD_POSITIONS["guild_button"]))
        self.gifts_btn = tuple(pos_cfg.get("gifts_button", DEFAULT_GUILD_POSITIONS["gifts_button"]))
        self.claim_gift_btn = tuple(pos_cfg.get("claim_gift_btn", DEFAULT_GUILD_POSITIONS["claim_gift_btn"]))
        self.bank_btn = tuple(pos_cfg.get("bank_button", DEFAULT_GUILD_POSITIONS["bank_button"]))
        self.donate_food = tuple(pos_cfg.get("donate_food", DEFAULT_GUILD_POSITIONS["donate_food"]))
        self.donate_wood = tuple(pos_cfg.get("donate_wood", DEFAULT_GUILD_POSITIONS["donate_wood"]))
        self.donate_stone = tuple(pos_cfg.get("donate_stone", DEFAULT_GUILD_POSITIONS["donate_stone"]))
        self.donate_gold = tuple(pos_cfg.get("donate_gold", DEFAULT_GUILD_POSITIONS["donate_gold"]))
        self.donate_btn = tuple(pos_cfg.get("donate_btn", DEFAULT_GUILD_POSITIONS["donate_btn"]))
        self.close_btn = tuple(pos_cfg.get("close_button", DEFAULT_GUILD_POSITIONS["close_button"]))

    def verify_ready(self) -> bool:
        """Check that game is running and accessible."""
        if not self.radar.clients:
            print("[!] GuildBot: Game not detected. Is Lords Mobile running?")
            return False
        if not self.hands.hwnd:
            print("[!] GuildBot: Game window not found.")
            return False
        return True

    def _click(self, x: int, y: int, delay_ms: float = None) -> None:
        """Click with anti-detection humanization."""
        delay = delay_ms or self.anti_detection.random_action_delay()
        self.hands.vClick(x, y, delay_ms=delay)

    def claim_gifts(self) -> bool:
        """
        Navigate to guild gifts and claim available rewards.
        Returns True if gifts were successfully claimed.
        """
        try:
            if not self.session_guard.should_act("guild_gift"):
                print("[*] GuildBot: Rate limit reached for gift claiming, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            # 1. Open guild menu
            self._click(*self.guild_btn)
            delay = self.anti_detection.human_delay(min_ms=1500, max_ms=3000)
            time.sleep(delay / 1000)

            # 2. Click gifts tab
            self._click(*self.gifts_btn)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 3. Claim available gifts (click the claim button)
            self._click(*self.claim_gift_btn)
            delay = self.anti_detection.human_delay(min_ms=600, max_ms=1200)
            time.sleep(delay / 1000)

            # 4. May need to claim multiple gifts — click claim button again
            self._click(*self.claim_gift_btn)
            delay = self.anti_detection.human_delay(min_ms=600, max_ms=1200)
            time.sleep(delay / 1000)

            # 5. Close guild UI
            self._click(*self.close_btn)
            delay = self.anti_detection.human_delay(min_ms=400, max_ms=800)
            time.sleep(delay / 1000)

            self.session_guard.record_action("guild_gift")
            print("[+] GuildBot: Guild gifts claimed successfully")
            return True

        except Exception as e:
            print(f"[!] Guild gift claim failed: {e}")
            return False

    def donate_to_bank(self, resource: str, amount: int) -> bool:
        """
        Donate a specific resource amount to guild bank.
        Returns True if donation was successful.
        """
        try:
            if not self.session_guard.should_act("guild_donate"):
                print("[*] GuildBot: Rate limit reached for donations, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            # Map resource names to button positions
            resource_buttons = {
                "food": self.donate_food,
                "wood": self.donate_wood,
                "stone": self.donate_stone,
                "gold": self.donate_gold,
            }

            if resource not in resource_buttons:
                print(f"[!] GuildBot: Unknown resource '{resource}'")
                return False

            # 1. Open guild menu
            self._click(*self.guild_btn)
            delay = self.anti_detection.human_delay(min_ms=1500, max_ms=3000)
            time.sleep(delay / 1000)

            # 2. Click guild bank tab
            self._click(*self.bank_btn)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 3. Select resource
            self._click(*resource_buttons[resource])
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 4. Enter donation amount (simplified — assumes amount input field is focused)
            # In a real implementation, you'd type the number
            self._click(*resource_buttons[resource])  # Focus amount field
            delay = self.anti_detection.human_delay(min_ms=500, max_ms=1000)
            time.sleep(delay / 1000)

            # 5. Confirm donation
            self._click(*self.donate_btn)
            delay = self.anti_detection.human_delay(min_ms=600, max_ms=1200)
            time.sleep(delay / 1000)

            # 6. Close guild UI
            self._click(*self.close_btn)
            delay = self.anti_detection.human_delay(min_ms=400, max_ms=800)
            time.sleep(delay / 1000)

            self.session_guard.record_action("guild_donate")
            print(f"[+] GuildBot: Donated {amount:,} {resource} to guild bank")
            return True

        except Exception as e:
            print(f"[!] Guild donation failed: {e}")
            return False

    def run_cycle(self) -> None:
        """
        Run one guild automation cycle.
        Claims gifts and donates to bank based on configuration.
        """
        if not self.verify_ready():
            return

        if self.session_guard.enforced_cooldown():
            remaining = self.session_guard.cooldown_remaining
            print(f"[*] GuildBot: In cooldown, {remaining:.0f}s remaining")
            return

        # Claim guild gifts if enabled
        if self.auto_claim_gifts:
            print("[*] GuildBot: Claiming guild gifts...")
            self.claim_gifts()
            cycle_delay = self.anti_detection.random_cycle_delay()
            time.sleep(cycle_delay)

        # Donate to guild bank if enabled
        if self.auto_donate:
            print("[*] GuildBot: Donating to guild bank...")
            for resource, amount in self.donation_limits.items():
                if amount > 0:
                    self.donate_to_bank(resource, amount)
                    # Small delay between donations to avoid rapid-fire
                    inter_donate_delay = self.anti_detection.human_delay(min_ms=2000, max_ms=4000)
                    time.sleep(inter_donate_delay / 1000)

        print("[+] GuildBot: Cycle complete")
