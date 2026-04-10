"""
core/frida/bridge.py — Frida Script Bridge
Loads, manages, and communicates with Frida scripts injected into the game process.
"""

import json
import time
import frida
from pathlib import Path
from typing import Callable, Optional


class FridaBridge:
    def __init__(self, process_name: str = None):
        self.process_name = process_name or "Lords Mobile PC"
        self.session: Optional[frida.core.Session] = None
        self.script: Optional[frida.core.Script] = None
        self.device: frida.core.Device = None
        self._messages: list = []

    def attach(self, pid: int = None) -> None:
        """Attach Frida to the game process."""
        self.device = frida.get_local_device()
        if pid:
            self.session = self.device.attach(pid)
        else:
            # Find by name
            processes = self.device.enumerate_processes()
            for p in processes:
                if self.process_name.lower() in p.name.lower():
                    self.session = self.device.attach(p.pid)
                    break
            else:
                raise RuntimeError(f"Process '{self.process_name}' not found")

    def load_script(self, script_name: str, **kwargs) -> None:
        """Load a Frida script by name from core/frida/scripts/."""
        scripts_dir = Path(__file__).parent / "scripts"
        script_path = scripts_dir / f"{script_name}.js"

        if not script_path.exists():
            raise FileNotFoundError(f"Frida script not found: {script_path}")

        with open(script_path) as f:
            source = f.read()

        if self.session:
            self.script = self.session.create_script(source)
            self.script.on("message", self._on_message)
            self.script.load()

    def _on_message(self, message: dict, data: bytes) -> None:
        """Handle messages from Frida script."""
        self._messages.append({"message": message, "data": data})
        if message.get("type") == "error":
            print(f"[Frida Error] {message['stack']}")

    def call(self, func_name: str, *args) -> any:
        """Call an exported function in the Frida script."""
        if not self.script:
            raise RuntimeError("No script loaded")
        return self.script.exports_sync.call(func_name, *args)

    def enumerate_scripts(self) -> list[str]:
        """List available Frida scripts."""
        scripts_dir = Path(__file__).parent / "scripts"
        if not scripts_dir.exists():
            return []
        return [p.stem for p in scripts_dir.glob("*.js")]

    def read_messages(self) -> list:
        """Read and clear pending messages."""
        msgs = self._messages[:]
        self._messages.clear()
        return msgs
