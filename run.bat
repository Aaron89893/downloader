@echo off
title Downloader - Server Host
echo ============================================================
echo      STARTING DOWNLOADER WEB SERVER (PORT 5000)          
echo ============================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment venv not found. Running setup.bat...
    call setup.bat
)

call venv\Scripts\activate.bat

echo [OK] Launching backend server at: http://127.0.0.1:5000
echo [*] Please keep this window open while using Chrome Extension.
echo.
python app.py
pause
