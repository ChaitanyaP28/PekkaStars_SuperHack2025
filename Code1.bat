REM --- Bat file used by Orchestrator to handle failure-retry loop for service 1.py
@echo off
REM --- Automatic Restart for 1.py ---

:loop
echo Starting 1.py...
python "%~dp0\1.py"

echo.
echo 1.py crashed or exited. Restarting in 10 seconds...
timeout /t 10 /nobreak >nul
echo.

goto loop
