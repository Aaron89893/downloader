# Bilibili High Quality & No-Watermark Downloader

Tool tải video Bilibili tự động, không watermark, chất lượng cao nhất (hỗ trợ 1080p, 1080p60, 4K, 8K) sử dụng Python & yt-dlp engine.

## 🚀 Tính năng nổi bật

1. **Không Watermark**: Trực tiếp bóc tách luồng DASH gốc (video + audio), không bị dính logo như trên trình duyệt.
2. **Chất lượng cao nhất**: Tải stream video & audio có bitrate cao nhất và ghép thành file `.mp4` hoàn chỉnh.
3. **Tự động hóa**: Nhập danh sách link vào `urls.txt` và chỉ cần chạy `run.sh`.
4. **Hỗ trợ Cookies.txt**: Mở khóa các độ phân giải 1080p60, 4K (2160p), 8K và âm thanh chuẩn Dolby/Hi-Res.

---

## 🛠️ Hướng dẫn sử dụng

### 1. Thêm URL cần tải
Mở file `urls.txt` và dán các đường dẫn video Bilibili vào (mỗi link một dòng). Hỗ trợ link thường, link b23.tv rút gọn, link phim/anime (bangumi).

```text
https://www.bilibili.com/video/BV1xX4y1A76z
https://b23.tv/xxxxxx
```

### 2. Chạy Tool
Mở Terminal / Git Bash và chạy lệnh:

```bash
bash run.sh
```

Tool sẽ tự động:
- Khởi tạo môi trường ảo Python (`venv`)
- Cài đặt các thư viện phụ thuộc (`yt-dlp`)
- Tải tất cả video trong `urls.txt` và lưu vào thư mục `downloads/`

---

## 💎 Cách mở khóa chất lượng 4K / 1080p60

Mặc định Bilibili giới hạn chất lượng đối với người dùng chưa đăng nhập (Khách / Guest) ở mức 720p hoặc 1080p tiêu chuẩn.

Để tải được **4K, 1080p60, 8K**:
1. Đăng nhập tài khoản Bilibili trên trình duyệt (Chrome / Edge / Firefox).
2. Dùng tiện ích mở rộng (Extension) như **Get cookies.txt LOCALLY** để xuất cookie của trang `bilibili.com`.
3. Lưu file xuất ra thành tên `cookies.txt` và để cùng thư mục với script này.
4. Chạy lại `bash run.sh`, tool sẽ tự nhận diện file `cookies.txt` và tải ở độ phân giải tối đa của tài khoản!

---

## 📌 Yêu cầu hệ thống

- Python 3.8+
- [FFmpeg](https://ffmpeg.org/) (đã thêm vào PATH hệ thống để ghép video & audio)
