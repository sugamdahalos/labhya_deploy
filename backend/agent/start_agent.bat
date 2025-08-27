@echo off
title Labhya GPU Agent

echo.
echo ================================================================
echo               Labhya GPU Agent Startup
echo ================================================================
echo.
echo IMPORTANT: This is a Windows batch file (.bat)
echo Do NOT run this with Python! Use one of these methods:
echo.
echo   Method 1: Double-click this file in Windows Explorer
echo   Method 2: Run in Command Prompt: start_agent.bat
echo   Method 3: Run Python script: python start_agent.py
echo.
echo If you ran "python start_agent.bat" - that's wrong!
echo Batch files should not be run with Python.
echo.
pause
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "combined_agent.py" (
    echo Error: combined_agent.py not found
    echo Please run this script from the agent directory
    pause
    exit /b 1
)

if not exist "start_agent.py" (
    echo Error: start_agent.py not found
    echo Please run this script from the agent directory
    pause
    exit /b 1
)

echo Starting Labhya GPU Agent...
echo.

REM Use the Python startup script for better cross-platform compatibility
python start_agent.py

echo.
pause
