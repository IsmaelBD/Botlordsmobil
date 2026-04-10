"""
modules/labyrinth/bot.py — Labyrinth Bot
Automatically solves the labyrinth puzzle using pathfinding.
Phase 3 Anti-Detection: randomized timing throughout.
"""

import time
import json
import random
from pathlib import Path
from typing import Optional

from core.memory.radar import MemoryRadar
from core.win32.hands import Win32GhostClient
from core.anti_detection import AntiDetection, SessionGuard


# Cardinal directions for pathfinding
DIRECTIONS = [
    (0, -1),   # North (up)
    (1, 0),    # East (right)
    (0, 1),    # South (down)
    (-1, 0),   # West (left)
]

DIR_NAMES = ["N", "E", "S", "W"]

# Default labyrinth UI positions
DEFAULT_LABYRINTH_POSITIONS = {
    "labyrinth_button": (80, 400),
    "enter_btn": (540, 480),
    "move_north": (540, 200),
    "move_south": (540, 520),
    "move_east": (700, 360),
    "move_west": (380, 360),
    "map_view": (540, 360),
    "close_button": (870, 155),
}


class LabyrinthBot:
    """
    Win32 macro-based labyrinth solver.
    Uses BFS pathfinding to find optimal path through the labyrinth.
    Phase 3 Anti-Detection: session guarding and randomized timing.
    """

    def __init__(self):
        self.radar = MemoryRadar()
        self.hands = Win32GhostClient()
        self.anti_detection = AntiDetection()
        self.session_guard = SessionGuard()
        self._load_config()
        self.active = False

        # Labyrinth state
        self.labyrinth_size = 7  # 7x7 default
        self.current_pos = (0, 0)
        self.goal_pos = (6, 6)
        self.walls = set()
        self.visited = set()
        self.current_path = []

    def _load_config(self) -> None:
        cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
        with open(cfg) as f:
            self._cfg = json.load(f)

        self.resolution = self._cfg["game"]["resolution"]
        self.labyrinth_size = self._cfg.get("labyrinth", {}).get("size", 7)
        self.goal_pos = tuple(self._cfg.get("labyrinth", {}).get("goal", [6, 6]))

        # Load positions
        pos_cfg = self._cfg.get("labyrinth", {}).get("positions", DEFAULT_LABYRINTH_POSITIONS)
        self.labyrinth_btn = tuple(pos_cfg.get("labyrinth_button", DEFAULT_LABYRINTH_POSITIONS["labyrinth_button"]))
        self.enter_btn = tuple(pos_cfg.get("enter_btn", DEFAULT_LABYRINTH_POSITIONS["enter_btn"]))
        self.move_north = tuple(pos_cfg.get("move_north", DEFAULT_LABYRINTH_POSITIONS["move_north"]))
        self.move_south = tuple(pos_cfg.get("move_south", DEFAULT_LABYRINTH_POSITIONS["move_south"]))
        self.move_east = tuple(pos_cfg.get("move_east", DEFAULT_LABYRINTH_POSITIONS["move_east"]))
        self.move_west = tuple(pos_cfg.get("move_west", DEFAULT_LABYRINTH_POSITIONS["move_west"]))
        self.map_view = tuple(pos_cfg.get("map_view", DEFAULT_LABYRINTH_POSITIONS["map_view"]))
        self.close_btn = tuple(pos_cfg.get("close_button", DEFAULT_LABYRINTH_POSITIONS["close_button"]))

    def verify_ready(self) -> bool:
        """Check that game is running and accessible."""
        if not self.radar.clients:
            print("[!] LabyrinthBot: Game not detected. Is Lords Mobile running?")
            return False
        if not self.hands.hwnd:
            print("[!] LabyrinthBot: Game window not found.")
            return False
        return True

    def _click(self, x: int, y: int, delay_ms: float = None) -> None:
        """Click with anti-detection humanization."""
        delay = delay_ms or self.anti_detection.random_action_delay()
        self.hands.vClick(x, y, delay_ms=delay)

    def _click_direction(self, direction: str) -> None:
        """Click the appropriate movement button."""
        dir_map = {
            "N": self.move_north,
            "E": self.move_east,
            "S": self.move_south,
            "W": self.move_west,
        }
        if direction in dir_map:
            self._click(*dir_map[direction])

    def bfs_pathfind(self, start: tuple, goal: tuple, walls: set) -> Optional[list]:
        """
        BFS pathfinding from start to goal avoiding walls.
        Returns list of (x, y) positions or None if no path exists.
        """
        from collections import deque

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            pos, path = queue.popleft()

            if pos == goal:
                return path

            for dx, dy in DIRECTIONS:
                nx, ny = pos[0] + dx, pos[1] + dy

                # Check bounds
                if not (0 <= nx < self.labyrinth_size and 0 <= ny < self.labyrinth_size):
                    continue

                next_pos = (nx, ny)
                if next_pos in visited or next_pos in walls:
                    continue

                visited.add(next_pos)
                queue.append((next_pos, path + [next_pos]))

        return None

    def detect_walls(self) -> None:
        """
        Detect walls by scanning the labyrinth view.
        In a real implementation, this would analyze game screen pixels
        or read from game memory. Here we use a simplified approach.
        """
        # Clear previous walls
        self.walls.clear()

        # Simplified: randomly mark some cells as walls based on labyrinth layout
        # In reality, this would come from game state analysis
        for y in range(self.labyrinth_size):
            for x in range(self.labyrinth_size):
                # Border walls
                if x == 0 or y == 0 or x == self.labyrinth_size - 1 or y == self.labyrinth_size - 1:
                    self.walls.add((x, y))

    def solve_path(self) -> bool:
        """
        Calculate the optimal path through the labyrinth.
        Returns True if a path was found and stored in current_path.
        """
        self.detect_walls()
        path = self.bfs_pathfind(self.current_pos, self.goal_pos, self.walls)

        if path:
            self.current_path = path
            print(f"[+] LabyrinthBot: Path found with {len(path)} steps")
            for i, pos in enumerate(path):
                if i > 0:
                    prev = path[i - 1]
                    dx = pos[0] - prev[0]
                    dy = pos[1] - prev[1]
                    direction = DIR_NAMES[DIRECTIONS.index((dx, dy))]
                    print(f"    Step {i}: ({pos[0]}, {pos[1]}) - {direction}")
            return True
        else:
            print("[!] LabyrinthBot: No path found to goal!")
            return False

    def follow_path(self) -> bool:
        """
        Execute the current path by clicking movement buttons.
        Returns True if the path was followed successfully.
        """
        if not self.current_path:
            print("[!] LabyrinthBot: No path to follow. Call solve_path() first.")
            return False

        try:
            if not self.session_guard.should_act("labyrinth"):
                print("[*] LabyrinthBot: Rate limit reached, waiting...")
                pause = self.anti_detection.random_cycle_delay()
                print(f"[*] Random pause for {pause:.1f}s")
                time.sleep(pause)
                return False

            for i, pos in enumerate(self.current_path):
                if i == 0:
                    # Skip starting position
                    continue

                prev = self.current_path[i - 1]
                dx = pos[0] - prev[0]
                dy = pos[1] - prev[1]

                # Determine direction name
                direction = DIR_NAMES[DIRECTIONS.index((dx, dy))]

                print(f"[*] LabyrinthBot: Step {i}/{len(self.current_path)-1} → {direction} ({pos[0]}, {pos[1]})")

                # Click the movement button
                self._click_direction(direction)

                # Random delay between moves
                move_delay = self.anti_detection.human_delay(min_ms=600, max_ms=1200)
                time.sleep(move_delay / 1000)

                # Mark as visited
                self.visited.add(pos)
                self.current_pos = pos

            self.session_guard.record_action("labyrinth")
            print(f"[+] LabyrinthBot: Reached goal at {self.goal_pos}")
            return True

        except Exception as e:
            print(f"[!] Labyrinth navigation failed: {e}")
            return False

    def run_cycle(self) -> None:
        """
        Run one labyrinth solving cycle.
        Enters labyrinth, solves path, and navigates to goal.
        """
        if not self.verify_ready():
            return

        if self.session_guard.enforced_cooldown():
            remaining = self.session_guard.cooldown_remaining
            print(f"[*] LabyrinthBot: In cooldown, {remaining:.0f}s remaining")
            return

        print(f"[*] LabyrinthBot: Starting labyrinth cycle (size={self.labyrinth_size}x{self.labyrinth_size})")

        try:
            # 1. Open labyrinth
            self._click(*self.labyrinth_btn)
            delay = self.anti_detection.human_delay(min_ms=1500, max_ms=3000)
            time.sleep(delay / 1000)

            # 2. Enter labyrinth
            self._click(*self.enter_btn)
            delay = self.anti_detection.human_delay(min_ms=1000, max_ms=2000)
            time.sleep(delay / 1000)

            # 3. Open map view to see layout
            self._click(*self.map_view)
            delay = self.anti_detection.human_delay(min_ms=800, max_ms=1500)
            time.sleep(delay / 1000)

            # 4. Solve the path
            if not self.solve_path():
                self._click(*self.close_btn)
                return

            # 5. Close map view
            self._click(*self.close_btn)
            delay = self.anti_detection.human_delay(min_ms=500, max_ms=1000)
            time.sleep(delay / 1000)

            # 6. Follow the path
            success = self.follow_path()

            # 7. Close labyrinth UI
            self._click(*self.close_btn)
            delay = self.anti_detection.human_delay(min_ms=400, max_ms=800)
            time.sleep(delay / 1000)

            if success:
                print(f"[+] LabyrinthBot: Cycle complete — reached goal!")
            else:
                print(f"[!] LabyrinthBot: Cycle failed")

        except Exception as e:
            print(f"[!] LabyrinthBot: Cycle error: {e}")
