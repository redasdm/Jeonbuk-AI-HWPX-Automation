@echo off
cd /d "%~dp0"
echo ====================================
echo   AntiGravity CV Macro Launcher
echo ====================================
echo.
echo Current folder: %CD%
echo.

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo Launching GUI...
.venv\Scripts\python.exe gui_app.py
echo.
echo === Program exited. Press any key to close ===
pause >nul
