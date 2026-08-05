import os
import sys
import io
import re
import glob
import math
import time
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp

from sub_translator import process_all_subtitles
from history_manager import (
    get_all_history, get_history_item, add_or_update_history,
    add_log_to_history, clear_all_history
)

try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_PATH = None

import threading

import uuid

# Force UTF-8 stdout/stderr on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

PROJECT_DIR = Path(__file__).parent.resolve()
DOWNLOADS_DIR = PROJECT_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)
COOKIES_FILE = PROJECT_DIR / "cookies.txt"

def cleanup_old_files(max_age_seconds=180):
    """Clean up temporary download files older than max_age_seconds (3 minutes) to prevent disk memory overflow"""
    now = time.time()
    for item in DOWNLOADS_DIR.glob('*'):
        try:
            if item.is_file() and not item.name.startswith('cookies_') and (now - item.stat().st_mtime > max_age_seconds):
                item.unlink()
        except Exception:
            pass

def delayed_delete(file_path, delay=60):
    """Schedule file deletion 60 seconds after download link is fetched by Chrome Download Manager"""
    def _delete():
        time.sleep(delay)
        try:
            p = Path(file_path)
            if p.exists():
                p.unlink()
        except Exception:
            pass
    threading.Thread(target=_delete, daemon=True).start()

def extract_video_id(url, fallback_id='video'):
    if not url:
        return fallback_id
    bv = re.search(r'(BV[a-zA-Z0-9]+)', url)
    if bv:
        return bv.group(1)
    digits = re.search(r'/video/(\d+)', url)
    if digits:
        return digits.group(1)
    yt = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
    if yt:
        return yt.group(1)
    num = re.search(r'(\d{8,})', url)
    if num:
        return num.group(1)
    return fallback_id

def clean_video_url(url):
    if not url:
        return ''
    url = url.strip()
    if 'youtube.com' in url or 'youtu.be' in url:
        m = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
        if m:
            return f"https://www.youtube.com/watch?v={m.group(1)}"
    return url

def format_duration(seconds):
    if not seconds:
        return "N/A"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_ydl_options(extra_opts=None, sessdata=None, url=None):
    referer = 'https://www.bilibili.com/'
    if url:
        if 'douyin.com' in url:
            referer = 'https://www.douyin.com/'
        elif 'tiktok.com' in url:
            referer = 'https://www.tiktok.com/'
        elif 'youtube.com' in url or 'youtu.be' in url:
            referer = 'https://www.youtube.com/'

    headers = {
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }
    if sessdata:
        headers['Cookie'] = f"SESSDATA={sessdata}"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': headers['User-Agent'],
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'srt/vtt/best',
        'subtitleslangs': ['en', 'vi', 'zh-Hans', 'zh', 'ja', 'orig'],
        'embedsubtitles': True,
        'nocheckcertificate': True,
        'http_headers': headers,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }
    if FFMPEG_PATH:
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 0:
        ydl_opts['cookiefile'] = str(COOKIES_FILE)
    if extra_opts:
        ydl_opts.update(extra_opts)
    return ydl_opts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    url = clean_video_url(data.get('url', ''))

    if not url:
        return jsonify({'error': 'Vui lòng nhập đường dẫn URL hợp lệ (YouTube, TikTok, Bilibili, Douyin).'}), 400

    sessdata = data.get('sessdata')
    temp_cookie_file = None

    try:
        ydl_opts = get_ydl_options({'extract_flat': False}, sessdata=sessdata, url=url)

        # Handle custom Netscape cookies string if passed from Extension
        cookies_txt = data.get('cookies_txt')
        if cookies_txt and isinstance(cookies_txt, str) and cookies_txt.strip():
            temp_cookie_file = str(PROJECT_DIR / f"temp_cookie_analyze_{int(time.time())}_{uuid.uuid4().hex[:4]}.txt")
            with open(temp_cookie_file, "w", encoding="utf-8") as f:
                f.write(cookies_txt)
            if os.path.exists(temp_cookie_file):
                ydl_opts['cookiefile'] = temp_cookie_file

        info = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            video_id = extract_video_id(url, fallback_id='video')
            info = {
                'id': video_id,
                'title': f"Video {video_id}",
                'thumbnail': '',
                'duration': 0,
                'uploader': 'Creator'
            }

        if info and 'entries' in info and info['entries']:
            info = info['entries'][0]

        if not info:
            video_id = extract_video_id(url, fallback_id='video')
            info = {
                'id': video_id,
                'title': f"Video {video_id}",
                'thumbnail': '',
                'duration': 0,
                'uploader': 'Creator'
            }

        title = info.get('title', 'Video')
        thumbnail = info.get('thumbnail') or info.get('cover') or ''
        duration = format_duration(info.get('duration'))
        uploader = info.get('uploader') or info.get('owner', {}).get('name') or 'Creator'
        video_id = info.get('id') or extract_video_id(url, fallback_id='video')

        thumb_proxy = f"/api/proxy_thumb?url={requests.utils.quote(thumbnail)}" if thumbnail else "/static/default-cover.jpg"

        qualities = [
            {'id': '1080p', 'name': '1080p Full HD (Chuẩn)'},
            {'id': '720p', 'name': '720p HD (Tốc độ cao)'},
            {'id': '480p', 'name': '480p SD (Tải Nhanh)'},
            {'id': 'mp3', 'name': '🎵 Tải Âm Thanh MP3'}
        ]

        return jsonify({
            'success': True,
            'title': title,
            'thumbnail': thumb_proxy,
            'duration': duration,
            'uploader': uploader,
            'id': video_id,
            'original_url': url,
            'qualities': qualities,
            'has_subtitles': True
        })

    except Exception as e:
        return jsonify({'error': f'Không thể phân tích URL. Chi tiết: {str(e)}'}), 500
    finally:
        if temp_cookie_file and os.path.exists(temp_cookie_file):
            try:
                os.remove(temp_cookie_file)
            except Exception:
                pass

