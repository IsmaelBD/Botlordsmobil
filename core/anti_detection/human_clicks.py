"""
core/anti_detection/human_clicks.py — Human-like Click Patterns
Makes mouse movements and clicks feel human, not robotic.
Uses Bezier curves for smooth path movement.
"""

import random
import time
import ctypes
import ctypes.wintypes
from typing import Optional, Tuple


class HumanClicker:
    """
    Human-like clicker using Bezier curves for mouse movement.
    Key behaviors:
    - Movement follows a curved path, not a straight line
    - Tiny random coordinate offsets (±2px)
    - Randomized press duration (±10ms)
    - Random delays before/after clicks
    """

    def __init__(self):
        self.coord_offset_max = 2      # ±2px coordinate jitter
        self.press_duration_jitter = 10  # ±10ms press duration jitter
        self.pre_click_delay_ms = 5    # delay before click
        self.post_click_delay_ms = 8   # delay after click
        self.scroll_min_ms = 100
        self.scroll_max_ms = 300
        self._hwnd: Optional[int] = None

    def set_window(self, hwnd: int) -> None:
        """Set the target window handle."""
        self._hwnd = hwnd

    def bezier_curve(self, start: Tuple[float, float], end: Tuple[float, float], t: float) -> Tuple[float, float]:
        """
        Cubic Bezier curve for smooth mouse movement.
        Uses two control points for natural-looking curves.

        P(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

        t: parameter from 0.0 to 1.0
        Returns interpolated (x, y).
        """
        x0, y0 = start
        x3, y3 = end

        # Control points offset perpendicular to the movement direction
        dx = x3 - x0
        dy = y3 - y0

        # Perpendicular offset for natural curves
        perp_x = -dy
        perp_y = dx
        length = (dx * dx + dy * dy) ** 0.5 + 1e-6
        perp_x /= length
        perp_y /= length

        # Random curve magnitude (10-40% of distance)
        curve_magnitude = random.uniform(0.1, 0.4) * length

        # Two control points
        mid_x = (x0 + x3) / 2
        mid_y = (y0 + y3) / 2

        # Offset control points perpendicular to line
        offset1 = random.uniform(0.2, 0.4)
        offset2 = random.uniform(0.6, 0.8)

        x1 = mid_x + perp_x * curve_magnitude * offset1 * random.choice([-1, 1])
        y1 = mid_y + perp_y * curve_magnitude * offset1 * random.choice([-1, 1])
        x2 = mid_x + perp_x * curve_magnitude * offset2 * random.choice([-1, 1])
        y2 = mid_y + perp_y * curve_magnitude * offset2 * random.choice([-1, 1])

        # Cubic Bezier formula
        mt = 1 - t
        bx = mt**3 * x0 + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x3
        by = mt**3 * y0 + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y3

        return bx, by

    def human_move(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 200) -> None:
        """
        Move mouse along a Bezier path, not a straight line.
        Sends WM_MOUSEMOVE messages to the target window.
        """
        if not self._hwnd:
            return

        steps = max(int(duration_ms / 10), 5)  # At least 5 steps
        for i in range(steps + 1):
            t = i / steps
            bx, by = self.bezier_curve((float(x1), float(y1)), (float(x2), float(y2)), t)
            cx, cy = self._screen_to_client(int(bx), int(by))

            ctypes.windll.user32.SendMessageW(
                self._hwnd, 0x0200, 0,
                ctypes.wintypes.MAKELONG(cx, cy)
            )
            time.sleep(duration_ms / steps / 1000)

    def human_click(self, x: int, y: int, delay_ms: Optional[float] = None) -> None:
        """
        Click with human-like randomization:
        - Tiny random offset to coordinates (±2px)
        - Random press duration (±10ms)
        - Random pre/post click delays
        """
        if not self._hwnd:
            return

        # Add coordinate jitter
        jx = random.randint(-self.coord_offset_max, self.coord_offset_max)
        jy = random.randint(-self.coord_offset_max, self.coord_offset_max)
        cx, cy = self._screen_to_client(x + jx, y + jy)

        # Pre-click delay (slight pause before moving)
        if self.pre_click_delay_ms > 0:
            time.sleep(self.pre_click_delay_ms / 1000)

        # Move mouse to position
        ctypes.windll.user32.SendMessageW(
            self._hwnd, 0x0200, 0,
            ctypes.wintypes.MAKELONG(cx, cy)
        )

        # Randomized press duration (within ±10ms of declared delay)
        press_ms = (delay_ms or random.uniform(40, 80)) + random.uniform(
            -self.press_duration_jitter, self.press_duration_jitter
        )

        # Mouse down
        ctypes.windll.user32.SendMessageW(
            self._hwnd, 0x0201, 1,
            ctypes.wintypes.MAKELONG(cx, cy)
        )
        time.sleep(press_ms / 1000)

        # Mouse up
        ctypes.windll.user32.SendMessageW(
            self._hwnd, 0x0202, 0,
            ctypes.wintypes.MAKELONG(cx, cy)
        )

        # Post-click delay
        if self.post_click_delay_ms > 0:
            time.sleep(self.post_click_delay_ms / 1000)

    def random_scroll(self, direction: str = 'down', amount: Optional[int] = None) -> None:
        """
        Scroll with human-like speed and amount.
        Uses WM_VSCROLL / WM_HSCROLL or mouse wheel events.
        """
        if not self._hwnd:
            return

        # Randomize scroll amount if not specified
        if amount is None:
            amount = random.randint(3, 8)

        # Randomize wheel delta direction
        delta = amount * (1 if direction == 'down' else -1)
        wheel_delta = delta * 120  # WHEEL_DELTA = 120

        # Human-like pause before scroll
        time.sleep(random.uniform(0.05, 0.15))

        # Send mouse wheel message
        ctypes.windll.user32.SendMessageW(
            self._hwnd, 0x020A, wheel_delta,  # WM_MOUSEWHEEL
            ctypes.wintypes.MAKELONG(0, 0)
        )

        time.sleep(random.uniform(0.05, 0.15))

    def _screen_to_client(self, x: int, y: int) -> Tuple[int, int]:
        """Convert screen coordinates to client coordinates."""
        if not self._hwnd:
            return x, y
        point = ctypes.wintypes.POINT(x, y)
        ctypes.windll.user32.ScreenToClient(self._hwnd, ctypes.byref(point))
        return point.x, point.y
