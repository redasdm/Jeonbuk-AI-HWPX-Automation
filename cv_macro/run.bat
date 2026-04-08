@echo off
cd /d "%~dp0"
echo ====================================
echo   AntiGravity CV Macro Launcher
echo ====================================
echo.
echo Current folder: %CD%
echo.

if not exist ".venv" (
    echo [1/3] Creating virtual environment (This will take a minute - please wait!)...
    python -m venv .venv
    echo   Done.
)

echo [2/3] Downloading and installing required packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo   Done.

echo.
echo [3/3] Launching GUI (this window will close automatically)...
cscript //nologo launch_gui.vbs
exit
