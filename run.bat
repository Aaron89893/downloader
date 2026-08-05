@echo off
title Downloader - Server Host
echo ============================================================
echo      🚀 DOWNLOADER WEB SERVER (PORT 5000)          
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist "venv" (
    echo [+] Creating virtual environment (venv)...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1

if not exist "downloads" (
    mkdir downloads
)

echo [OK] Launching backend server at: http://127.0.0.1:5000
echo [*] Keep this window open while using Chrome Extension.
echo.
python app.py
pause
