---
name: lords-mobile-bot
description: Lords Mobile game bot with memory editing, packet injection, Frida hooks, and Win32 automation. Use when working with Lords Mobile bot development, automation, or game hacking. Supports resource gathering, attack coordination, gift code redemption, map exploration, and real-time game state monitoring.
---

# Lords Mobile Bot — Refactored Edition

## Architecture

```
lords-mobile-bot/
├── config/             # Centralized configuration (offsets, settings, credentials)
├── core/               # Low-level system interfaces
│   ├── memory/         # Memory radar (read/write process memory)
│   ├── network/        # Packet capture and injection
│   ├── frida/          # Frida script bridge
│   └── win32/          # Win32 UI automation (mouse, keyboard)
├── modules/            # Game modules (one per feature)
│   ├── gatherer/       # Resource gathering automation
│   ├── attacker/       # Combat/troop march system
│   ├── redeemer/       # Gift code redemption
│   └── explorer/       # Map exploration/scanning
├── brain/              # Decision making
│   ├── fsm/            # Finite State Machine engine
│   └── decisions/      # AI decision logic
├── ui/                 # User interfaces
│   └── web/            # Flask web dashboard
├── utils/              # Shared utilities
└── main.py             # Entry point
```

## Core Principles

1. **One class per file, one responsibility per module**
2. **Offsets stored in JSON, never hardcoded in logic**
3. **Frida scripts are versioned and loaded dynamically**
4. **All network traffic goes through core/network/sniffer.py**
5. **Win32 automation is isolated in core/win32/hands.py**
