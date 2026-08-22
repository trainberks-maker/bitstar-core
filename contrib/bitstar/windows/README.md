# BitStar Windows Launcher Scripts

These helper scripts are included in the Windows bootstrap package.

The recommended entry point for normal users is `BitStar-Launcher.bat`. It
opens a PowerShell menu that can create the local config, start the node, show
sync status, open the GUI, back up loaded wallets, open the data folder, and
stop the node cleanly.

## Scripts

- `Start-BitStar-Node.bat` starts `bitstard.exe` and connects to the public
  seed nodes.
- `Check-BitStar-Status.bat` checks sync state and peer count.
- `Stop-BitStar-Node.bat` stops the local node cleanly.
- `Open-BitStar-Console.bat` opens a command prompt in the BitStar folder.
- `BitStar-Launcher.bat` opens the interactive launcher menu.
- `BitStar-Launcher.ps1` contains the launcher logic and can also be run with
  actions such as `-Action start`, `-Action status`, `-Action backup`, and
  `-Action stop`.

## Launcher Actions

From PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\BitStar-Launcher.ps1 -Action start
powershell -ExecutionPolicy Bypass -File .\BitStar-Launcher.ps1 -Action status
powershell -ExecutionPolicy Bypass -File .\BitStar-Launcher.ps1 -Action backup
powershell -ExecutionPolicy Bypass -File .\BitStar-Launcher.ps1 -Action stop
```

The launcher uses `%LOCALAPPDATA%\BitStar` by default. Advanced testers can
pass a separate data directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\BitStar-Launcher.ps1 -Action start -DataDir "$env:TEMP\bitstar-clean-test"
```

## Notes

- The default data directory is `%LOCALAPPDATA%\BitStar`.
- Windows Firewall may ask for network access the first time the node starts.
- RPC is configured for localhost only. Do not expose RPC port `21332` to the
  public internet.
- This is pre-release software. Do not use it for custody, exchange deposits,
  merchant payments, or production funds.
