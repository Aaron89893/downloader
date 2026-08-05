# ⚡ Downloader - Web App & Chrome Extension

Hệ thống tải video HD (1080p) kèm phụ đề gốc tự động từ **Bilibili, YouTube, TikTok, Douyin** gom vào từng thư mục riêng biệt.

---

## ⚡ Hướng Dẫn Nhanh (Quick Start)

### 1. Khởi tạo & Cài đặt Môi Trường (Setup)
- Nhấp đúp file **`setup.bat`** (Tự động tải & cài đặt Python 3.11 nếu máy chưa có, khởi tạo `venv` và cài đặt các thư viện cần thiết).

### 2. Khởi chạy Web Server Backend (Run)
- Nhấp đúp file **`run.bat`** hoặc gõ `.\run.bat` trên PowerShell.
- Server tự động kích hoạt môi trường ảo `venv` và chạy tại: `http://127.0.0.1:5000`

### 3. Khởi chạy Cùng Windows (Tùy chọn Auto-Start)
- Nhấp đúp file **`install_auto_start.bat`** (Đăng ký Web Server tự động chạy ngầm mỗi khi mở máy tính).

### 4. Cài đặt Chrome Extension
1. Mở trình duyệt Chrome → Truy cập `chrome://extensions`
2. Bật **Developer mode** ở góc trên bên phải
3. Nhấn **Load unpacked** → Chọn thư mục `./extension` trong dự án

---

## 🚀 Tính Năng Nổi Bật

- 🎯 **Gom Thư Mục Riêng**: Tự động tạo thư mục theo ID Video (ví dụ: `BV1KS4y1i7zL/`) chứa đúng 1 file Video (`.mp4`/`.webm`) và 1 file Phụ Đề Gốc (`.orig.srt`).
- 🛡️ **2-Stage Zero-Failure Fallback**: Tự động gỡ cookie xung đột và chuyển sang luồng dự phòng nếu YouTube chặn tải.
- ⚡ **Bilibili Danmaku & Douyin Subtitle**: Giải nén zlib Danmaku Bilibili và ghép phụ đề multi-block Douyin/TikTok.
- 🧹 **Tự Động Xóa Đĩa**: Tự động dọn dẹp file tạm trên ổ đĩa sau 60 giây để tránh tràn bộ nhớ.

---

## ⚙️ Lệnh Điều Khiển CMD / PowerShell

| Thao tác | Câu lệnh / File |
| :--- | :--- |
| **Setup Môi Trường** | `setup.bat` |
| **Bật Server** | `run.bat` hoặc `.\venv\Scripts\python.exe app.py` |
| **Tắt Server** | `taskkill /F /IM python.exe` |
| **Tự Bật Cùng Win** | `install_auto_start.bat` |
