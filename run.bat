@echo off
title Downloader - Server Host
echo ============================================================
echo      DOWNLOADER WEB SERVER (PORT 5000)          
echo ============================================================
echo.

if not exist venv\Scripts\python.exe (
    echo [!] Virtual environment venv not found. Running setup.bat...
    call setup.bat
)

echo [OK] Launching backend server at http://127.0.0.1:5000
echo [*] Keep this window open while using Chrome Extension.
echo.
.\venv\Scripts\python.exe app.py
pause
