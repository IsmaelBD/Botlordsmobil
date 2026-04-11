# Account Manager - Sistema de Cuentas

## Login Providers
- Google OAuth (`LordsMobileBot.OAuth.Google`)
- Huawei OAuth (`LordsMobileBot.OAuth.Huawei`)
- Facebook OAuth
- WeChat OAuth  
- Amazon OAuth
- IGG (vendor propio)

## Account Manager API
```
AccountWindow - Ventana principal
AccountManager - Gestor central
├── addAccount
├── deleteAccount
├── findAccount
├── StartAccount
├── StopAccount
├── resetAccount
├── SetAccount
├── createNewAccount
├── loadAllAccounts
├── BackupAccounts / PCBackupAccounts
└── RestoreAccounts

AccountInfo
├── UpdateAccountInfo
├── GetPlayerDataList
├── isPlayerDataReady
└── m_CombatPlayerData
```

## Login Flow
```
LoginWorker_DoWork
├── beginLogin
│   └── LoginFinish
├── ResendEmailButton_Click
├── ResetPasswordButthon_Click
└── PasswordWorker_DoWork
```

## Account Backup
- Backup1, Backup2, Backup3 - slots de backup
- Import/Export de cuentas
- ExportType (DumpFile, RawFile, HtmlExport)
- GuildStatExportForm

## Device ID System
```
get_DeviceID / set_DeviceID
tDeviceID
createDeviceIDFile
DeviceIDReachTheLimit
DeviceIDInput / openDeviceIDBox
```

## Proxy Support
```
proxyWorker_DoWork
TryConnectViaProxy
proxyIP
stripProxyPass
resetProxyRetry
setProxy
```
