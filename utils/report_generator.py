"""
utils/report_generator.py — Generate formatted reports
"""

from datetime import datetime, timedelta
from typing import Optional


class ReportGenerator:
    """Generate formatted text and ASCII reports from analytics data."""

    def __init__(self, analytics):
        self.analytics = analytics

    def daily_summary(self) -> str:
        """Today's summary with key metrics."""
        stats = self.analytics.get_session_stats()
        history = self.analytics.get_history_stats()

        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append("│" + " 📊 DAILY SUMMARY ".center(48) + "│")
        lines.append("├" + "─" * 48 + "┤")

        # Session stats
        duration = stats.get("duration_seconds", 0)
        hours, remainder = divmod(int(duration), 3600)
        minutes = remainder // 60
        lines.append(f"│ Session Runtime: {hours}h {minutes}m".ljust(48) + "│")

        # Resources
        resources = stats.get("resources_gathered", {})
        if resources:
            total_res = sum(resources.values())
            lines.append(f"│ Resources Gathered: {total_res:,}".ljust(48) + "│")
            for res, amount in list(resources.items())[:3]:
                lines.append(f"│   • {res.title()}: {amount:,}".ljust(48) + "│")
        else:
            lines.append(f"│ Resources Gathered: 0".ljust(48) + "│")

        # Combat
        attacks = stats.get("total_attacks", 0)
        kills = stats.get("total_kills", 0)
        losses = stats.get("total_losses", 0)
        lines.append(f"│ Attacks: {attacks} (K:{kills} L:{losses})".ljust(48) + "│")

        # Might
        might = history.get("current_might", 0)
        lines.append(f"│ Current Might: {might:,}".ljust(48) + "│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    def weekly_trends(self) -> str:
        """7-day trend analysis."""
        history = self.analytics.history
        might_history = history.get("might_history", [])
        kill_history = history.get("kill_history", [])

        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append("│" + " 📈 WEEKLY TRENDS (7 days) ".center(48) + "│")
        lines.append("├" + "─" * 48 + "┤")

        # Might trend
        cutoff = datetime.now() - timedelta(days=7)
        recent_might = [
            (datetime.fromisoformat(h["timestamp"]), h["might"])
            for h in might_history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]

        if len(recent_might) >= 2:
            recent_might.sort()
            start_might = recent_might[0][1]
            end_might = recent_might[-1][1]
            gain = end_might - start_might
            pct = (gain / start_might * 100) if start_might > 0 else 0
            lines.append(f"│ Might Growth:".ljust(48) + "│")
            lines.append(f"│   Start: {start_might:,}".ljust(48) + "│")
            lines.append(f"│   End: {end_might:,}".ljust(48) + "│")
            lines.append(f"│   Gain: +{gain:,} ({pct:.1f}%)".ljust(48) + "│")
        else:
            lines.append(f"│ Might: Insufficient data".ljust(48) + "│")

        lines.append("│" + "─" * 48 + "│")

        # Kill trend
        recent_kills = [
            h for h in kill_history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]
        if recent_kills:
            total = sum(h["kills"] for h in recent_kills)
            lines.append(f"│ Kills (7 days): {total:,}".ljust(48) + "│")
            lines.append(f"│ Daily Avg: {total / 7:.1f}".ljust(48) + "│")
        else:
            lines.append(f"│ Kills: No data".ljust(48) + "│")

        # Activity breakdown
        daily = history.get("daily", [])
        if daily:
            last_7 = daily[-7:] if len(daily) > 7 else daily
            total_attacks = sum(d.get("attacks", 0) for d in last_7)
            lines.append(f"│ Attacks (7 days): {total_attacks}".ljust(48) + "│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    def resource_chart(self, width: int = 40) -> str:
        """ASCII bar chart of resources gathered."""
        stats = self.analytics.get_session_stats()
        resources = stats.get("resources_gathered", {})

        if not resources:
            return "┌" + "─" * (width + 2) + "┐\n│ No resource data".ljust(width + 2) + "│\n└" + "─" * (width + 2) + "┘"

        lines = []
        lines.append("┌" + "─" * (width + 2) + "┐")
        lines.append("│" + " 💎 RESOURCES GATHERED ".center(width + 2) + "│")
        lines.append("├" + "─" * (width + 2) + "┤")

        max_val = max(resources.values()) if resources else 1

        resource_icons = {
            "gold": "👑",
            "food": "🌾",
            "wood": "🪵",
            "stone": "🪨",
            "iron": "⛏️",
            "gems": "💎",
        }

        for resource, amount in sorted(resources.items(), key=lambda x: -x[1]):
            icon = resource_icons.get(resource.lower(), "📦")
            bar_len = int((amount / max_val) * width)
            bar = "█" * bar_len
            label = f" {icon} {resource.title()}: {amount:,} "
            lines.append("│" + label.ljust(width + 2) + "│")
            lines.append("│" + bar.ljust(width + 1) + "│")

        lines.append("└" + "─" * (width + 2) + "┘")
        return "\n".join(lines)

    def attack_log(self, limit: int = 10) -> str:
        """Table of recent attacks."""
        attacks = self.analytics.session.get("attacks", [])[-limit:]

        if not attacks:
            return "┌" + "─" * 50 + "┐\n│ No attack data".ljust(50) + "│\n└" + "─" * 50 + "┘"

        lines = []
        lines.append("┌" + "─" * 58 + "┐")
        lines.append("│" + " ⚔️ RECENT ATTACKS ".center(58) + "│")
        lines.append("├" + "─" * 7 + "┬" + "─" * 10 + "┬" + "─" * 10 + "┬" + "─" * 8 + "┬" + "─" * 8 + "┬" + "─" * 8 + "┤")
        lines.append("│" + " # ".center(7) + "│" + " Zone ".center(10) + "│" + " Point ".center(10) + "│" + " Result ".center(8) + "│" + " Kills ".center(8) + "│" + " Lost ".center(8) + "│")
        lines.append("├" + "─" * 7 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 8 + "┼" + "─" * 8 + "┼" + "─" * 8 + "┤")

        for i, attack in enumerate(attacks, 1):
            zone = str(attack.get("zone", "-"))
            point = str(attack.get("point", "-"))
            result = attack.get("result", "-")[:6]
            kills = str(attack.get("kills", 0))
            losses = str(attack.get("losses", 0))

            lines.append("│" + str(i).center(7) + "│" + zone.center(10) + "│" + point.center(10) + "│" + result.center(8) + "│" + kills.center(8) + "│" + losses.center(8) + "│")

        lines.append("└" + "─" * 7 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 8 + "┴" + "─" * 8 + "┴" + "─" * 8 + "┘")
        return "\n".join(lines)

    def might_progress(self, points: int = 20) -> str:
        """Track might changes over time as ASCII chart."""
        history = self.analytics.history
        might_history = history.get("might_history", [])

        if not might_history or len(might_history) < 2:
            return "┌" + "─" * 52 + "┐\n│ No might data available".ljust(52) + "│\n└" + "─" * 52 + "┘"

        # Sample data points
        step = max(1, len(might_history) // points)
        sampled = might_history[::step][:points]

        if not sampled:
            return "┌" + "─" * 52 + "┐\n│ No might data".ljust(52) + "│\n└" + "─" * 52 + "┘"

        mights = [h["might"] for h in sampled]
        min_might = min(mights)
        max_might = max(mights)
        range_might = max_might - min_might if max_might != min_might else 1

        # Normalize heights to 10 rows
        height = 10
        chart = [[" " for _ in range(len(mights))] for _ in range(height)]

        for col, might in enumerate(mights):
            normalized = int(((might - min_might) / range_might) * (height - 1))
            chart[height - 1 - normalized][col] = "█"

        lines = []
        lines.append("┌" + "─" * (len(mights) + 2) + "┐")
        lines.append("│" + f" ⚔️ MIGHT PROGRESSION ({len(might_history)} points) ".center(len(mights) + 2) + "│")
        lines.append("├" + "─" * (len(mights) + 2) + "┤")

        for row in chart:
            lines.append("│ " + "".join(row) + " │")

        lines.append("├" + "─" * (len(mights) + 2) + "┤")
        lines.append(f"│ Min: {min_might:,}  Max: {max_might:,} ".ljust(len(mights) + 2) + "│")
        lines.append("└" + "─" * (len(mights) + 2) + "┘")
        return "\n".join(lines)

    def full_report(self) -> str:
        """Generate a complete formatted report."""
        sections = [
            self.daily_summary(),
            "",
            self.resource_chart(),
            "",
            self.attack_log(),
            "",
            self.might_progress(),
            "",
            self.weekly_trends(),
        ]
        return "\n".join(sections)
