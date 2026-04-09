@echo off
cd /d "%~dp0"
echo ====================================
echo   AntiGravity CV Macro Launcher
echo ====================================
echo.

if not exist ".venv" (
    echo Creating virtual environment - please wait...
    python -m venv .venv
)

echo Installing packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo Done! Launching GUI...

.venv\Scripts\python.exe gui_app.py
pause
