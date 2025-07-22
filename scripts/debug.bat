@echo off
:: Navigate up one directory to the project root
cd /d %~dp0\..

:: Set PYTHONPATH to include the project root
set PYTHONPATH=%CD%

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Run the GUI application with pythonw (window mode) instead of python
start "" pythonw app\guiMain.py

if errorlevel 1 (
    echo 🔴 Error running guiMain.py
    pause
    exit /b 2
)

:: Note: We don't need to deactivate since the start command runs in a separate process