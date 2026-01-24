@echo off
:: ═══════════════════════════════════════════════════════════════
::  IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT
::  Run this file as Administrator!
:: ═══════════════════════════════════════════════════════════════

echo.
echo   Launching Iran-Only Firewall...
echo.

cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python is not installed!
    echo.
    echo   Please install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo   Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Run the script
python iran_firewall.py

pause
