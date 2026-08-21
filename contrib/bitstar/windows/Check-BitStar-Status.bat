@echo off
setlocal
cd /d "%~dp0"

echo BitStar Core status
echo.

"%~dp0bitstar-cli.exe" getblockchaininfo
echo.
"%~dp0bitstar-cli.exe" getconnectioncount

echo.
pause
