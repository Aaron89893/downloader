@echo off
title Downloader - Automatic Setup Script
echo ============================================================
echo      DOWNLOADER AUTOMATIC SETUP AND CONFIGURATION          
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed on this system.
    echo [+] Auto-installing Python 3.11 for Windows...
    winget install --id Python.Python.3.11 -e --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
    if %errorlevel% neq 0 (
        echo [+] Downloading Python installer via PowerShell...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%temp%\python_setup.exe'"
        echo [+] Running silent Python installation...
        "%temp%\python_setup.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    )
    echo [✓] Python installation completed. Refreshing environment...
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;C:\Program Files\Python311;C:\Program Files\Python311\Scripts;%PATH%"
)

echo [1/3] Creating Python Virtual Environment (venv)...
if not exist venv\Scripts\python.exe python -m venv venv

echo [2/3] Installing required dependencies into venv...
.\venv\Scripts\python.exe -m pip install -r requirements.txt >nul 2>&1

echo [3/3] Preparing downloads directory...
if not exist downloads mkdir downloads

echo.
echo ============================================================
echo      SETUP COMPLETED SUCCESSFULLY!           
echo ============================================================
echo.