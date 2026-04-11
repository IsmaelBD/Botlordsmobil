# Game Events & Activities

## Event Data
```
DLLBSGetEventDataLen
DLLTDGetEventDataLen
ActivityStage.bytes
```

## Event Types (from namespaces)
```
LordsMobileBot.Game.Activity
LordsMobileBot.Game.Magic
LordsMobileBot.Game.Magic.Enum
LordsMobileBot.Game.FantasyRealm
```

## PVP System
```
LordsMobileBot.Game.PVP
LordsMobileBot.Game.PVP.PVPAssignmentMgr
├── SendReward
├── Send_MSG_REQUEST_PVP_BATTLEFIELD_LIST
├── Send_MSG_REQUEST_PVP_BATTLEFIELD_LEAVE
├── TryEnterPVP
└── Send_MSG_REQUEST_PVP_BATTLEFIELD_ENTER
PVPBattleFieldUtility
├── GetLightSignalsText
```

## Arena System
```
LordsMobileBot.Game.Arena
ArenaManager
├── SendArena_Refresh_Target
├── findHeroArenaFightDataCustom
└── SimulateBattle
DLLBSSetArenaTopic
```

## Mission System
```
LordsMobileBot.Game.Mission
MissionManager
├── sendMissionComplete
├── RecvTimeMissionReward
├── RecvTimeMissionReward_OnePass
└── RecvMissionComplete
```

## VIP System
```
DllCSCalculateVIPBonus
DllSetVIPExtTable
```
