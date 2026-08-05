# ⚡ Downloader - Chrome Extension & Backend

Tải video HD (1080p) kèm phụ đề gốc từ **Bilibili, YouTube, TikTok, Douyin** vào một thư mục riêng biệt.

---

## ⚡ Hướng Dẫn Nhanh (Quick Start)

### 1. Khởi chạy Server (1-Click)
- Nhấp đúp file **`run.bat`**
- Server tự động cài đặt môi trường và chạy tại: `http://127.0.0.1:5000`

### 2. Cài đặt Chrome Extension
1. Mở Chrome → Truy cập `chrome://extensions`
2. Bật **Developer mode** (Góc trên bên phải)
3. Nhấn **Load unpacked** → Chọn thư mục `./extension`

---

## 🚀 Tính Năng Chính
- **2 File Duy Nhất**: Tự động lưu 1 file Video (`.mp4`) và 1 file Phụ Đề Gốc (`.orig.srt`).
- **Thư Mục Chuẩn**: Tự động gom 2 file vào thư mục mang mã ID Video (ví dụ: `BV1KS4y1i7zL/`).
- **Bilibili Danmaku**: Tự bóc tách và giải nén 400+ câu phụ đề Danmaku.
- **Tự Động Làm Sạch Bộ Nhớ**: Tự động xóa file tạm trên đĩa sau 60 giây.

---

## ⚙️ Lệnh Điều Khiển qua CMD

- **Bật Server**: `run.bat`
- **Tắt Server**: `taskkill /F /IM python.exe`
