"""
core/win32/hands.py — Win32 Ghost Client
Sends mouse clicks and keyboard input to the game window.
Integrated with Phase 3 Anti-Detection System.
"""

import ctypes
import ctypes.wintypes
import time
import json
from pathlib import Path
from typing import Optional

from core.anti_detection import AntiDetection, HumanClicker


class Win32GhostClient:
    def __init__(self, window_title: str = None):
        self.window_title = window_title or self._load_window_title()
        self.hwnd = self._find_window()
        self._config = self._load_config()

        # Phase 3 Anti-Detection integration
        self.anti_detection = AntiDetection()
        self.human_clicker = HumanClicker()
        if self.hwnd:
            self.human_clicker.set_window(self.hwnd)

    def _load_window_title(self) -> str:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            return json.load(f)["game"]["window_title"]

    def _load_config(self) -> dict:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            return json.load(f)

    def _find_window(self):
        hwnd = ctypes.windll.user32.FindWindowW(None, self.window_title)
        if not hwnd:
            # Try partial match
            hwnd = ctypes.windll.user32.FindWindowW(None, None)
            while hwnd:
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                    if self.window_title.lower() in buff.value.lower():
                        return hwnd
                hwnd = ctypes.windll.user32.GetWindowW(hwnd, 2)  # GW_HWNDNEXT
        return hwnd

    def _screen_to_client(self, x: int, y: int) -> tuple:
        """Convert screen coordinates to client coordinates."""
        if not self.hwnd:
            return x, y
        point = ctypes.wintypes.POINT(x, y)
        ctypes.windll.user32.ScreenToClient(self.hwnd, ctypes.byref(point))
        return point.x, point.y

    def vClick(self, x: int, y: int, delay_ms: Optional[float] = None) -> None:
        """
        Virtual click at coordinates (screen space).

        Uses AntiDetection for randomized delays and HumanClicker for
        Bezier-curved mouse movement instead of instant teleportation.
        """
        if not self.hwnd:
            raise RuntimeError(f"Window '{self.window_title}' not found")

        # Random delay from anti-detection system (or use provided value)
        delay = delay_ms if delay_ms is not None else self.anti_detection.random_action_delay()

        client_x, client_y = self._screen_to_client(x, y)

        # Move mouse along a human-like Bezier path
        self.human_clicker.human_move(client_x, client_y, client_x, client_y, duration_ms=200)

        # Use human_clicker for the actual click with randomization
        self.human_clicker.human_click(x, y, delay_ms=delay)

    def vClickFast(self, x: int, y: int, delay_ms: int = None) -> None:
        """
        Standard fast click (no anti-detection humanization).
        Use sparingly — only for non-critical UI elements.
        """
        if not self.hwnd:
            raise RuntimeError(f"Window '{self.window_title}' not found")

        delay_ms = delay_ms or self._config["timing"]["click_delay_ms"]
        client_x, client_y = self._screen_to_client(x, y)

        # Send mouse move
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0200, 0,
            ctypes.wintypes.MAKELONG(client_x, client_y)
        )
        time.sleep(delay_ms / 1000)

        # Send mouse down
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0201, 1,
            ctypes.wintypes.MAKELONG(client_x, client_y)
        )
        time.sleep(delay_ms / 1000)

        # Send mouse up
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0202, 0,
            ctypes.wintypes.MAKELONG(client_x, client_y)
        )

    def force_resolution(self, width: int, height: int) -> None:
        """Request game to switch resolution."""
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0112, 0xF170, 3  # WM_DISPLAYCHANGE
        )
