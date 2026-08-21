@echo off
setlocal
cd /d "%~dp0"

echo Starting BitStar Core node...
echo Data directory: %LOCALAPPDATA%\BitStar
echo.

start "BitStar Core Daemon" "%~dp0bitstard.exe" -server=1 -listen=1 -dnsseed=1 -addnode=seed1.bitstarcoin.org:21333 -addnode=seed2.bitstarcoin.org:21333

echo Waiting for BitStar RPC to become available...
timeout /t 8 /nobreak >nul

"%~dp0bitstar-cli.exe" getblockchaininfo
if errorlevel 1 (
  echo.
  echo BitStar is still starting. Run Check-BitStar-Status.bat again in a minute.
)

echo.
pause
