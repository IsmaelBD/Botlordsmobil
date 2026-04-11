# Chat Bot & Command System

## Integrations

### Discord Bot
```
LordsMobileBot.AppClasses.ChatBot.discordBot
├── Init
├── StartBot
├── Bot_Ready
├── Bot_MessageReceived
├── Bot_SlashCommandExecuted
├── Bot_AutocompleteExecuted
├── SendMessage
├── SendImage
└── SendFile
```
- Usa Discord.Net (DiscordSocketConfig)

### Telegram Bot  
```
LordsMobileBot.AppClasses.ChatBot.tgBot
├── Init
├── HandleUpdateAsync
├── SendMessage
├── SendImage
└── SendFile
```
- Usa Telegram.Bot con Polling

### Webhooks
```
lordsWebhook
├── MessageWorkerThread
├── SendMessage (multiple overloads)
├── SendImage
├── SendFile_
├── SendFile
├── Chunker
├── SendAccountStatus
└── SendMessageFromAccount
```

## Chat Commands
```
LordsMobileBot.AppClasses.ChatBot.Commands
├── ClearGroupCmd
├── CmdBase
│   ├── Execute
│   ├── AutoComplete
│   └── AccountMenuAutoComplete
├── HelpCmd
├── LogCmd
├── QStatusCmd
├── ScreenshotCmd
├── SetCastleCmd
└── ShortLogCmd
```

## Command Handler
```
cmdHandler
├── RouteInteraction
├── RouteCommand  
├── RouteAutoComplete
└── findAcc
```

## Chat Settings
```
allowChatCommands
clearChatBotDataBtn
ChatBot_Stack1
ChatBot_Stack_2
```
