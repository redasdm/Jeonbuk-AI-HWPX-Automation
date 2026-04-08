@echo off
setlocal
title AntiGravity - CV Macro Setup

echo.
echo ====================================================
echo   AntiGravity CV Macro - Setup and Run
echo ====================================================
echo.

:: Check python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

:: Create venv if not exists
if not exist ".venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv .venv
    echo       Done.
) else (
    echo [1/3] Virtual environment already exists. Skipping.
)

:: Install packages
echo.
echo [2/3] Installing required packages...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
echo       Done.

:: Ask what to run
echo.
echo [3/3] What would you like to do?
echo.
echo   [1] Capture template images  (FIRST TIME SETUP - run this first!)
echo   [2] Run CV macro             (Start the auto-study macro)
echo.
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" (
    echo.
    echo Starting template capture tool...
    echo Make sure the JBStudy lecture popup is open in Chrome before proceeding!
    echo.
    .venv\Scripts\python capture_templates.py
    echo.
    echo [자동 실행] 설정이 완료되어 매크로를 곧바로 시작합니다...
    echo Press Ctrl+C in this window to stop.
    echo.
    .venv\Scripts\python cv_macro.py
) else if "%choice%"=="2" (
    echo.
    echo Starting CV macro...
    echo Press Ctrl+C in this window to stop.
    echo.
    .venv\Scripts\python cv_macro.py
) else (
    echo Invalid choice. Exiting.
)

echo.
pause
