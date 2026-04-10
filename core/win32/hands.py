"""
core/win32/hands.py — Win32 Ghost Client
Sends mouse clicks and keyboard input to the game window.
"""

import ctypes
import time
import json
from pathlib import Path


class Win32GhostClient:
    def __init__(self, window_title: str = None):
        self.window_title = window_title or self._load_window_title()
        self.hwnd = self._find_window()
        self._config = self._load_config()

    def _load_window_title(self) -> str:
        cfg = Path(__file__).parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            return json.load(f)["game"]["window_title"]

    def _load_config(self) -> dict:
        cfg = Path(__file__).parent.parent / "config" / "settings.json"
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

    def vClick(self, x: int, y: int, delay_ms: int = None) -> None:
        """Virtual click at coordinates (screen space)."""
        if not self.hwnd:
            raise RuntimeError(f"Window '{self.window_title}' not found")

        delay_ms = delay_ms or self._config["timing"]["click_delay_ms"]
        client_x, client_y = self._screen_to_client(x, y)

        # Send mouse move
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0200, 0,
            ctypes.wintypes.MAKELONG(client_x, client_y)  # WM_MOUSEMOVE
        )
        time.sleep(delay_ms / 1000)

        # Send mouse down
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0201, 1,
            ctypes.wintypes.MAKELONG(client_x, client_y)  # WM_LBUTTONDOWN
        )
        time.sleep(delay_ms / 1000)

        # Send mouse up
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0202, 0,
            ctypes.wintypes.MAKELONG(client_x, client_y)  # WM_LBUTTONUP
        )

    def force_resolution(self, width: int, height: int) -> None:
        """Request game to switch resolution."""
        ctypes.windll.user32.SendMessageW(
            self.hwnd, 0x0112, 0xF170, 3  # WM_DISPLAYCHANGE
        )
