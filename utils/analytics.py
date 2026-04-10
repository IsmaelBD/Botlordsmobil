"""
utils/analytics.py — Lords Mobile Bot Analytics
Tracks resources, might, kills, and account changes over time.
"""

import json
import csv
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


class BotAnalytics:
    """Tracks and stores bot activity metrics over time."""

    def __init__(self, account_name: str = "default"):
        self.account = account_name
        self.data_dir = Path.home() / ".lordsbot" / "analytics"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.data_dir / f"{account_name}_session.json"
        self.history_file = self.data_dir / f"{account_name}_history.json"

        self.session = self._load_session()
        self.history = self._load_history()
        self.session_start = datetime.now()
        self._session_resources = defaultdict(int)
        self._session_attacks = []
        self._session_marches = []

    # ──────────────────────────────────────────────
    #  Persistence
    # ──────────────────────────────────────────────

    def _load_session(self) -> dict:
        """Load or create session data."""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "started_at": datetime.now().isoformat(),
            "resources_gathered": {},
            "attacks": [],
            "marches": [],
            "state_transitions": [],
            "player_snapshots": [],
        }

    def _load_history(self) -> dict:
        """Load or create historical data."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "daily": [],  # List of daily summaries
            "might_history": [],  # [(timestamp, might), ...]
            "kill_history": [],  # [(timestamp, kills), ...]
        }

    def _save_session(self) -> None:
        """Persist session data to disk."""
        self.session["resources_gathered"] = dict(self._session_resources)
        self.session["attacks"] = self._session_attacks
        self.session["marches"] = self._session_marches
        with open(self.session_file, "w") as f:
            json.dump(self.session, f, indent=2)

    def _save_history(self) -> None:
        """Persist history data to disk."""
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def save(self) -> None:
        """Save all analytics data."""
        self._save_session()
        self._save_history()

    # ──────────────────────────────────────────────
    #  Recording Methods
    # ──────────────────────────────────────────────

    def record_resource_gather(self, resource: str, amount: int) -> None:
        """Record resources gathered this session."""
        self._session_resources[resource] += amount
        self.session["resources_gathered"] = dict(self._session_resources)
        self._save_session()

    def record_attack(self, zone: int, point: int, result: str,
                      troops_deployed: int = 0, kills: int = 0,
                      losses: int = 0) -> None:
        """Record attack result."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "zone": zone,
            "point": point,
            "result": result,
            "troops_deployed": troops_deployed,
            "kills": kills,
            "losses": losses,
        }
        self._session_attacks.append(entry)
        self.session["attacks"] = self._session_attacks
        self._save_session()

        # Update kill history
        if kills > 0:
            self.history.setdefault("kill_history", []).append({
                "timestamp": datetime.now().isoformat(),
                "kills": kills
            })
            self._save_history()

    def record_march_return(self, duration_seconds: float, troops_used: int,
                            resources_delivered: dict = None) -> None:
        """Record march statistics."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "troops_used": troops_used,
            "resources_delivered": resources_delivered or {},
        }
        self._session_marches.append(entry)
        self.session["marches"] = self._session_marches
        self._save_session()

        # Aggregate resources delivered
        if resources_delivered:
            for resource, amount in resources_delivered.items():
                self.record_resource_gather(resource, amount)

    def record_state_transition(self, from_state: str, to_state: str) -> None:
        """Record FSM state transition."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "from": from_state,
            "to": to_state,
        }
        self.session.setdefault("state_transitions", []).append(entry)
        self._save_session()

    def record_action(self, action: str, game_state: dict = None) -> None:
        """Generic action recorder for FSM integration."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "game_state": game_state,
        }
        self.session.setdefault("actions", []).append(entry)
        self._save_session()

    def snapshot_player_state(self, state: dict) -> None:
        """Take a full snapshot of player state from memory."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "gold": state.get("Gold", 0),
            "food": state.get("Food", 0),
            "wood": state.get("Wood", 0),
            "stone": state.get("Stone", 0),
            "iron": state.get("Iron", 0),
            "gems": state.get("Gems", 0),
            "might": state.get("Might", 0),
            "level": state.get("Level", 0),
            "tutorial_step": state.get("TutorialStep", 0),
            "AccountId": state.get("AccountId", ""),
        }
        self.session.setdefault("player_snapshots", []).append(snapshot)
        self._save_session()

        # Track might progression
        might = state.get("Might", 0)
        if might > 0:
            self.history.setdefault("might_history", []).append({
                "timestamp": datetime.now().isoformat(),
                "might": might
            })
            self._save_history()

    # ──────────────────────────────────────────────
    #  Reporting Methods
    # ──────────────────────────────────────────────

    def generate_session_report(self) -> str:
        """Generate a text report of this session's activity."""
        lines = []
        lines.append("=" * 50)
        lines.append("  SESSION REPORT")
        lines.append("=" * 50)

        # Duration
        started = datetime.fromisoformat(self.session.get("started_at", datetime.now().isoformat()))
        duration = datetime.now() - started
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        lines.append(f"Session Duration: {hours}h {minutes}m {seconds}s")
        lines.append("")

        # Resources gathered
        resources = self.session.get("resources_gathered", {})
        if resources:
            lines.append("Resources Gathered:")
            for resource, amount in sorted(resources.items()):
                lines.append(f"  {resource}: {amount:,}")
        else:
            lines.append("Resources Gathered: None")

        lines.append("")

        # Attacks
        attacks = self.session.get("attacks", [])
        lines.append(f"Total Attacks: {len(attacks)}")
        if attacks:
            successful = sum(1 for a in attacks if a.get("result") == "success")
            lines.append(f"  Successful: {successful}")
            lines.append(f"  Failed: {len(attacks) - successful}")
            total_kills = sum(a.get("kills", 0) for a in attacks)
            total_losses = sum(a.get("losses", 0) for a in attacks)
            lines.append(f"  Total Kills: {total_kills:,}")
            lines.append(f"  Total Losses: {total_losses:,}")

        lines.append("")

        # Marches
        marches = self.session.get("marches", [])
        lines.append(f"Total Marches: {len(marches)}")
        if marches:
            avg_duration = sum(m.get("duration_seconds", 0) for m in marches) / len(marches)
            lines.append(f"  Avg Duration: {avg_duration:.0f}s")
            total_troops = sum(m.get("troops_used", 0) for m in marches)
            lines.append(f"  Total Troops Used: {total_troops:,}")

        lines.append("")

        # State transitions
        transitions = self.session.get("state_transitions", [])
        if transitions:
            lines.append(f"State Transitions: {len(transitions)}")
            states = [t["to"] for t in transitions]
            from collections import Counter
            state_counts = Counter(states)
            for state, count in state_counts.most_common(5):
                lines.append(f"  {state}: {count}")

        lines.append("=" * 50)
        return "\n".join(lines)

    def generate_history_report(self, days: int = 7) -> str:
        """Generate a report of historical trends."""
        lines = []
        lines.append("=" * 50)
        lines.append(f"  HISTORY REPORT ({days} days)")
        lines.append("=" * 50)

        # Might progression
        might_history = self.history.get("might_history", [])
        if might_history:
            cutoff = datetime.now() - timedelta(days=days)
            recent = [
                (datetime.fromisoformat(h["timestamp"]), h["might"])
                for h in might_history
                if datetime.fromisoformat(h["timestamp"]) > cutoff
            ]
            if recent:
                recent.sort()
                start_might = recent[0][1]
                end_might = recent[-1][1]
                lines.append(f"\nMight Progress ({days} days):")
                lines.append(f"  Start: {start_might:,}")
                lines.append(f"  Current: {end_might:,}")
                lines.append(f"  Gained: {end_might - start_might:,}")
                if start_might > 0:
                    pct = ((end_might - start_might) / start_might) * 100
                    lines.append(f"  Growth: {pct:.1f}%")

        # Kill history
        kill_history = self.history.get("kill_history", [])
        if kill_history:
            cutoff = datetime.now() - timedelta(days=days)
            recent_kills = [
                h for h in kill_history
                if datetime.fromisoformat(h["timestamp"]) > cutoff
            ]
            if recent_kills:
                total = sum(h["kills"] for h in recent_kills)
                lines.append(f"\nKill Stats ({days} days):")
                lines.append(f"  Total Kills: {total:,}")
                lines.append(f"  Avg/Kill Event: {total / len(recent_kills):.1f}")

        # Daily summaries
        daily = self.history.get("daily", [])
        if daily:
            cutoff = datetime.now() - timedelta(days=days)
            recent_daily = [
                d for d in daily
                if datetime.fromisoformat(d.get("date", "2000-01-01")) > cutoff.date()
            ]
            if recent_daily:
                lines.append(f"\nDaily Activity ({len(recent_daily)} days logged):")
                for day in recent_daily[-5:]:  # Last 5 days
                    date = day.get("date", "?")
                    attacks = day.get("attacks", 0)
                    resources = day.get("resources_gathered", {})
                    total_res = sum(resources.values()) if isinstance(resources, dict) else 0
                    lines.append(f"  {date}: {attacks} attacks, {total_res:,} resources")

        if not might_history and not kill_history and not daily:
            lines.append("\nNo historical data available yet.")
            lines.append("Run the bot for a few sessions to see trends.")

        lines.append("=" * 50)
        return "\n".join(lines)

    def export_csv(self, output_path: str) -> str:
        """Export analytics as CSV for spreadsheet analysis."""
        rows = []

        # Resource gatherings
        resources = self.session.get("resources_gathered", {})
        for resource, amount in resources.items():
            rows.append({
                "category": "resource",
                "timestamp": datetime.now().isoformat(),
                "type": resource,
                "value": amount,
                "details": ""
            })

        # Attacks
        for attack in self.session.get("attacks", []):
            rows.append({
                "category": "attack",
                "timestamp": attack.get("timestamp", ""),
                "type": "attack",
                "value": attack.get("kills", 0),
                "details": f"zone={attack.get('zone')}, point={attack.get('point')}, result={attack.get('result')}"
            })

        # Marches
        for march in self.session.get("marches", []):
            rows.append({
                "category": "march",
                "timestamp": march.get("timestamp", ""),
                "type": "march_duration",
                "value": march.get("duration_seconds", 0),
                "details": f"troops={march.get('troops_used', 0)}"
            })

        # Might snapshots
        for snapshot in self.session.get("player_snapshots", []):
            rows.append({
                "category": "snapshot",
                "timestamp": snapshot.get("timestamp", ""),
                "type": "might",
                "value": snapshot.get("might", 0),
                "details": f"gold={snapshot.get('gold', 0)}, food={snapshot.get('food', 0)}"
            })

        if not rows:
            return "No data to export"

        # Write CSV
        fieldnames = ["category", "timestamp", "type", "value", "details"]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return f"Exported {len(rows)} rows to {output_path}"

    def clear_session(self) -> None:
        """Clear current session data (keeps history)."""
        self.session = {
            "started_at": datetime.now().isoformat(),
            "resources_gathered": {},
            "attacks": [],
            "marches": [],
            "state_transitions": [],
            "player_snapshots": [],
        }
        self._session_resources.clear()
        self._session_attacks.clear()
        self._session_marches.clear()
        self._save_session()

    def clear_history(self) -> None:
        """Clear all historical data."""
        self.history = {
            "daily": [],
            "might_history": [],
            "kill_history": [],
        }
        self._save_history()

    def get_session_stats(self) -> dict:
        """Get current session statistics."""
        return {
            "started_at": self.session.get("started_at", ""),
            "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "resources_gathered": dict(self._session_resources),
            "total_attacks": len(self._session_attacks),
            "total_marches": len(self._session_marches),
            "total_kills": sum(a.get("kills", 0) for a in self._session_attacks),
            "total_losses": sum(a.get("losses", 0) for a in self._session_attacks),
        }

    def get_history_stats(self) -> dict:
        """Get historical statistics."""
        might_history = self.history.get("might_history", [])
        kill_history = self.history.get("kill_history", [])

        if might_history:
            mights = [h["might"] for h in might_history]
            current_might = mights[-1] if mights else 0
            peak_might = max(mights) if mights else 0
        else:
            current_might = 0
            peak_might = 0

        return {
            "current_might": current_might,
            "peak_might": peak_might,
            "total_kills": sum(h["kills"] for h in kill_history),
            "days_logged": len(self.history.get("daily", [])),
        }
