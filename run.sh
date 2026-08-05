#!/usr/bin/env bash

# SnapBili Web Downloader Auto Runner
set -e

echo "=================================================="
echo "    SnapBili Web Downloader Auto Runner           "
echo "=================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

PYTHON_BIN=""
if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
elif command -v py &> /dev/null; then
    PYTHON_BIN="py -3"
else
    echo "[❌] Lỗi: Không tìm thấy Python!"
    exit 1
fi

VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Đang tạo môi trường ảo Python (venv)..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

if [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
fi

echo "[+] Đang kiểm tra thư viện..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo "[+] Khởi chạy Web Server tại: http://127.0.0.1:5000"
python app.py
