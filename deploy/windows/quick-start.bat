@echo off
REM TradingMTQ Quick Start Script for Windows
REM Run this for one-command deployment

echo.
echo ========================================
echo   TradingMTQ Quick Start
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell not found
    echo Please install PowerShell to use this script
    pause
    exit /b 1
)

REM Run the PowerShell setup script
echo Running deployment setup...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   Setup Complete!
    echo ========================================
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo.
    echo ========================================
    echo   Setup Failed
    echo ========================================
    echo.
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)
