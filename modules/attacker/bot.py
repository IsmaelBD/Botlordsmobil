"""
modules/attacker/bot.py — Attacker Bot
Sends troop marches to attack targets on the map.
Uses the v13.9.1 synchronized march injection method.
"""

import ctypes
import struct
import time
import json
from pathlib import Path
from typing import Optional

from core.memory.radar import MemoryRadar


# Default march template from game_analysis.md (101 bytes content, no header)
MARCH_TEMPLATE_CONTENT = bytes.fromhex(
    "09000000000000002c0100000000000000000000000000006400000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000"
)


class MarchInjector:
    """
    Injects troop marches via shellcode into the game process.
    Based on the v13.9.1 Frida injector with synchronized sequence IDs.
    """

    def __init__(self, radar: MemoryRadar, client_info: dict):
        self.radar = radar
        self.client = client_info
        self.handle = client_info["handle"]
        self.base = client_info["assembly_base"]
        self._load_rvas()

    def _load_rvas(self) -> None:
        cfg_path = Path(__file__).parent.parent.parent / "config" / "offsets.json"
        with open(cfg_path) as f:
            cfg = json.load(f)
        rvass = cfg["rvass"]
        self.fn_get_mp = self.base + int(rvass["GET_MP"], 16)
        self.fn_add_seq = self.base + int(rvass["ADD_SEQ"], 16)
        self.fn_add_us = self.base + int(rvass["ADD_US"], 16)
        self.fn_net_send = self.base + int(rvass["NET_SEND"], 16)

    def _alloc_remote(self, size: int) -> int:
        """Allocate memory in the game process."""
        addr = ctypes.windll.kernel32.VirtualAllocEx(
            self.handle, 0, size, 0x3000, 0x40
        )
        if not addr:
            raise RuntimeError("VirtualAllocEx failed")
        return addr

    def _write_remote(self, addr: int, data: bytes) -> None:
        """Write data to the game process."""
        written = ctypes.c_size_t(0)
        ctypes.windll.kernel32.WriteProcessMemory(
            self.handle, ctypes.c_void_p(addr),
            bytes(data), len(data), ctypes.byref(written)
        )

    def _run_shellcode(self, addr: int) -> None:
        """Execute shellcode in the game process via remote thread."""
        ctypes.windll.kernel32.CreateRemoteThread(
            self.handle, None, 0, ctypes.c_void_p(addr), None, 0, None
        )

    def build_inject_shellcode(self, content_addr: int, content_size: int) -> bytes:
        """Build the complete injection shellcode (x64)."""
        shellcode = bytearray()

        # === Prologue ===
        shellcode.extend(b"\x55\x48\x89\xE5\x48\x83\xEC\x40")

        # === Step 1: Get MessagePacket pointer ===
        shellcode.extend(b"\x48\xB8")
        shellcode.extend(struct.pack("<Q", self.fn_get_mp))
        shellcode.extend(b"\xFF\xD0\x48\x89\x45\xF8")  # mov [rbp-8], rax

        # === Step 2: Navigate to data buffer ===
        shellcode.extend(b"\x48\x8B\x45\xF8")           # mov rax, [rbp-8]
        shellcode.extend(b"\x48\x8B\x40\x28")           # mov rax, [rax+0x28] (buffer object)
        shellcode.extend(b"\x48\x8B\x40\x20")           # mov rax, [rax+0x20] (data object)
        shellcode.extend(b"\x48\x89\x45\xF0")           # mov [rbp-0x10], rax (save)

        # === Step 3: Get current position ===
        shellcode.extend(b"\x48\x8B\x45\xF8")           # mov rax, [rbp-8]
        shellcode.extend(b"\x8B\x40\x18")               # mov eax, [rax+0x18] (currentPos)
        shellcode.extend(b"\x89\x45\xEC")               # mov [rbp-0x14], eax (save pos)

        # === Step 4: Calculate raw start (dataObject + 0x20 + currentPos) ===
        shellcode.extend(b"\x48\x8B\x45\xF0")           # mov rax, [rbp-0x10]
        shellcode.extend(b"\x48\x05\x20\x02\x00\x00")   # add rax, 0x220 (rawStart offset)
        shellcode.extend(b"\x8B\x55\xEC")               # mov edx, [rbp-0x14]
        shellcode.extend(b"\x48\x01\xD0")               # add rax, rdx (rawStart + pos)
        shellcode.extend(b"\x48\x89\x45\xE8")           # mov [rbp-0x18], rax (dest ptr)

        # === Step 5: Copy content via rep movsb ===
        shellcode.extend(b"\x48\x8B\x4D\xE8")           # mov rcx, [rbp-0x18] (dest)
        shellcode.extend(b"\x48\xBE")                   # mov rsi, content_addr
        shellcode.extend(struct.pack("<Q", content_addr))
        shellcode.extend(b"\xB9")                       # mov rcx, count
        shellcode.extend(struct.pack("<I", content_size))
        shellcode.extend(b"\xF3\xA4")                   # rep movsb

        # === Step 6: Update length (currentPos + contentSize) ===
        shellcode.extend(b"\x48\x8B\x45\xF8")           # mov rax, [rbp-8]
        shellcode.extend(b"\x8B\x55\xEC")               # mov edx, [rbp-0x14]
        shellcode.extend(b"\x48\x8B\x08")               # mov rcx, [rax]
        shellcode.extend(b"\x03\x55\xEC")               # add edx, [rbp-0x14] (pos + pos = 2*pos... wait)
        # Actually: currentPos + contentSize
        shellcode.extend(b"\x8B\x45\xEC")               # mov eax, [rbp-0x14]
        shellcode.extend(struct.pack("<I", content_size & 0xFFFFFFFF))  # add eax, contentSize
        shellcode.extend(b"\x05" + struct.pack("<I", content_size))
        shellcode.extend(b"\x89\x40\x18")               # mov [rax+0x18], eax

        # === Step 7: Set protocol to 6615 ===
        shellcode.extend(b"\x48\x8B\x45\xF8")           # mov rax, [rbp-8]
        shellcode.extend(b"\x66\xC7\x40\x30\xD7\x19")  # mov [rax+0x30], 6615

        # === Step 8: AddSeq + AddUS + Send ===
        # AddSeq
        shellcode.extend(b"\x48\x8B\x4D\xF8\x48\xB8")
        shellcode.extend(struct.pack("<Q", self.fn_add_seq))
        shellcode.extend(b"\xFF\xD0")

        # AddUS (prefix = 1)
        shellcode.extend(b"\x48\x8B\x4D\xF8\x66\xB8\x01\x00\x48\xB8")
        shellcode.extend(struct.pack("<Q", self.fn_add_us))
        shellcode.extend(b"\xFF\xD0")

        # Send
        shellcode.extend(b"\x48\x8B\x4D\xF8\xBA\x00\x00\x00\x00\x48\xB8")
        shellcode.extend(struct.pack("<Q", self.fn_net_send))
        shellcode.extend(b"\xFF\xD0")

        # === Epilogue ===
        shellcode.extend(b"\x48\x83\xC4\x40\x5D\xC3")

        return bytes(shellcode)

    def inject(self, zone_id: int, point_id: int, troop_config: bytes = None) -> bool:
        """Inject a synchronized march into the game.

        Args:
            zone_id: Zone ID (e.g., 507)
            point_id: Point ID within the zone (e.g., 59)
            troop_config: Optional custom troop configuration (101 bytes).
                         Defaults to MARCH_TEMPLATE_CONTENT.
        """
        content = troop_config or MARCH_TEMPLATE_CONTENT

        # Encode coordinates into the content at offsets 72 and 74
        march_data = bytearray(content)
        struct.pack_into("<H", march_data, 72, zone_id)
        struct.pack_into("<B", march_data, 74, point_id)

        try:
            # Allocate memory for content in game process
            content_addr = self._alloc_remote(len(march_data))
            self._write_remote(content_addr, bytes(march_data))

            # Build and allocate shellcode
            shellcode = self.build_inject_shellcode(content_addr, len(march_data))
            shellcode_addr = self._alloc_remote(len(shellcode))
            self._write_remote(shellcode_addr, shellcode)

            # Execute
            self._run_shellcode(shellcode_addr)
            print(f"[🚀] March injected → zone={zone_id}, point={point_id}")
            return True

        except Exception as e:
            print(f"[!] March injection failed: {e}")
            return False


