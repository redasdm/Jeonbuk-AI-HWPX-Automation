@echo off
setlocal
title AntiGravity - CV Macro Setup

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
) else (
    echo [1/3] Virtual environment already exists. Skipping.
)

:: 3. Install Packages
echo.
echo [2/3] Installing required packages...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
echo   Done.

:: 4. Select Option
echo.
echo [3/3] What would you like to do?
echo   [1] Capture template images (FIRST TIME SETUP)
echo   [2] Run CV macro
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" (
    echo.
    echo Starting template capture tool...
    .venv\Scripts\python capture_templates.py
) else if "%choice%"=="2" (
    echo.
    echo Starting CV macro...
    .venv\Scripts\python cv_macro.py
) else (
    echo Invalid choice. Exiting.
)

echo.
pause
