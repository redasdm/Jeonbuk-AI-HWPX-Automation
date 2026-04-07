@echo off

set "SSID=JBE-WIFI"
echo 와이파이 네트워크 상태를 확인 중입니다... [%SSID%]

:: 현재 JBE-WIFI에 연결되어 있는지 확인 (네트워크 상태 판별 로직)
:: netsh 결과에서 현재 대상 SSID가 존재하는지 검색하여 연결 여부를 판단합니다.
netsh wlan show interfaces | findstr /C:"%SSID%" > nul

if %errorlevel% equ 0 (
    echo ===================================================
    echo 현재 [%SSID%] 에 연결되어 있습니다.
    echo 와이파이 연결을 해제합니다...
    echo ===================================================
    
    :: 와이파이 연결을 끊는 로직 (현재 네트워크 연결 수동 차단 목적)
    netsh wlan disconnect
) else (
    echo ===================================================
    echo 현재 [%SSID%] 에 연결되어 있지 않거나 다른 네트워크에 있습니다.
    echo [%SSID%] 와이파이 연결을 시도합니다...
    echo ===================================================
    
    :: 대상 프로필 이름으로 와이파이에 연결 (네트워크 액세스 복원 목적)
    netsh wlan connect name="%SSID%"
)

echo.
echo 작업을 완료했습니다. 창이 곧 닫힙니다.
timeout /t 0 > nul
