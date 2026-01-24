@echo off
:: Iran-Only Firewall for Psiphon Conduit
:: This script auto-elevates to Administrator

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Now running as admin
cd /d "%~dp0"
python iran_firewall.py
pause
