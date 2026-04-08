@echo off
setlocal
title AntiGravity CV Macro Launcher

echo.
echo ====================================================
echo   AntiGravity CV Macro - Setup and Run
echo ====================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    echo   Done.
)

:: 3. Install Packages
echo [2/3] Installing required packages (this might take a few seconds)...
.venv\Scripts\python -m pip install -q --upgrade pip
.venv\Scripts\python -m pip install -q -r requirements.txt
echo   Done.

:: 4. Launch GUI
echo [3/3] Starting CV macro GUI App...
start "" ".venv\Scripts\pythonw.exe" gui_app.py
exit
