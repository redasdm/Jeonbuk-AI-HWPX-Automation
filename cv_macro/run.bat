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

:: CMD 창을 작업표시줄로 최소화
powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()" >nul 2>&1

.venv\Scripts\python.exe gui_app.py
pause