class AttackerBot:
    """
    High-level attack bot using the MarchInjector.
    Supports single-target attacks, battle loops, and rally coordination.
    """

    def __init__(self):
        self.radar = MemoryRadar()
        if not self.radar.clients:
            raise RuntimeError("Game not detected. Is Lords Mobile running?")
        self.client = self.radar.clients[0]
        self.injector = MarchInjector(self.radar, self.client)
        self._load_config()
        self._load_targets()

    def _load_config(self) -> None:
        cfg_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg_path) as f:
            self._cfg = json.load(f)
        self.resolution = self._cfg["game"]["resolution"]
        self.cooldown = self._cfg["timing"]["march_wait_seconds"]

    def _load_targets(self) -> None:
        """Load target list from config or default."""
        cfg_path = Path(__file__).parent.parent.parent / "config" / "targets.json"
        if cfg_path.exists():
            with open(cfg_path) as f:
                self.targets = json.load(f)
        else:
            self.targets = []

    def attack(self, zone_id: int, point_id: int, wait: int = None) -> bool:
        """Send a single attack march."""
        w = wait or self.cooldown
        print(f"[*] Attacking zone={zone_id}, point={point_id}")
        success = self.injector.inject(zone_id, point_id)
        if success:
            print(f"[*] Waiting {w}s before next action...")
            time.sleep(w)
        return success

    def attack_rally(self, target: dict) -> bool:
        """Attack with rally parameters."""
        zone = target.get("zone", 507)
        point = target.get("point", 59)
        rally = target.get("rally", False)
        troops = target.get("troops", None)  # Optional custom troop config

        print(f"[*] Rally attack: zone={zone}, point={point}, rally={rally}")
        return self.injector.inject(zone, point, troops)

    def run_battle_loop(self, targets: list[dict] = None, loop: bool = False) -> None:
        """
        Run attack loop through targets list.

        Args:
            targets: List of {zone, point, wait, rally, troops}
            loop: If True, repeat indefinitely
        """
        if targets is None:
            targets = self.targets

        if not targets:
            print("[!] No targets configured. Add targets to config/targets.json")
            return

        print(f"[*] Battle loop starting — {len(targets)} targets, loop={loop}")

        iteration = 0
        while True:
            iteration += 1
            print(f"\n=== Iteration {iteration} ===")
            for i, t in enumerate(targets):
                zone = t.get("zone", 507)
                point = t.get("point", 59)
                wait = t.get("wait", self.cooldown)

                print(f"[*] [{i+1}/{len(targets)}] zone={zone}, point={point}")
                self.injector.inject(zone, point, t.get("troops"))

                if i < len(targets) - 1:
                    print(f"[*] Cooldown {wait}s...")
                    time.sleep(wait)

            if not loop:
                break
            print(f"[+] Cycle complete. Restarting in {self.cooldown}s...")
            time.sleep(self.cooldown)


# Quick test
if __name__ == "__main__":
    bot = AttackerBot()
    # Default: attack the forest (zone 507, point 59)
    bot.attack(507, 59)
