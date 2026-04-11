# Anti-Detection System — Phase 3

> Nothing is 100% safe. But a bot that looks like a human is harder to catch.

This document describes the anti-detection system integrated into the Lords Mobile bot.

---

## Overview

The Phase 3 Anti-Detection System introduces four core components that work together to make the bot's behavior indistinguishable from a real human user:

| Component | File | Purpose |
|---|---|---|
| `AntiDetection` | `core/anti_detection/timing.py` | Randomized timing for delays and cycles |
| `HumanClicker` | `core/anti_detection/human_clicks.py` | Bezier-curved mouse movement, natural clicks |
| `SessionGuard` | `core/anti_detection/session_guard.py` | Rate limiting via sliding window |
| `OffsetUpdater` | `core/anti_detection/offset_updater.py` | Auto-recovers from game updates |

---

## 1. AntiDetection — Randomized Timing

**File:** `core/anti_detection/timing.py`

### What it does

Generates human-like random delays instead of using fixed timing values.

### Methods

- **`random_action_delay()`** → float (ms)
  Returns a random delay between `min_action_delay_ms` and `max_action_delay_ms` for mouse clicks and other discrete actions.

- **`random_cycle_delay()`** → float (seconds)
  Returns a random delay between `min_cycle_delay` and `max_cycle_delay` for longer pauses between automation cycles.

- **`jitter(base_ms, variance_pct)`** → float (ms)
  Adds variance around a base timing. `variance_pct=0.2` means ±20% randomization.

- **`human_delay(min_ms, max_ms)`** → float (ms)
  Generic human-like pause between any two actions.

### Tuning Parameters

All values are configurable in `config/settings.json`:

```json
{
  "anti_detection": {
    "min_action_delay_ms": 50,
    "max_action_delay_ms": 500,
    "min_cycle_delay": 180,
    "max_cycle_delay": 600,
    "min_jitter_ms": 10,
    "max_jitter_ms": 50
  }
}
```

- **Low values** → faster, more aggressive, higher detection risk
- **High values** → slower, safer, less productive

**Recommended starting values:**
- Casual use: `min/max_action_delay_ms: 50-500`, `min/max_cycle_delay: 180-600`
- Aggressive: `min/max_action_delay_ms: 20-200`, `min/max_cycle_delay: 60-180`
- Ultra-safe: `min/max_action_delay_ms: 100-1000`, `min/max_cycle_delay: 300-900`

---

## 2. HumanClicker — Human-like Click Patterns

**File:** `core/anti_detection/human_clicks.py`

### What it does

Makes mouse movements feel human instead of robotic:

1. **Bezier curves** — Mouse doesn't move in a straight line. It curves naturally using cubic Bezier interpolation with randomized control points.
2. **Coordinate jitter** — Click coordinates are offset by ±2px randomly.
3. **Press duration jitter** — Mouse button hold time varies by ±10ms.
4. **Pre/post click pauses** — Small human-like pauses before and after clicks.

### Methods

- **`human_move(x1, y1, x2, y2, duration_ms)`**
  Moves mouse from (x1, y1) to (x2, y2) along a Bezier path. `duration_ms` controls how long the movement takes (default 200ms).

- **`human_click(x, y, delay_ms)`**
  Clicks at (x, y) with full humanization. Adds coordinate offset, press duration jitter, and timing randomness.

- **`random_scroll(direction, amount)`**
  Scrolls with randomized wheel delta and pauses.

### Tuning Parameters

| Parameter | Default | Description |
|---|---|---|
| `coord_offset_max` | 2 | ±px for click coordinate jitter |
| `press_duration_jitter` | 10 | ±ms for mouse press duration |
| `pre_click_delay_ms` | 5 | ms pause before click |
| `post_click_delay_ms` | 8 | ms pause after click |

---

## 3. SessionGuard — Session Rotation & Cooldown

**File:** `core/anti_detection/session_guard.py`

### What it does

Prevents detection through **behavioral rate limiting**:

1. **Sliding window rate limiter** — Tracks timestamps of all actions in a 60-second rolling window. If too many actions occur in that window, further actions are blocked.
2. **Consecutive cycle limit** — After `max_consecutive_cycles` actions, forces a cooldown break.
3. **Random pause** — Cooldown uses a random duration within a configured range, not a fixed value.

### Why Sliding Window?

A simple counter ("only 10 actions per minute") fails because it doesn't account for *when* those actions happened. A sliding window tracks exact timestamps:

```
[action @ 0s] [action @ 5s] [action @ 10s]  ← after 60s these are forgotten
         [action @ 55s] [action @ 58s] [action @ 59s]  ← still within window
```

This is much harder to detect than a simple counter.

### Methods

- **`should_act(action_type)`** → bool
  Returns `True` if the rate limiter hasn't been exceeded for the given action type.

- **`record_action(action_type)`**
  Logs an action with its timestamp. Triggers cooldown if consecutive cycle limit is reached.

