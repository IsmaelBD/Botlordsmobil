# Lords Mobile Bot - Análisis Técnico Completo

## 📦 Estructura del Paquete

```
bot.zip
├── Lords Monitor.exe          (700 KB) - Launcher/UI
├── LordsMobileBot.exe         (222 MB) - Core Bot
├── LordsMobileBot.dll.config  - Configuración
├── Updater.exe               (660 KB) - Auto-update
├── MSVCP120.dll / MSVCR120.dll - Runtime C++
└── GameAssets/               - Assets del juego (539 archivos .txt)
    ├── HeroStats, Items, Skills
    ├── Map data, Quest data
    └── huntData.json         - Guías de Hunt
```

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────┐
│         Lords Monitor.exe (Launcher)                │
│         - DevExpress WPF + .NET 6+                  │
│         - NamedPipe Server (comunicación IPC)       │
│         - Configuración de inicio                   │
└────────────────────┬────────────────────────────────┘
                     │ Pipe: "LordsMobileBot"
                     ▼
┌─────────────────────────────────────────────────────┐
│         LordsMobileBot.exe (Core)                   │
│         - WinForms + DevExpress                     │
│         - Account Manager (múltiples cuentas)      │
│         - DLL Injection hooks                       │
│         - Discord/Telegram bots integrados           │
└────────────────────┬────────────────────────────────┘
                     │ DLL Hooks
                     ▼
