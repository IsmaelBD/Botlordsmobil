# Analytics & Reporting System

Phase 4 of the Lords Mobile Bot introduces a comprehensive analytics and reporting system.

## Overview

The analytics system tracks all bot activity over time, providing:
- Session statistics (resources gathered, attacks, marches)
- Historical trends (might progression, kill counts)
- Automated periodic snapshots
- Exportable CSV data for external analysis
- Multiple reporting channels

## Data Collected

### Session Data
- **Resources Gathered**: Gold, food, wood, stone, iron by amount
- **Attacks**: Zone, point, result, troops deployed, kills, losses
- **Marches**: Duration, troops used, resources delivered
- **State Transitions**: FSM state changes with timestamps
- **Player Snapshots**: Full game state (gold, food, wood, stone, iron, gems, might, level)

### Historical Data
- **Might History**: Timestamped might values for tracking progression
- **Kill History**: Timestamped kill counts
- **Daily Summaries**: Aggregated daily statistics

## Storage Location

All analytics data is stored locally on your machine:

| OS | Path |
|----|------|
| Linux/macOS | `~/.lordsbot/analytics/` |
| Windows | `%USERPROFILE%\.lordsbot\analytics\` |

This keeps analytics separate from the bot code repository.

### Files
- `{account}_session.json` — Current session data
- `{account}_history.json` — Historical trends
- `reports/report_YYYY-MM-DD.txt` — Daily text reports

## Configuration

Add to `config/settings.json`:

```json
{
  "analytics": {
    "enabled": true,
    "snapshot_interval_seconds": 3600,
    "save_history_days": 30,
    "report_channels": ["local", "discord"]
  }
}
```

### Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable/disable analytics | `true` |
| `snapshot_interval_seconds` | How often to take state snapshots | `3600` (1 hour) |
| `save_history_days` | How long to keep historical data | `30` days |
| `report_channels` | Where to send reports | `["local"]` |

### Report Channels
- `local` — Save text reports to `~/.lordsbot/analytics/reports/`
- `discord` — Send reports via registered Discord webhook
- `webhook` — Send reports to a generic webhook URL

## Usage

### In Code

```python
from utils.analytics import BotAnalytics
from utils.report_generator import ReportGenerator

# Initialize
analytics = BotAnalytics("my_account")
reporter = ReportGenerator(analytics)

# Record events
analytics.record_resource_gather("gold", 1000)
analytics.record_attack(507, 59, "success", troops_deployed=100, kills=50)
analytics.record_march_return(300, 50, {"gold": 500})

# Generate reports
print(reporter.daily_summary())
print(reporter.weekly_trends())
print(reporter.attack_log())
print(reporter.might_progress())
print(reporter.full_report())

# Export to CSV
analytics.export_csv("~/lordsbot_export.csv")
```

### FSM Integration

The FSM engine automatically tracks state transitions and player snapshots:

```python
engine = FSMBotEngine()
engine.start()  # Takes initial snapshot
# ... bot runs ...
engine.stop()   # Takes final snapshot, generates session report
```

Modules can record their activity:

```python
# In gatherer module
engine.record_gather("gold", 1000)
engine.record_march(300, 50, {"gold": 500, "food": 200})

# In attacker module
engine.record_attack(507, 59, "success", troops=100, kills=50, losses=10)
```

### Reporter Bot

The `ReporterBot` runs in background and periodically sends reports:

```python
from modules.reporter.bot import ReporterBot

reporter = ReporterBot()
reporter.enable(interval_seconds=3600)  # Every hour

# Or send a one-time report
reporter.send_daily_report(channel="discord")
reporter.send_custom_report(report_type="weekly")
```

## Export & Analysis

### CSV Export

Export all analytics to CSV for spreadsheet analysis:

```python
analytics.export_csv("~/lordsbot_analytics.csv")
```

CSV columns:
- `category`: resource, attack, march, snapshot
- `timestamp`: ISO format datetime
- `type`: Specific type (gold, food, attack, might, etc.)
- `value`: Numeric value
- `details`: Additional info as key=value pairs

### Manual Analysis

```bash
# View session report
cat ~/.lordsbot/analytics/default_session.json | python -m json.tool

# View history
cat ~/.lordsbot/analytics/default_history.json | python -m json.tool

# List reports
ls -la ~/.lordsbot/analytics/reports/
```

## Privacy

All analytics data is **100% local**. No data is ever sent to external servers unless you explicitly configure a webhook or Discord channel.

- Data stored in `~/.lordsbot/` (not in the bot repo)
- No telemetry or phone-home
- Export and delete your data anytime
- No personal information is collected (only in-game stats)

## Report Formats

### Daily Summary
```
┌────────────────────────────────────────────────┐
│              📊 DAILY SUMMARY                  │
├────────────────────────────────────────────────┤
│ Session Runtime: 2h 34m                        │
│ Resources Gathered: 15,230                     │
│   • Food: 10,000                               │
│   • Gold: 5,230                                │
│ Attacks: 12 (K:450 L:25)                       │
│ Current Might: 125,430                         │
└────────────────────────────────────────────────┘
```

### Resource Chart
```
┌────────────────────────────────────────────────┐
│            💎 RESOURCES GATHERED               │
├────────────────────────────────────────────────┤
│  👑 Gold: 15,230         ██████████████████  │
│  🌾 Food: 45,000          ██████████████████████│
│  🪨 Stone: 8,500          ████████             │
```

### Attack Log
```
┌──────────────────────────────────────────────────────────┐
│                     ⚔️ RECENT ATTACKS                    │
├───────┬────────────┬────────────┬──────────┬─────────────┤
│   #   │    Zone    │    Point   │  Result  │   Kills     │
├───────┼────────────┼────────────┼──────────┼─────────────┤
│   1   │    507     │     59     │  success │     50      │
│   2   │    507     │     60     │  success │     45      │
```

### Might Progress Chart
```
┌──────────────────────────────────────┐
│       ⚔️ MIGHT PROGRESSION (50 pts)  │
├──────────────────────────────────────┤
│                    █                │
│                  █ █                │
│               █  █ █                │
│            █  █  █ █                │
│         █  █  █  █ █                │
├──────────────────────────────────────┤
│  Min: 100,000  Max: 125,430         │
└──────────────────────────────────────┘
```

## Troubleshooting

### No data appearing
- Check `config/settings.json` has `"analytics": {"enabled": true}`
- Verify write permissions to `~/.lordsbot/`
- Check logs for analytics errors

### Reports not sending to Discord
- Ensure `discord-chat` skill is configured
- Check webhook URL is valid
- Verify bot has permission to send to channel

### CSV export empty
- Run the bot for a session first
- Check session data exists: `cat ~/.lordsbot/analytics/default_session.json`
