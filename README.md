## Super Hack 2025
## Team: PEKKA STARS
### Team Members : Kamboji Akhilesh, Chaitanya Patange, Micheal Keal, M Hitesh
### Problem Statement : Operational Efficiency Improvement for MSPs and IT Teams

## Video Link : https://youtu.be/-D-Wdspi4J0

## Requirements : 
#### Powershell 7 (pwsh)
Please install powershell 7+ using this link for windows (auto-downloads) and install the same ```
https://github.com/PowerShell/PowerShell/releases/download/v7.5.3/PowerShell-7.5.3-win-x64.msi```
#### Pip libraries : 
Please install all libraries listed in requirements.txt. Please also modify .env file to provide
LLM and LLM API keys

## How to run :
Prototype was designed to run on Windows and spawns services/modules on individual pwsh shells.
Start the prototype by executing `.\Main.bat` from a command prompt or powershell
Go to URL http://localhost:8000 to access the Admin Panel
Everything else can be run directly from the Admin Panel

## Cleanup :
The prototype may generate temporary files which may need to removed manually. This is a known issue.
Most of the files are cleaned up using restore.py. Some extra files may remain.


