@echo off
cd /d "%~dp0"
echo ====================================
echo   AntiGravity CV Macro Launcher
echo ====================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않거나 환경 변수(PATH)에 추가되지 않았습니다!
    echo 파이썬 설치 시 화면 하단의 "Add python.exe to PATH" 옵션을 **반드시 체크**하고 설치해주세요.
    echo 다운로드: https://www.python.org/downloads/
    pause
    exit /b
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment - please wait...
    python -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
    echo [오류] 가상환경(.venv) 생성에 실패했습니다. 폴더 권한 문제이거나 백신 때문일 수 있습니다.
    pause
    exit /b
)

echo Installing packages...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo Done! Launching GUI...

.venv\Scripts\python.exe gui_app.py
pause