- **`enforced_cooldown()`** → bool
  Returns `True` if the bot should remain in cooldown state.

- **`random_pause()`** → float (seconds)
  Takes a random break and resets the cycle counter.

### Tuning Parameters

```json
{
  "anti_detection": {
    "max_actions_per_minute": 10,
    "max_consecutive_cycles": 5,
    "cooldown_after_max": 300,
    "min_pause_seconds": 30,
    "max_pause_seconds": 120
  }
}
```

- **`max_actions_per_minute`**: Actions allowed in any 60-second window
- **`max_consecutive_cycles`**: Cycles before forced cooldown
- **`cooldown_after_max`**: Minimum cooldown duration in seconds
- **`min/max_pause_seconds`**: Range for random pause duration during cooldown

---

## 4. OffsetUpdater — Auto Offset Recovery

**File:** `core/anti_detection/offset_updater.py`

### What it does

Game updates change memory offsets in `GameAssembly.dll`. When offsets break, this component:

1. **Checks validity** — Reads memory at expected offset addresses to verify they still work
2. **Scans for new offsets** — Uses Frida to scan game memory for the same signatures
3. **Backs up first** — Saves the old `offsets.json` before overwriting
4. **Flags for manual review** — If auto-scan fails, marks offsets as needing human attention

### Methods

- **`check_offsets_valid(radar)`** → bool
  Reads 4 bytes at each known offset address. Returns `False` if any read fails.

- **`scan_for_offsets(radar)`** → dict
  Attaches Frida to the game process and runs `geotrack.js` pattern scanning.

- **`auto_update(radar)`** → bool
  Full workflow: check → backup → scan → update. Returns `True` if updated.

### Backup Restoration

Backups are stored in `config/offsets_backups/offsets_YYYYMMDD_HHMMSS.json`.

```python
from core.anti_detection import OffsetUpdater
updater = OffsetUpdater()
updater.restore_backup("latest")  # Restore most recent backup
```

---

## Integration Points

### Win32GhostClient (`core/win32/hands.py`)

- **`vClick(x, y, delay_ms)`** — Full anti-detection (Bezier move + humanized click)
- **`vClickFast(x, y, delay_ms)`** — Fast raw click (no anti-detection). Use for low-risk UI.

### Module Integration

Each bot module uses `AntiDetection` and `SessionGuard`:

- **GathererBot** — Replaced all `time.sleep(X)` with randomized delays via `anti_detection.human_delay()` and `anti_detection.random_cycle_delay()`
- **AttackerBot** — Same pattern; rate limits attack actions
- **RedeemerBot** — Randomized delays between TCP steps and batch codes
- **ExplorerBot** — Rate-limited map scanning
- **FSM Engine** — Randomized polling interval instead of fixed `polling_interval`

---

## Known Limitations

> **Nothing is 100% safe.** These components reduce detection risk but don't eliminate it.

1. **Pattern over time** — Even random delays can form patterns if the random seed is predictable. The system uses Python's `random` module which is not cryptographically secure.

2. **Frida detection** — The `OffsetUpdater` uses Frida, which is itself detectable by anti-cheat. Use `master_bypass.js` patterns to reduce this risk.

3. **Hardware fingerprinting** — Mouse movement curves are algorithmic. A sophisticated anti-cheat could potentially distinguish Bezier-generated curves from real human curves. To reduce this:
   - Vary the curve magnitude significantly
   - Don't always use Bezier — sometimes move in a slightly jagged path

4. **SessionGuard is memory-only** — State is not persisted. Restarting the bot resets all counters. For long-running unmonitored bots, consider persisting action logs to disk.

5. **Offset auto-update may fail** — If the game's memory layout changes significantly, Frida scanning may not find the new offsets. In that case, manual `offsets.json` update is required.

---

## Testing Anti-Detection

```python
# Quick smoke test
from core.anti_detection import AntiDetection, HumanClicker, SessionGuard

ad = AntiDetection()
print(f"Action delay: {ad.random_action_delay():.2f}ms")
print(f"Cycle delay: {ad.random_cycle_delay():.2f}s")
print(f"Jitter(500ms, 20%): {ad.jitter(500, 0.2):.2f}ms")

sg = SessionGuard()
print(f"should_act: {sg.should_act('test')}")  # True
sg.record_action("test")
print(f"should_act after record: {sg.should_act('test')}")  # False after 10 records
```

---

## Configuration Checklist

Before running the bot in production:

- [ ] Set `anti_detection.enabled: true`
- [ ] Tune `min/max_action_delay_ms` for your risk tolerance
- [ ] Tune `max_actions_per_minute` (10 is conservative, 20+ is aggressive)
- [ ] Ensure `config/offsets_backups/` is writable
- [ ] Test `OffsetUpdater.auto_update()` works with your game version
- [ ] Consider `SessionGuard` persistence if running unattended for days
