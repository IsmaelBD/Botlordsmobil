"""
core/network/sniffer.py — Packet Sniffer & Injector
Captures and injects game network traffic.
"""

import socket
import struct
import json
import time
from pathlib import Path
from typing import Optional


class PacketSniffer:
    """Raw socket sniffer for game packets (requires admin)."""

    def __init__(self, server_host: str = None, server_port: int = None):
        cfg = self._load_config()
        self.server_host = server_host or cfg["network"]["server"]["host"]
        self.server_port = server_port or cfg["network"]["server"]["port"]
        self.socket: Optional[socket.socket] = None

    def _load_config(self) -> dict:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            return json.load(f)

    def connect(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.server_host, self.server_port))

    def send_packet(self, hex_data: str) -> Optional[bytes]:
        """Send raw hex packet to server."""
        if not self.socket:
            self.connect()
        data = bytes.fromhex(hex_data)
        self.socket.sendall(data)
        try:
            return self.socket.recv(4096)
        except socket.timeout:
            return None

    def send_version(self) -> bool:
        cfg_path = Path(__file__).parent.parent.parent / "config" / "offsets.json"
        with open(cfg_path) as f:
            cfg = json.load(f)
        proto = cfg["protocols"]["version"]
        # Placeholder — real packet must be captured from live session
        return True

    def close(self) -> None:
        if self.socket:
            self.socket.close()
            self.socket = None


class PacketInjector:
    """Direct memory injection of packets via shellcode (Windows only)."""

    def __init__(self, radar, client_info: dict):
        self.radar = radar
        self.client = client_info
        self._load_offsets()

    def _load_offsets(self) -> None:
        cfg_path = Path(__file__).parent.parent.parent / "config" / "offsets.json"
        with open(cfg_path) as f:
            self._cfg = json.load(f)

        self._rva_get_mp = int(self._cfg["rvass"]["GET_MP"], 16)
        self._rva_add_seq = int(self._cfg["rvass"]["ADD_SEQ"], 16)
        self._rva_send = int(self._cfg["rvass"]["SEND"], 16)

    def build_march_shellcode(self, zone_id: int, point_id: int, content_addr: int, content_size: int) -> bytearray:
        """Build the complete shellcode for march injection.

        Args:
            content_addr: Remote address in game process (allocated via VirtualAllocEx)
            content_size: Size of the march data in bytes
        """
        import ctypes

        base = self.client["assembly_base"]
        shellcode = bytearray()

        # Prologue
        shellcode.extend(b"\x55\x48\x89\xE5\x48\x83\xEC\x40")

        # Get MessagePacket pointer
        shellcode.extend(b"\x48\xB8")
        shellcode.extend(struct.pack("<Q", base + self._rva_get_mp))
        shellcode.extend(b"\xFF\xD0\x48\x89\x45\xF8")

        # Navigate to buffer
        shellcode.extend(b"\x48\x8B\x45\xF8")
        shellcode.extend(b"\x48\x8B\x40\x28")  # +0x28 = Buffer
        shellcode.extend(b"\x48\x8B\x40\x20")  # +0x20 = Data
        shellcode.extend(b"\x48\x83\xC0\x20")  # +0x20 = Raw Start

        # Copy march_data using rep movsb
        shellcode.extend(b"\x48\x89\xC1")  # mov rcx, rax (dest)
        shellcode.extend(b"\x48\xBA")  # mov rdx, src
        shellcode.extend(struct.pack("<Q", content_addr))  # remote address in game process
        shellcode.extend(b"\x49\xC7\xC0")  # mov r8, len
        shellcode.extend(struct.pack("<I", len(march_data)))
        shellcode.extend(b"\x4D\x89\xC1")  # mov r9, r8
        shellcode.extend(b"\x4C\x89\xC1")  # mov rcx, r8
        shellcode.extend(b"\x48\x8B\xFE")  # mov rdi, rsi
        shellcode.extend(struct.pack("<I", content_size))  # length of march data
        shellcode.extend(b"\xF3\xA4")  # rep movsb

        # Set Length and Protocol
        shellcode.extend(b"\x48\x8B\x45\xF8")
        shellcode.extend(b"\xC7\x40\x18\x6F\x00\x00\x00")  # len = 111
        shellcode.extend(b"\x66\xC7\x40\x30\xD7\x19")     # proto = 6615

        # AddSeqId + Send
        shellcode.extend(b"\x48\x8B\x4D\xF8\x48\xB8")
        shellcode.extend(struct.pack("<Q", base + self._rva_add_seq))
        shellcode.extend(b"\xFF\xD0")

        shellcode.extend(b"\x48\x8B\x4D\xF8\xBA\x00\x00\x00\x00\x48\xB8")
        shellcode.extend(struct.pack("<Q", base + self._rva_send))
        shellcode.extend(b"\xFF\xD0")

        # Epilogue
        shellcode.extend(b"\x48\x83\xC4\x40\x5D\xC3")

        return shellcode

    def inject_march(self, zone_id: int, point_id: int, march_template: bytes) -> bool:
        """Inject a march into the game."""
        import ctypes

        handle = self.client["handle"]
        march_data = bytearray(march_template)
        struct.pack_into("<H", march_data, 0x52, zone_id)
        struct.pack_into("<B", march_data, 0x54, point_id)

        # Allocate memory in game process
        addr_data = ctypes.windll.kernel32.VirtualAllocEx(
            handle, 0, len(march_data), 0x3000, 0x40
        )
        ctypes.windll.kernel32.WriteProcessMemory(
            handle, ctypes.c_void_p(addr_data),
            bytes(march_data), len(march_data), None
        )

        shellcode = self.build_march_shellcode(zone_id, point_id, addr_data, len(march_data))
        addr_shell = ctypes.windll.kernel32.VirtualAllocEx(
            handle, 0, len(shellcode), 0x3000, 0x40
        )
        ctypes.windll.kernel32.WriteProcessMemory(
            handle, ctypes.c_void_p(addr_shell),
            bytes(shellcode), len(shellcode), None
        )

        ctypes.windll.kernel32.CreateRemoteThread(
            handle, None, 0, ctypes.c_void_p(addr_shell), None, 0, None
        )
        return True
