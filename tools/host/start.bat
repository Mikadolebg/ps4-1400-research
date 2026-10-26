@echo off
setlocal
title PS4 14.00 research host (port 8000)
cd /d "%~dp0..\.."

set PYCMD=python
%PYCMD% --version >nul 2>&1
if errorlevel 1 (
    set PYCMD=py -3
    %PYCMD% --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found.
        pause
        exit /b 1
    )
)

set LANIP=
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | ForEach-Object { $_.IPv4Address.IPAddress } | Select-Object -First 1"`) do set LANIP=%%i
if "%LANIP%"=="" (
    for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' } | Select-Object -First 1).IPAddress"`) do set LANIP=%%i
)

cls
echo ================================================================
echo   PS4 14.00 RESEARCH HOST
echo   server.py (port 8000) + bridge.py (port 8001)
echo   This launcher is stable: it never changes between probes.
echo ================================================================
echo.
if "%LANIP%"=="" (
    echo   Open on the PS4:  http://YOUR_PC_IP:8000/
) else (
    echo   Open on the PS4:  http://%LANIP%:8000/
)
echo.
echo   Session log:    runs\last-session.txt + runs\last-verdicts.txt
echo   Bridge data:    bridge\  (commands.jsonl / results.jsonl / files\)
echo   Live commands:  echo {"t":"ping"} ^>^> bridge\commands.jsonl
echo   Stop: Ctrl+C
echo ================================================================
echo.

start "workshop bridge (port 8001)" cmd /c "%PYCMD% tools\host\bridge.py"
echo   bridge.py launched in a second window (port 8001)
echo.
%PYCMD% tools\host\server.py
pause