@app.route('/api/proxy_thumb')
def proxy_thumb():
    thumb_url = request.args.get('url')
    if not thumb_url:
        return Response(status=404)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://www.bilibili.com/'
        }
        res = requests.get(thumb_url, headers=headers, timeout=10)
        return Response(res.content, mimetype=res.headers.get('Content-Type', 'image/jpeg'))
    except Exception:
        return Response(status=500)

@app.route('/api/download', methods=['POST'])
def process_download():
    data = request.get_json() or {}
    url = clean_video_url(data.get('url', ''))
    download_type = data.get('type', '1080p') # '1080p', '720p', '480p', 'mp3'

    if not url:
        return jsonify({'error': 'URL không hợp lệ.'}), 400

    # Auto clean up old temporary files in downloads/
    cleanup_old_files(max_age_seconds=3600)

    try:
        timestamp = int(time.time())
        if download_type == 'mp3':
            fmt = 'bestaudio/best'
            ext = 'mp3'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif download_type == '720p':
            fmt = 'bestvideo[height<=?720]+bestaudio/bestvideo+bestaudio/best'
            ext = 'mp4'
            postprocessors = []
        elif download_type == '480p':
            fmt = 'bestvideo[height<=?480]+bestaudio/bestvideo+bestaudio/best'
            ext = 'mp4'
            postprocessors = []
        else:
            # Default quality max 1080p
            fmt = 'bestvideo[height<=?1080]+bestaudio/bestvideo+bestaudio/best'
            ext = 'mp4'
            postprocessors = []

        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
        task_id = f"task_{unique_id}"
        outtmpl = str(DOWNLOADS_DIR / f'download_{unique_id}_%(id)s.%(ext)s')
        sessdata = data.get('sessdata')

        add_or_update_history(task_id, url=url, status='DOWNLOADING', quality=download_type)
        add_log_to_history(task_id, f"Khởi tạo tác vụ tải video ({download_type}) từ: {url}")

        ydl_opts = get_ydl_options({
            'format': fmt,
            'outtmpl': outtmpl,
            'merge_output_format': 'mp4' if download_type != 'mp3' else None,
            'postprocessors': postprocessors
        }, sessdata=sessdata, url=url)

        # Handle custom Netscape cookies string if passed from Extension
        temp_cookie_file = None
        cookies_txt = data.get('cookies_txt')
        if cookies_txt and isinstance(cookies_txt, str) and cookies_txt.strip():
            temp_cookie_file = str(PROJECT_DIR / f"temp_cookie_{unique_id}.txt")
            with open(temp_cookie_file, "w", encoding="utf-8") as f:
                f.write(cookies_txt)
            if os.path.exists(temp_cookie_file):
                ydl_opts['cookiefile'] = temp_cookie_file
                add_log_to_history(task_id, "Đã nạp cookie xác thực từ trình duyệt active tab.")

        add_log_to_history(task_id, "Đang kết nối tải luồng Video HD & Audio bằng yt-dlp...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if download_type == 'mp3':
                    filename = os.path.splitext(filename)[0] + '.mp3'
                elif download_type != 'mp3' and not filename.endswith('.mp4'):
                    filename = os.path.splitext(filename)[0] + '.mp4'
        finally:
            if temp_cookie_file and os.path.exists(temp_cookie_file):
                try:
                    os.remove(temp_cookie_file)
                except Exception:
                    pass

        if not info:
            return jsonify({'error': 'Tải video thất bại, không nhận được thông tin từ nền tảng.'}), 500

        video_title = info.get('title', 'video')
        raw_id = info.get('id')
        video_id = extract_video_id(url, fallback_id=raw_id if raw_id else 'video')
        thumbnail_url = info.get('thumbnail', '')
        clean_title = re.sub(r'[\\/*?:"<>|【】！~～：？“”]', '_', video_title).strip('_')
        if not clean_title:
            clean_title = f"video_{video_id}"
        
        folder_name = re.sub(r'[\\/*?:"<>|【】！~～：？“”]', '_', str(video_id)).strip('_')
        if not folder_name:
            folder_name = 'video'

        add_or_update_history(task_id, title=clean_title, thumbnail=thumbnail_url)
        add_log_to_history(task_id, f"Tải stream hoàn tất. Đã trích xuất tiêu đề: '{clean_title}'")

        # Auto process XML/SRT/VTT/Fallback subtitles
        orig_sub = None
        if download_type != 'mp3' and os.path.exists(filename):
            add_log_to_history(task_id, "Đang xử lý phụ đề Gốc...")
            orig_sub = process_all_subtitles(filename, title_text=clean_title, duration_sec=info.get('duration', 15), url=url)
            add_log_to_history(task_id, "Đã trích xuất phụ đề Gốc thành công.")

        # Subfolder download name for Chrome: e.g. "BV1KS4y1i7zL/Title.mp4"
        download_name = f"{folder_name}/{clean_title}.{ext}"

        if os.path.exists(filename):
            file_basename = os.path.basename(filename)
            main_url = f"/api/get_file/{file_basename}?filename={requests.utils.quote(download_name)}"
            
            files = [{
                'url': main_url,
                'filename': download_name,
                'type': 'video'
            }]

            if orig_sub and os.path.exists(orig_sub):
                orig_basename = os.path.basename(orig_sub)
                orig_download_name = f"{folder_name}/{clean_title}.orig.srt"
                files.append({
                    'url': f"/api/get_file/{orig_basename}?filename={requests.utils.quote(orig_download_name)}",
                    'filename': orig_download_name,
                    'type': 'orig_sub'
                })

            add_or_update_history(
                task_id, status='COMPLETED', files=files,
                log_msg=f"✅ Thành công 100%! Đã tạo gói {len(files)} file hoàn chỉnh (Video + Sub Gốc)."
            )

            return jsonify({
                'success': True,
                'task_id': task_id,
                'file_url': main_url,
                'filename': download_name,
                'files': files
            })
        else:
            add_or_update_history(task_id, status='FAILED', error='Không tìm thấy file xuất ra.')
            return jsonify({'error': 'Tải video thất bại, không tìm thấy file xuất ra.'}), 500

    except Exception as e:
        if 'task_id' in locals():
            add_or_update_history(task_id, status='FAILED', error=str(e), log_msg=f"❌ Lỗi: {str(e)}")
        return jsonify({'error': f'Lỗi khi xử lý tải video: {str(e)}'}), 500

@app.route('/api/get_file/<filename>')
def get_file(filename):
    file_path = DOWNLOADS_DIR / filename
    custom_name = request.args.get('filename', filename)
    if file_path.exists():
        delayed_delete(file_path, delay=60)
        cleanup_old_files(max_age_seconds=180)
        return send_file(file_path, as_attachment=True, download_name=custom_name)
    cleanup_old_files(max_age_seconds=180)
    return Response("File not found", status=404)

@app.route('/api/history', methods=['GET'])
def get_history():
    history = get_all_history(limit=50)
    return jsonify({'success': True, 'history': history})

@app.route('/api/history/<task_id>', methods=['GET'])
def get_history_detail(task_id):
    item = get_history_item(task_id)
    if item:
        return jsonify({'success': True, 'item': item})
    return jsonify({'error': 'Không tìm thấy lịch sử.'}), 404

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    clear_all_history()
    return jsonify({'success': True, 'message': 'Đã xóa toàn bộ lịch sử tải.'})

@app.route('/history')
def history_page():
    return render_template('history.html')

if __name__ == '__main__':
    print("=" * 60)
    print("      DOWNLOADER WEB SERVER IS RUNNING      ")
    print("      Access at: http://127.0.0.1:5000         ")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
