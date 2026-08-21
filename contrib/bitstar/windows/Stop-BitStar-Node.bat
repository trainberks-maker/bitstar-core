@echo off
setlocal
cd /d "%~dp0"

echo Stopping BitStar Core node...
"%~dp0bitstar-cli.exe" stop

echo.
pause
