# Lords Mobile — Game Analysis

## DLL Structure (from `DummyDll/`)

- **Assembly-CSharp.dll** — Main game logic (.NET Mono DLL)
- **Assembly-CSharp-firstpass.dll** — Precompiled firstpass assemblies
- **UnityEngine*.dll** — Unity engine modules
- **Il2CppDummyDll.dll** — IL2CPP metadata stub

## Key RVAs (from Frida scripts + memory analysis)

| Function | RVA | Purpose |
|----------|-----|---------|
| `fnGetMP` | `0x1D22900` | Get empty MessagePacket from pool |
| `fnAddSeq` | `0x1D22110` | Add sequence ID to packet |
| `fnAddUS` | `0x1D224A0` | Add ushort prefix (for protocol 6615) |
| `fnNetSend` | `0x1D28C40` | Send packet to server |

## March Packet Format

Protocol: **6615** (`0x19D7`)

### Structure

```
[Header: 10 bytes][Content: 101 bytes]
Total: 111 bytes
```

### Content layout

| Offset | Size | Field | Example |
|--------|------|-------|---------|
| 0x48 (72) | 2 bytes | Zone ID | `fb 01` = 507 |
| 0x4A (74) | 1 byte | Point ID | `3b` = 59 |

### Template hex (without header)

```
09000000000000002c0100000000000000000000000000006400000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000
```

## Message Packet Offsets (from Frida)

| Offset | Field | Description |
|--------|-------|-------------|
| `+0x18` | `currentPos` | Current write position |
| `+0x20` | `bufferObject` | Buffer object |
| `+0x28` | `dataObject` | Data object |
| `+0x30` | `protocol` | Protocol ID (6615) |
| `+0x20` (inside dataObject) | `rawStart` | Raw data start |

## Known Packet Types

| Protocol | ID | Description |
|----------|----|-------------|
| Version | 13000 | Client version handshake |
| Hardware | 1024 | Hardware activation |
| Login | 1043 | Session login |
| Gift Redeem | 1420 | Gift code redemption |
| Troop March | 6615 | Troop march dispatch |

## Known Message Types

```
_MSG_REQUEST_TROOPMARCH
_MSG_REQUEST_TROOPMARCH_NOTATK
_MSG_RESP_TROOPMARCH
RecvTroopMarch
ETroopMarchTimeLimit
```

## Gift System Messages

```
Recv_MSG_RESP_GIFT_CHANNEL_DATA
_MSG_RESP_ALLIANCE_GIFT_CHECKEXPIRED
_MSG_REQUEST_ALLIANCE_GIFT_CHECKEXPIRED
_MSG_RESP_KING_GIFT_RECIVED
_MSG_GIFT_RECIVED
_MSG_RESP_SERIALGIFT_GIFTINFO
_MSG_REQUEST_SERIALGIFT_GIFTINFO
```

## Game State Classes

```
RoleAttr — Player attributes (level, diamond, exp, etc.)
GameData / userData — Global game state
PointCode — Map coordinate encoding
mZoneID / D_ZoneID / freeZoneID — Zone tracking
```

## Coordinate System

- Zone IDs: integer (e.g., 507)
- Point IDs: byte (e.g., 59 = 0x3b)
- Encoded as little-endian: `fb 01` for zone 507
- The game uses `PointCode` encoding for map positions

## String Signatures Found

```
KILLED_ENEMYTROOPS1000 / TRAIN_TROOPS2000
eGS_GetRedeem
ELCF_Redeemed
ProtocolVictory / ProtocolFailed
```

## Anti-Cheat Notes

- Game uses Frida detection (bypass scripts exist)
- Memory offsets change with game updates
- Server-side validation on march packets
- Sequence IDs must be synchronized with server
