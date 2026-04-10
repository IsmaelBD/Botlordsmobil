"""
core/memory/radar.py — Memory Radar
Reads game memory via Windows API (ctypes).
"""

import ctypes
import json
from pathlib import Path
from typing import Optional

PUL_SELECTION = 0x1F0FFF


class MemoryRadar:
    def __init__(self, process_name: str = None):
        self.process_name = process_name or self._load_process_name()
        self.clients: list[dict] = []
        self._find_clients()

    def _load_process_name(self) -> str:
        cfg = Path(__file__).parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            return json.load(f)["game"]["window_title"]

    def _find_clients(self) -> None:
        """Enumerate processes and find game by name."""
        PROCESS_QUERY_INFORMATION = 0x0400
        SYNCHRONIZE = 0x100000

        # Snap all processes
        snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000002, 0)  # TH32CS_SNAPPROCESS
        pe = ctypes.Structure
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * 260),
            ]

        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

        if ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
            while True:
                exe = pe.szExeFile.decode("utf-8", errors="ignore")
                if self.process_name.lower() in exe.lower():
                    pid = pe.th32ProcessID
                    handle = ctypes.windll.kernel32.OpenProcess(
                        PUL_SELECTION, False, pid
                    )
                    mod = self._get_module_base(snapshot, pid)
                    self.clients.append({
                        "name": exe,
                        "pid": pid,
                        "handle": handle,
                        "assembly_base": mod,
                    })
                if not ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                    break

        ctypes.windll.kernel32.CloseHandle(snapshot)

    def _get_module_base(self, snapshot, pid: int) -> int:
        """Get GameAssembly.dll base address."""
        class MODULEENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_ulong),
                ("th32ModuleID", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("GlblcntUsage", ctypes.c_ulong),
                ("ProccntUsage", ctypes.c_ulong),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_ulong)),
                ("modBaseSize", ctypes.c_ulong),
                ("hModule", ctypes.c_void_p),
                ("szModule", ctypes.c_char * 256),
                ("szExePath", ctypes.c_char * 260),
            ]

        me = MODULEENTRY32()
        me.dwSize = ctypes.sizeof(MODULEENTRY32)

        snap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000008, pid)  # TH32CS_SNAPMODULE
        if snap == -1:
            return 0

        base = 0
        if ctypes.windll.kernel32.Module32FirstW(snap, ctypes.byref(me)):
            while True:
                name = me.szModule.decode("utf-8", errors="ignore")
                if "GameAssembly" in name:
                    base = ctypes.addressof(me.modBaseAddr.contents)
                    break
                if not ctypes.windll.kernel32.Module32NextW(snap, ctypes.byref(me)):
                    break

        ctypes.windll.kernel32.CloseHandle(snap)
        return base

    def read_pointer(self, handle, address: int) -> int:
        buf = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.ReadProcessMemory(
            handle, ctypes.c_void_p(address),
            ctypes.byref(buf), 8, None
        )
        return buf.value

    def read_uint32(self, handle, address: int) -> int:
        buf = ctypes.c_ulong(0)
        ctypes.windll.kernel32.ReadProcessMemory(
            handle, ctypes.c_void_p(address),
            ctypes.byref(buf), 4, None
        )
        return buf.value

    def read_byte(self, handle, address: int) -> int:
        buf = ctypes.c_ubyte(0)
        ctypes.windll.kernel32.ReadProcessMemory(
            handle, ctypes.c_void_p(address),
            ctypes.byref(buf), 1, None
        )
        return buf.value

    def get_player_state(self, handle, assembly_base: int) -> Optional[dict]:
        """Read player state from game memory."""
        cfg_path = Path(__file__).parent.parent / "config" / "offsets.json"
        with open(cfg_path) as f:
            cfg = json.load(f)

        ptrs = cfg["pointers"]
        dm_typeinfo_ptr = assembly_base + int(ptrs["dm_typeinfo"], 16)
        type_info_addr = self.read_pointer(handle, dm_typeinfo_ptr)
        if type_info_addr == 0:
            return None

        static_fields_ptr = self.read_pointer(handle, type_info_addr + 0xB8)
        instance_ptr = self.read_pointer(handle, static_fields_ptr + 0x18)
        if instance_ptr == 0:
            return None

        role_attr = instance_ptr + 0x470

        return {
            "Level": self.read_byte(handle, role_attr + 0x32),
            "Diamond": self.read_uint32(handle, role_attr + 0x98),
            "TutorialStep": self.read_uint32(handle, role_attr + 0x80),
        }
