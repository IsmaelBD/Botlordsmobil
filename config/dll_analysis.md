# Lords Mobile — Assembly-CSharp.dll Deep Analysis

> Generated from `DummyDll/Assembly-CSharp.dll` (decompiled .NET Mono DLL)
> 966 unique `Recv*` handlers | 200+ `MSG_*` message types | 500+ `eGS_*` UI elements

---

## 📡 Network Protocol Reference

### Known Protocol IDs

| ID | Name | Description |
|----|------|-------------|
| 13000 | Version | Client version handshake |
| 1024 | Hardware | Hardware activation |
| 1043 | Login | Session login |
| 1420 | Gift Redeem | Gift code redemption |
| 6615 | Troop March | Troop march dispatch |
| 6615 | Heartbeat | Session keep-alive (small packets) |

### Key MSG_* Request/Response Types (88 documented)

```
MSG_REQUEST_ALLIANCE_MODIFY_RECRUIT_SETTINGS
MSG_RESP_ALLIANCE_MODIFY_RECRUIT_SETTINGS
MSG_RESP_GIFT_ACTIVITY_UNLOCK_RANDOM_GIFT_BOX_ErrorCode
MSG_TYPE
```

### Key Recv_* Handler Categories

#### 🗡️ Combat & Troops (40+ handlers)
```
RecvCombatDetail_Injuredata
RecvCombatDetail_Leaderdata
RecvCombatDetail_Playerdata
RecvCombatDetail_T5TIERDATA
RecvCombatPet / RecvCombatPet2 / RecvCombatPet3
RecvFillTroop
RecvGoCombatTower[1-8]
RecvGoTerritorySendTroop[1-3]
RecvGoTroopMemory[1-4]
RecvHideTroopInshelter
RecvJoinRally
RecvJoinedRallyData
RecvMapMonsterAttack
RecvMarchData / RecvMarchDataEX / RecvMarchDataNewTier
RecvMarchEventDataType
RecvMarchEventTime
RecvMarchRallyWonderData
RecvPetMarchEnd / RecvPetMarchEventData
RecvRallyAtkMarch / RecvRallyAtkNow
RecvArrivedRallyPoint / RecvBeginRally / RecvCancelRally
```

#### 🎁 Gift System (20+ handlers)
```
Recv_MSG_RESP_GIFT_CHANNEL_DATA
Recv_MSG_RESP_GIFT_ACTIVITY_SEND_RECORD
Recv_MSG_RESP_GIFT_ACTIVITY_ACCEPT_RECORD
Recv_MSG_RESP_GIFT_ACTIVITY_GIFT_BOX_INFO
Recv_MSG_RESP_GIFT_ACTIVITY_LIST
Recv_MSG_RESP_GIFT_ACTIVITY_OPEN_GIFT_BOX
Recv_MSG_RESP_GIFT_ACTIVITY_UNLOCK_RANDOM_GIFT_BOX
Recv_MSG_RESP_SERIALGIFT_GIFTINFO
Recv_MSG_RESP_SERIALGIFT_EVENTLIST
Recv_MSG_RESP_SERIALGIFT_GETGIFT
Recv_MSG_RESP_KING_GIFT_INFO / _ADDITEM / _RECIVED / _SYN / _CHECK
Recv_MSG_RESP_EMPEROR_GIFT_*
RecvAllianceGift_CheckExpired / _Delete / _Info / _Open / _OpenAllBox
Recv_GIFT_ACTIVITY
bRecvSerialGiftData / bRecvCustomGiftData
eGS_GetRedeem
```

#### 🏰 Alliance & Rally
```
RecvAllianceCreate / RecvAllianceQuit / RecvAllianceDismissLeader
RecvAllianceMember / RecvAlliancePublicInfo / RecvAllianceAttr
RecvAllianceGatherPointSet / RecvAllianceGatherPointFreeTeleport
RecvAllianceWarMemberList / RecvAllianceWonder_Info
RecvAllyAmbushInfo / RecvAllyInforceInfo / RecvAllyPoint
RecvBeginRally / RecvCancelRally / RecvJoinRally / RecvJoinedRallyData
```

#### 📦 Resources
```
RecvResources / RecvResourcesUpdate / RecvRefreshResources
RecvGoldGuy[1-4] / RecvGoWakeUpGoldGuy[1-2]
RecvSmartUseResource
```

