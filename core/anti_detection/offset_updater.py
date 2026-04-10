"""
core/anti_detection/offset_updater.py — Auto Offset Updates
Automatically detects when game updates break memory offsets
and attempts to find new ones via Frida-assisted scanning.
"""

import os
import json
import shutil
import time
from pathlib import Path
from typing import Optional

# Frida integration — scan patterns in game memory
try:
    import frida
    FRIDA_AVAILABLE = True
except ImportError:
    FRIDA_AVAILABLE = False


class OffsetUpdater:
    """
    Scans for new offsets when old ones break.

    Workflow:
    1. check_offsets_valid() — verifies current offsets by reading memory
    2. If broken, scan_for_offsets() — uses Frida to scan memory for new values
    3. auto_update() — backs up old offsets, writes new ones if found

    Requires GameAssembly.dll to be injectable via Frida.
    """

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self._cfg_dir = Path(config_dir)
        else:
            self._cfg_dir = Path(__file__).parent.parent.parent / "config"

        self._offsets_path = self._cfg_dir / "offsets.json"
        self._backup_dir = self._cfg_dir / "offsets_backups"
        self._backup_dir.mkdir(exist_ok=True)

        self._offsets = self._load_offsets()
        self._last_scan_time: Optional[float] = None
        self._needs_manual_review = False

    def _load_offsets(self) -> dict:
        with open(self._offsets_path) as f:
            return json.load(f)

    def _save_offsets(self, offsets: dict) -> None:
        with open(self._offsets_path, "w") as f:
            json.dump(offsets, f, indent=2)

    # -------------------------------------------------------------------------
    # Known coordinate signatures from geotrack.js — used for scanning
    # -------------------------------------------------------------------------
    SIGNATURES = [
        {"name": "Forest (507,59)", "hex": "fb 01 3b 00", "zone": 507, "point": 59},
        {"name": "Test Zone", "hex": "00 02 00 00", "zone": 512, "point": 0},
    ]

    def check_offsets_valid(self, radar) -> bool:
        """
        Verify current offsets still work by reading known game state.
        Returns True if offsets are valid, False if they need updating.
        """
        try:
            if not radar.clients:
                return False

            client = radar.clients[0]
            handle = client["handle"]
            base = client["assembly_base"]

            rvass = self._offsets.get("rvass", {})
            for name, rva_hex in rvass.items():
                addr = base + int(rva_hex, 16)
                # Try to read 4 bytes at the expected address
                import ctypes
                buf = ctypes.create_string_buffer(4)
                bytes_read = ctypes.c_size_t(0)
                result = ctypes.windll.kernel32.ReadProcessMemory(
                    handle,
                    ctypes.c_void_p(addr),
                    buf,
                    4,
                    ctypes.byref(bytes_read)
                )
                if not result or bytes_read.value < 4:
                    print(f"[!] Offset check failed for {name} at 0x{addr:08X}")
                    return False

            print(f"[*] OffsetUpdater: All {len(rvass)} offsets valid")
            return True

        except Exception as e:
            print(f"[!] OffsetUpdater: check failed — {e}")
            return False

    def scan_for_offsets(self, radar) -> dict:
        """
        Use Frida to scan memory and find new RVA offsets.
        Returns a dict of {name: hex_rva} for found offsets.

        This uses the same SIGNATURES pattern from geotrack.js.
        """
        if not FRIDA_AVAILABLE:
            print("[!] Frida not available — cannot scan for offsets")
            return {}

        if not radar.clients:
            print("[!] No game clients found for scanning")
            return {}

        client = radar.clients[0]
        pid = client["pid"]

        try:
            device = frida.get_local_device()
            session = device.attach(pid)

            # Load geotrack.js as a library to reuse its scanning logic
            scripts_dir = Path(__file__).parent / "frida" / "scripts"
            geotrack_path = scripts_dir / "geotrack.js"

            with open(geotrack_path) as f:
                source = f.read()

            script = session.create_script(source)
            messages = []

            def on_message(msg, data):
                messages.append(msg)

            script.on("message", on_message)
            script.load()

            # Give it time to scan
            time.sleep(3)

            # Read exported results
            try:
                results = script.exports_sync.call("rescan", None)
            except Exception:
                results = None

            script.unload()
            session.detach()

            # Parse results into offset dict
            found = self._parse_scan_results(messages)

            print(f"[*] OffsetUpdater scan complete: {len(found)} offset(s) found")
            return found

        except Exception as e:
            print(f"[!] OffsetUpdater: Frida scan failed — {e}")
            return {}

    def _parse_scan_results(self, messages: list) -> dict:
        """
        Parse Frida script messages to extract new offset RVAs.
        Returns dict mapping function names to hex RVA strings.
        """
        found = {}
        for msg in messages:
            if msg.get("type") == "send":
                payload = msg.get("payload", "")
                if isinstance(payload, str) and "offset:" in payload.lower():
                    # Extract offset from messages like "  [✅] address  offset: 0x1D22900"
                    for line in payload.split("\n"):
                        if "offset:" in line.lower():
                            try:
                                parts = line.split("0x")
                                if len(parts) >= 2:
                                    hex_val = "0x" + parts[1].strip()
                                    found["SCANNED"] = hex_val
                            except Exception:
                                pass
        return found

    def auto_update(self, radar) -> bool:
        """
        Main entry point: check, backup, scan, and update offsets.

        Returns True if offsets were updated, False if they are still valid
        or if scan failed (in which case the offsets are flagged for manual review).
        """
        # Step 1: Check if current offsets still work
        if self.check_offsets_valid(radar):
            print("[*] OffsetUpdater: Offsets still valid, no update needed")
            return False

        print("[!] OffsetUpdater: Offsets appear broken — attempting recovery scan...")

        # Step 2: Backup current offsets
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"offsets_{ts}.json"
        shutil.copy2(self._offsets_path, backup_path)
        print(f"[*] OffsetUpdater: Backed up offsets to {backup_path}")

        # Step 3: Attempt to scan for new offsets
        scanned = self.scan_for_offsets(radar)

        if scanned:
            # Step 4: Merge scanned results into current offsets
            new_offsets = self._offsets.copy()
            new_offsets["rvass"] = {**new_offsets.get("rvass", {}), **scanned}
            self._save_offsets(new_offsets)
            print("[+] OffsetUpdater: Offsets updated successfully")
            self._needs_manual_review = False
            return True
        else:
            # Step 5: Flag for manual review
            self._needs_manual_review = True
            print("[!] OffsetUpdater: Auto-scan failed. Flagged for manual review.")
            return False

    @property
    def needs_manual_review(self) -> bool:
        """True if auto-update failed and human review is needed."""
        return self._needs_manual_review

    def restore_backup(self, backup_name: str = "latest") -> bool:
        """Restore offsets from a backup file."""
        try:
            if backup_name == "latest":
                backups = sorted(self._backup_dir.glob("offsets_*.json"))
                if not backups:
                    return False
                backup_path = backups[-1]
            else:
                backup_path = self._backup_dir / backup_name

            shutil.copy2(backup_path, self._offsets_path)
            self._offsets = self._load_offsets()
            print(f"[*] OffsetUpdater: Restored from {backup_path}")
            return True
        except Exception as e:
            print(f"[!] Restore failed: {e}")
            return False
