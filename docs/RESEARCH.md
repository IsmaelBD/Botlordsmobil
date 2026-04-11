# Lords Mobile Bot — Research Notes

> Compiled: 2026-04-10

## Packet Protocol

### Project's Existing Knowledge
The bot already has detailed packet protocol documentation in `config/game_analysis.md`:

- **Protocol 6615** (0x19D7) — March packet format
- **Message Packet Offsets**: `+0x18` (currentPos), `+0x20` (bufferObject), `+0x28` (dataObject), `+0x30` (protocol)
- **Key RVAs**:
  - `fnGetMP` → `0x1D22900` — Get empty MessagePacket from pool
  - `fnAddSeq` → `0x1D22110` — Add sequence ID to packet
  - `fnAddUS` → `0x1D224A0` — Add ushort prefix
  - `fnNetSend` → `0x1D28C40` — Send packet to server

### March Packet Structure
```
[Header: 10 bytes][Content: 101 bytes]
Total: 111 bytes

Content layout:
- Offset 0x48 (72): Zone ID (2 bytes)
- Offset 0x4A (74): Point ID (1 byte)
```

### Public Protocol Documentation
- No official protocol documentation exists publicly
- Lords Mobile uses a custom binary protocol over TCP (server: `205.252.125.129:11977`)
- GitHub has scattered bot projects (mostly outdated C# bots)
- Game uses Unity/Mono runtime — packets are constructed in `Assembly-CSharp.dll`

### Frida Scripts Available
```
core/frida/scripts/
├── _shared
├── geotrack.js          # Memory tracking
├── heartbeat_capture.js # Network capture
├── inject_march.js      # Packet injection
├── master_bypass.js     # Anti-detection bypass
└── packet_sniff.js      # Packet sniffing
```

---

## Library Updates

### Frida (Python Bindings)
- **Latest stable**: `frida-17.9.1` (released March 27, 2026)
- **Project requirement**: `frida>=16.0.0` ✅ Compatible
- **Release history**: Frida 17.x series is current; 16.x is still supported
- **frida-python**: Available via `pip install frida`
- **Note**: Project uses Frida for memory reading and offset scanning

### PyQt5
- **Latest version**: `PyQt5-5.15.x` (current as of 2026)
- **Project requirement**: `PyQt5>=5.15.10` ✅ Compatible
- **License**: GPL v3 or commercial (Riverbank Computing)
- **Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **Note**: Used for the desktop UI (`ui/desktop/`)

### Other Dependencies (all satisfied)
| Library | Project Requirement | Status |
|---------|---------------------|--------|
| python-devtools | >=0.9.0 | Compatible |
| pyautogui | >=0.9.54 | Compatible |
| pyshark | (packet capture) | Compatible |
| scapy | >=2.5.0 | Compatible |
| flask | >=3.0.0 | Compatible |
| pydantic | >=2.0 | Compatible |

### Cheat Engine
- **Latest public**: Cheat Engine 7.6 (February 12, 2025)
- **Note**: Referenced for memory analysis workflow; not a direct dependency

---

## Anti-Ban Research

### Project's Existing Anti-Detection (Phase 3)
The bot already has a comprehensive anti-detection system documented in `docs/ANTI_DETECTION.md`:

| Component | File | Purpose |
|-----------|------|---------|
| `AntiDetection` | `core/anti_detection/timing.py` | Randomized timing |
| `HumanClicker` | `core/anti_detection/human_clicks.py` | Bezier-curved mouse movement |
| `SessionGuard` | `core/anti_detection/session_guard.py` | Rate limiting via sliding window |
| `OffsetUpdater` | `core/anti_detection/offset_updater.py` | Auto-recovers from game updates |

### Anti-Detection Techniques Already Implemented
1. **Timing randomization** — Human-like delays instead of fixed intervals
2. **Bezier mouse curves** — Non-linear mouse movement
3. **Coordinate jitter** — ±2px click offset
4. **Press duration jitter** — Variable mouse button hold time
5. **Sliding window rate limiter** — Tracks actions in 60s rolling window
6. **Consecutive cycle limits** — Forces cooldown after N cycles
7. **Frida-based offset recovery** — Auto-updates memory offsets after game patches

### Known Anti-Detection Limitations
1. Python's `random` is not cryptographically secure — patterns could emerge
2. Frida itself is detectable by anti-cheat — use `master_bypass.js` patterns
3. Hardware fingerprinting — Bezier curves are algorithmic, not human
4. `SessionGuard` is memory-only — state resets on restart

### How Game Clients Detect Automation
Common detection vectors:
- **Timing patterns** — Fixed intervals between actions
- **Mouse movement** — Perfectly linear or instantaneous moves
- **Input frequency** — Too many actions per minute
- **Memory scanning** — Frida/modified memory access
- **Checksum mismatches** — Modified game files

### Lords Mobile ToS (via IGG)
- Lords Mobile is developed by IGG (I Got Games)
- IGG actively detects and bans botters
- Bot detection is not publicly documented
- Using bots risks account termination
- **No public documentation** of specific detection methods found

---

## Useful Links

### Frida
- **Homepage**: https://frida.re/
- **Releases**: https://github.com/frida/frida/releases
- **Python bindings**: https://pypi.org/project/frida/
- **JavaScript API**: https://frida.re/docs/javascript-api/

### PyQt5
- **PyPI**: https://pypi.org/project/PyQt5/
- **Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt5/

### Lords Mobile Bot Communities
- Various GitHub repos exist (search: "Lords Mobile bot")
- Most are outdated or abandoned
- No active public protocol documentation

### Game Hacking Resources
- **Cheat Engine**: https://cheatengine.org/
- **Frida**: Dynamic instrumentation toolkit

### Project Files
- `config/offsets.json` — Memory offset configuration
- `config/game_analysis.md` — Frida-derived game internals
- `config/dll_analysis.md` — Deep DLL analysis (966 handlers)
- `core/frida/scripts/` — Frida instrumentation scripts
- `docs/ANTI_DETECTION.md` — Anti-detection system docs
- `docs/ANALYTICS.md` — Analytics and reporting docs