#### 📊 Game State
```
RecvAllInfo / RecvAllBuildData
RecvActivityInfo / RecvActivity_* (40+ variants)
RecvChapterCutsceneManager
```

---

## 🏗️ Game Architecture (Class Managers)

Discovered `*Manager` classes in the DLL:

| Manager | Purpose |
|---------|---------|
| `ActivityGiftManager` | Gift box events |
| `ActivityStageManager` | Event stages |
| `AllianceGatherPointManager` | Alliance rally points |
| `AllianceWarManager` | Alliance war |
| `ArmyArenaConfigureManager` | Arena configuration |
| `AttribValManager` | Attribute values |
| `BattlePassManager` | Battle pass |
| `BattlePassRewardManager` | Battle pass rewards |
| `BoxPreviewManager` | Loot box preview |
| `BuildPromptManager` | Building prompts |
| `DragonWarZoneCupManager` | Dragon war |
| `EventCollectionManager` | Event collection |
| `ExpExchangeManager` | Experience exchange |
| `FantasyRealmManager` | Fantasy realm |
| `FirebaseEventManager` | Analytics |
| `GlobalProjectorManager` | Projections |
| `GuardianVerificationManager` | Account verification |
| `HeroDisplayManager` | Hero display |

---

## 🎮 Game State Offsets (from Frida analysis)

### RoleAttr (Player Attributes)
Located via: `dm_typeinfo + 0x58F5368 → type_info → static_fields + 0xB8 → instance + 0x18 → role_attr`

| Offset | Field | Type |
|--------|-------|------|
| `+0x32` | Level | byte |
| `+0x80` | TutorialStep | uint32 |
| `+0x98` | Diamond | uint32 |

### MessagePacket Structure
| Offset | Field |
|--------|-------|
| `+0x18` | currentPos |
| `+0x28` | buffer object |
| `+0x30` | protocol (uint16) |

---

## 🔧 Frida Script API

All migrated scripts in `core/frida/scripts/`:

### inject_march.js
```javascript
// Direct call:
rpc.exports.injectMarch(zone, point, contentHex);

// Example:
rpc.exports.injectMarch(507, 59, null);  // Forest
```

### geotrack.js
```javascript
rpc.exports.rescan();                    // Scan all signatures
rpc.exports.rescan("Forest (507,59)");   // Scan specific
```

### packet_sniff.js
```javascript
rpc.exports.getLog(100);                 // Last 100 packets
rpc.exports.getByProtocol(6615);         // Filter by protocol
rpc.exports.getCount();                   // Total count
rpc.exports.clearLog();                   // Clear buffer
```

### heartbeat_capture.js
```javascript
rpc.exports.getCandidates();              // All heartbeat candidates
rpc.exports.getLastInterval();            // ms between last two
rpc.exports.clear();                      // Clear buffer
```

---

## 🗺️ Coordinate System

- **Zone ID**: uint16, encoded little-endian (e.g., 507 = `0x01FB`)
- **Point ID**: uint8 (e.g., 59 = `0x3B`)
- In march content: Zone at offset 72, Point at offset 74

### Known Points
| Name | Zone | Point |
|------|------|-------|
| Forest (default farm) | 507 | 59 |

---

## 🔐 Anti-Cheat Notes

- Frida detection strings exist (`frida-server`, `linjector`, `gum-js-loop`)
- `master_bypass.js` patches string detection
- Game uses IL2CPP (not pure .NET) — `DummyDll/Il2CppDummyDll.dll` is a stub
- Offsets change with game updates — verify before each session
- Sequence IDs must be synchronized via `AddSeq + AddUS` before sending

---

## 📁 DLL Contents Summary

```
DummyDll/
├── Assembly-CSharp.dll          # Main game logic (966 Recv handlers)
├── Assembly-CSharp-firstpass.dll # Precompiled assemblies
├── UnityEngine*.dll            # 40+ Unity engine modules
├── Il2CppDummyDll.dll          # IL2CPP metadata stub
├── Newtonsoft.Json.dll         # JSON serialization
├── spine-*.dll                  # Spine animation
├── ZFBrowser.dll                # HTML/MHTML browser (ads?)
└── mscorlib.dll                 # .NET core library
```