┌─────────────────────────────────────────────────────┐
│         Memoria del Juego (LordsMobile.exe)          │
│         - Lectura/Escritura de RAM                  │
│         - Modificación de stats, posición, etc.    │
└─────────────────────────────────────────────────────┘
```

## 🔧 Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Launcher UI | C# / .NET 6+, DevExpress WPF |
| Core Bot | C# / .NET, WinForms, DevExpress |
| Protección | DNGuard (obfuscador .NET) |
| Auto-Update | HTTP manifest + ZIP |
| IPC | Named Pipes |
| Discord | Discord.Net |
| Telegram | Telegram.Bot |
| Game Hacks | DLL Injection |

## 📊 Módulos Principales (Namespaces)

### Game Modules
- `LordsMobileBot.Game` - Núcleo del juego
- `LordsMobileBot.Game.Building` - Construcción de edificios
- `LordsMobileBot.Game.Arena` - Arena PVP
- `LordsMobileBot.Game.PVP` - Sistema PVP
- `LordsMobileBot.Game.GVG` - Guild vs Guild
- `LordsMobileBot.Game.Magic` - Eventos mágicos
- `LordsMobileBot.Game.World` - Mapa del mundo
- `LordsMobileBot.Game.Dungeon` - Calabozos
- `LordsMobileBot.Game.Expedition` - Expediciones
- `LordsMobileBot.Game.ADGame` - Minijuego de defensa
- `LordsMobileBot.Game.Newbie` - Tutorial
- `LordsMobileBot.Game.Map` - Sistema de mapas
- `LordsMobileBot.Game.Mission` - Missions
- `LordsMobileBot.Game.Tech` - Tecnología
- `LordsMobileBot.Game.Decorations` - Decoraciones

### Account & Social
- `LordsMobileBot.AppClasses.AccountManager` - Gestor de cuentas
- Login con: Google, Huawei, Facebook, WeChat, Amazon

### Automatización
- `LordsMobileBot.Game.Simulator` - Simulador de batallas
  - `BattleSimulator` - Simula batallas
  - `CombatSimulator` - Simula combate
  - `TDSimulator` - Simulador Tower Defense
- `SimulateStage`, `SimulateBattle`, `SimulateArena`, `SimulateMonster`, `SimulateMagicStage`

### Integraciones
- `LordsMobileBot.AppClasses.ChatBot` - Sistema de chat
- `ChatBot.Commands` - Comandos del bot
- `discordBot` - Bot de Discord
- `tgBot` - Bot de Telegram
- `lordsWebhook` - Sistema de webhooks

### UI Forms (Partial List)
- `AccountWindow` - Ventana de cuentas
- `botControlForm` - Control principal del bot
- `buildingSettings`, `heroSettings`, `gatherSettings`
- `protectionSettings` - Configuración de protección
- `eventSettings`, `guildSettings`, `warSettings`
- `resourceControl`, `armyControl`, `researchControl`

## 🎮 DLL Hooks (Game Memory Manipulation)

### Hero Management
- `DLLBSGetHeroNowHP` / `DLLBSSetHeroNowHP`
- `DLLBSGetHeroPosition` / `DLLBSSetHeroPosition`
- `DLLBSAddHeroExtraSkillEffect`
- `DLLBSHeroReplaceSkill`
- `DLLBSSetHeroAtkAddition`
- `DLLBSSetHeroOver`

### Monster/Boss
- `DLLBSGetPVEMonsterHP` / `DLLBSSetPVEMonsterHP`
- `DLLBSGetPVEMonsterDamage`
- `DLLBSSetPVEMonsterAttr`

### Buildings
- `DllCSCalculateBuildingBonus`
- `DLLBSSetCBGameBuildEffect`

### Arena
- `DLLBSSetArenaTopic`

### Troops
- `DLLCSSetTroopOver`

### TD (Tower Defense)
- `DLLTDGetEventDataLen`
- `DLLTDSSetOver`
- `DLLTDSetUserData`
- `DLLTDClientInvisibleShow`

### Game Data
- `DLLBSSetStageVersion`
- `DLLBSSetRewardData`
- `DLLBSSetUserData`
- `DLLBSGetEventDataLen`
- `DLLBSGameSetting`
- `DLLBSCasinoModeInput`

## 💬 Sistema de Chat/Comandos

### Integraciones
- **Discord**: Usa Discord.Net
  - Slash commands
  - Recibe mensajes
  - Envía imágenes/archivos
  
- **Telegram**: Usa Telegram.Bot
  - Polling para updates
  - Envía mensajes, imágenes, archivos

- **Webhooks**
  - `SendAccountStatus`
  - `SendMessageFromAccount`
  - Configurable por usuario

### Account Manager Commands
- `addAccount`
- `deleteAccount`
- `findAccount`
- `StartAccount`
- `StopAccount`
- `resetAccount`
- `SetAccount`
- `createNewAccount`
- `loadAllAccounts`
- `BackupAccounts`

## 🔐 Sistemas de Protección

1. **DNGuard** - Obfuscador de código .NET
2. **HVMRuntime.dll** - Protección de runtime
3. **Memory Manipulation** - Modificación directa de RAM del juego
4. **Named Pipes** - Comunicación segura entre procesos

## 📝 Notas de Ingeniería Reversa

1. Los archivos `.txt` en GameAssets están codificados en binario (no legibles como texto plano)
2. Los recursos "Heros.bytes", "Skills.bytes" están embebidos en el ejecutable
3. El sistema usa `ProcessMemoryLimit` y funciones de `ReadProcessMemory`/`WriteProcessMemory`
4. Las direcciones de memoria usan un sistema de `GetAddress`, `SetAddress` con offsets dinámicos

## ⚠️ Riesgos y Limitaciones

1. **Ban del juego** - DLL injection viola TOS
2. **DNGuard** - Código ofuscado, difícil de modificar
3. **Sin source** - No hay código fuente disponible
4. **Updater** - Descarga y ejecuta binarios de internet

## 🎯 Conceptos para Replicar (Anti-Ban)

1. **Sistemas anti-detección**
   - Rotación de accounts
   - Random delays entre acciones
   - Detección de patrones de jugadores reales

2. **Account Manager**
   - Sistema de múltiples cuentas
   - Backup/restore de cuentas
   - Rotación automática

3. **Simulator**
   - Simulación de batallas para testing
   - Validación de estrategias

4. **Integraciones Externas**
   - Discord/Telegram bots para control remoto
   - Webhook para notificaciones
