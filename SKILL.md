---
name: lords-mobile-bot
description: Lords Mobile game bot with memory editing, packet injection, Frida hooks, and Win32 automation. Use when working with Lords Mobile bot development, automation, or game hacking. Supports resource gathering, attack coordination, gift code redemption, map exploration, and real-time game state monitoring.
---

# Lords Mobile Bot — Refactored Edition v2.0

## Architecture

```
lords-mobile-bot/
├── config/                  # Centralized configuration
│   ├── offsets.json         # Game RVAs, pointers, protocol IDs
│   ├── settings.json         # General settings, timing, anti-ban
│   ├── targets.json          # Attack/gather target lists
│   ├── accounts.json         # Multi-account profiles
│   ├── game_analysis.md      # Frida-derived game internals
│   └── dll_analysis.md       # Deep DLL analysis (966 handlers)
├── core/                    # Low-level system interfaces
│   ├── memory/radar.py       # Memory Radar (read/write process memory)
│   ├── network/sniffer.py    # Packet capture + injection
│   ├── frida/bridge.py      # Frida script bridge
│   └── win32/hands.py        # Win32 ghost client (mouse/keyboard)
├── modules/                 # Game automation modules
│   ├── gatherer/             # Resource gathering (Win32 macro)
│   ├── attacker/            # Combat/march injection (shellcode)
│   ├── redeemer/            # Gift code redemption (TCP socket)
│   └── explorer/            # Map exploration/scanning
├── brain/                   # Decision making
│   └── fsm/engine.py        # Finite State Machine (autonomous mode)
├── ui/
│   ├── desktop/             # PyQt5 Desktop Application (Phase 1)
│   │   ├── main_window.py   # Main window (7 tabs + dashboard)
│   │   ├── run_desktop.py   # Launcher
│   │   └── requirements.txt
│   └── web/                # Flask web dashboard
│       ├── app.py
│       └── templates/dashboard.html
├── scripts/                # Utility scripts
├── DummyDll/              # Decompiled game DLLs (reference)
├── legacy/               # Archived original scripts (v1)
└── main.py              # CLI entry point
```

## Quick Start

### Desktop UI (recommended)
```bash
pip install PyQt5
cd ui/desktop
python run_desktop.py
```

### CLI mode
```bash
pip install -r requirements.txt
python main.py --mode cli
```

## UI Features (Phase 1)

- 🎨 **Professional dark theme** — matches paid bot aesthetics
- 👥 **Multi-account management** — add/edit/remove profiles
- 🚜 **Gatherer panel** — target coordinates, march wait, loop control
- ⚔️ **Attacker panel** — zone/point targeting, rally mode, cooldown
- 🎁 **Redeemer panel** — single + batch gift code redemption
- 🗺️ **Explorer panel** — grid-based map scanning
- 🤖 **FSM Engine** — fully autonomous decision loop
- ⚙️ **Settings window** — General, Anti-Ban, Network tabs
- 📊 **Real-time logs** — per-module activity logging

## Core Principles

1. **Offsets in JSON, never hardcoded** — update `config/offsets.json`
2. **One class per module** — gatherer, attacker, redeemer, explorer
3. **Frida scripts versioned** — `core/frida/scripts/`
4. **Non-blocking UI** — BotWorker threads, no freezes
5. **Multi-account ready** — profile-based account switching
