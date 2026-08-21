# BitStar Windows Launcher Scripts

These helper scripts are included in the Windows bootstrap package.

## Scripts

- `Start-BitStar-Node.bat` starts `bitstard.exe` and connects to the public
  seed nodes.
- `Check-BitStar-Status.bat` checks sync state and peer count.
- `Stop-BitStar-Node.bat` stops the local node cleanly.
- `Open-BitStar-Console.bat` opens a command prompt in the BitStar folder.

## Notes

- The default data directory is `%LOCALAPPDATA%\BitStar`.
- Windows Firewall may ask for network access the first time the node starts.
- This is pre-release software. Do not use it for custody, exchange deposits,
  merchant payments, or production funds.
