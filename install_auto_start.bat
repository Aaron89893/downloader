@echo off
title Install Windows Auto Startup for Downloader
echo ============================================================
echo      🚀 CẤU HÌNH TỰ ĐỘNG BẬT SERVER KHI MỞ MÁY TÍNH          
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set VBS_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DownloaderServer.vbs

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WshShell.Run """%SCRIPT_DIR%run.bat""", 0, False >> "%VBS_PATH%"

echo [✓] Đã cài đặt tự động khởi chạy ngầm thành công!
echo Từ bây giờ, Web Server sẽ tự động bật ngầm khi bạn mở máy tính.
echo Bạn có thể sử dụng Chrome Extension ngay lập tức mà KHÔNG CẦN bật server bằng tay nữa!
echo.
pause
