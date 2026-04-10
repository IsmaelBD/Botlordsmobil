"""
modules/attacker/bot.py — Attack Bot
Sends troop marches to attack other players' castles.
"""

import time
import json
from pathlib import Path

from core.memory.radar import MemoryRadar
from core.network.sniffer import PacketInjector


class AttackerBot:
    """Memory + packet injection based combat system."""

    def __init__(self):
        self.radar = MemoryRadar()
        if self.radar.clients:
            self.injector = PacketInjector(self.radar, self.radar.clients[0])
        else:
            self.injector = None
        self._load_config()

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

    def attack_target(self, zone_id: int, point_id: int) -> bool:
        """Send an attack march to coordinates (zone_id, point_id)."""
        if not self.injector:
            print("[!] Game not detected")
            return False

        template_path = Path(__file__).parent.parent.parent / "master_march.bin"
        if not template_path.exists():
            print("[!] master_march.bin not found")
            return False

        with open(template_path, "rb") as f:
            template = f.read()

        try:
            self.injector.inject_march(zone_id, point_id, template)
            print(f"[+] Attack march dispatched to zone={zone_id}, point={point_id}")
            return True
        except Exception as e:
            print(f"[!] Attack failed: {e}")
            return False

    def run_battle_loop(self, targets: list[dict]) -> None:
        """Run combat loop through a list of targets."""
        for i, target in enumerate(targets):
            zone = target.get("zone", 507)
            point = target.get("point", 59)
            wait = target.get("wait", 300)
            print(f"[*] Battle {i+1}/{len(targets)}: zone={zone}, point={point}")
            self.attack_target(zone, point)
            if i < len(targets) - 1:
                print(f"[*] Waiting {wait}s...")
                time.sleep(wait)
