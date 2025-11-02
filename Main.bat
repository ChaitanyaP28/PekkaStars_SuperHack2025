REM Single point of initialization: starts main.py which starts orchestrator and health monitor

@echo off
REM === Launch FastAPI Admin Panel ===
cd /d "%~dp0"

echo Starting Admin Panel...
echo (Close this window to stop the server.)
echo.

python "%~dp0main.py"

pause
