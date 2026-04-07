@echo off
setlocal

echo.
echo ====================================================
echo   AntiGravity - JBStudy Auto Macro Setup
echo ====================================================
echo.

:: Step 1: Open Tampermonkey Chrome Extension page
echo [1/3] Opening Tampermonkey extension page in Chrome...
echo       (If already installed, just close the tab)
echo.
start "" "chrome.exe" "https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo"
pause

echo.
echo ====================================================
echo [2/3] Opening script file for Tampermonkey install...
echo       Click the [Install] button in the new tab!
echo ====================================================
echo.
set "SCRIPT_PATH=%~dp0lms_auto_macro.user.js"
start "" "chrome.exe" "%SCRIPT_PATH%"
pause

echo.
echo ====================================================
echo [3/3] Opening the JBStudy lecture popup...
echo ====================================================
echo.
start "" "chrome.exe" "https://www.jbstudy.kr/lh/mc/ch/selectMcLrnrHomePopup.do"

echo.
echo Setup complete! The macro will run automatically.
echo.
echo How it works:
echo  - Icon 1 (during lecture): auto-clicked when detected
echo  - Rate ^>= 90%%: clicks lecture screen, then icon 2 (playerBtnafter)
echo  - Moves to next chapter automatically
echo.
pause
