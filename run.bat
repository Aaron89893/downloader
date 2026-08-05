@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title SnapBili Web Downloader - Bilibili No Watermark

echo ==================================================
echo     SnapBili Web Downloader Auto Runner
echo ==================================================

cd /d "%~dp0"

if exist venv goto HAS_VENV
echo [+] Creating Python virtual environment...
python -m venv venv

:HAS_VENV
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

echo [+] Checking and installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo [+] Starting Web App at http://127.0.0.1:5000 ...
start "" http://127.0.0.1:5000
python app.py

echo.
echo [OK] Execution completed.
pause
