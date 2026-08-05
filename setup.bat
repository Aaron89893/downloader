@echo off
title Downloader - Automatic Setup Script
echo ============================================================
echo      DOWNLOADER AUTOMATIC SETUP AND CONFIGURATION          
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python Virtual Environment (venv)...
if not exist "venv" (
    echo [+] Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready.

echo [2/4] Installing required dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)
echo [OK] Dependencies installed (yt-dlp, flask, flask-cors, requests, imageio-ffmpeg).

echo [3/4] Checking downloads directory...
if not exist "downloads" (
    mkdir downloads
)
echo [OK] Downloads directory ready.

echo [4/4] Verifying FFmpeg binary...
python -c "import imageio_ffmpeg; print('[OK] FFmpeg Binary:', imageio_ffmpeg.get_ffmpeg_exe())"
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg verification warning.
)

echo.
echo ============================================================
echo      SETUP COMPLETED SUCCESSFULLY!           
echo ============================================================
echo.
echo To run the application:
echo  1. Run: run.bat
echo  2. Load Chrome Extension from folder: ./extension
echo.
pause
