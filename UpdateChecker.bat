REM Automates process of checking for upgrades and upgrading each depenedency manually

@echo off
REM Change directory to where your Python script is located
REM Example: cd C:\Users\YourName\Documents\MyScripts

REM Run WSL and execute the Python script
python upgrade_checker.py
python auto_update.py

pause
