# Battle Simulator System

## DLL Externa
```
D:\BattleSimDll_2021\x64\Release\BattleSimDll.pdb
BattleSimDll.dll
```

## Simulator Classes
```
battlesim namespace:
├── IBattleSimulator / CBattleSimulator
├── ICombatSimulator / CCombatSimulator
└── ITDSimulator / CTDSimulator
```

## Simulation Methods
```
SimulateStage
SimulateBattle
SimulateMagicStage
SimulateArena
SimulateMonster
SimulateActivity
```

## Battle Data
```
sendInitBattle
sendInitBattleSP (for special)
sendInitMagicGateBattle
BattleStatus
BattleResult
Battle_Period0, Battle_Period1
BattleStageAwardList1
```

## DLL Hooks Relacionados
```
DLLBSGetPVEMonsterHP / DLLBSSetPVEMonsterHP
DLLBSGetPVEMonsterDamage
DLLBSGetHeroNowHP / DLLBSSetHeroNowHP
DLLBSGetHeroPosition / DLLBSSetHeroPosition
DLLBSSetHeroOver
```

## Uses
- Calcular daño óptimo
- Testear estrategias
- Validar builds de héroes
- Predecir resultados de batalla
