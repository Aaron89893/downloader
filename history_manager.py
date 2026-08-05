import os
import json
import time
import threading
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.resolve() / "download_history.json"
_lock = threading.Lock()

def _load_history_raw():
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_history_raw(data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Lỗi khi ghi history.json: {e}")

def get_all_history(limit=50):
    with _lock:
        items = _load_history_raw()
        items.sort(key=lambda x: x.get('timestamp_raw', 0), reverse=True)
        return items[:limit]

def get_history_item(task_id):
    with _lock:
        items = _load_history_raw()
        for item in items:
            if item.get('id') == task_id:
                return item
        return None

def add_or_update_history(task_id, url=None, title=None, thumbnail=None, platform=None, status=None, quality=None, files=None, log_msg=None, error=None):
    with _lock:
        items = _load_history_raw()
        found = None
        for item in items:
            if item.get('id') == task_id:
                found = item
                break

        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        now_ts = time.time()

        if not found:
            # Identify platform if not provided
            if not platform and url:
                if 'tiktok.com' in url or 'douyin.com' in url: platform = 'TikTok/Douyin'
                elif 'youtube.com' in url or 'youtu.be' in url: platform = 'YouTube'
                elif 'bilibili.com' in url or 'b23.tv' in url: platform = 'Bilibili'
                else: platform = 'Video'

            found = {
                'id': task_id,
                'url': url or '',
                'title': title or 'Đang tải...',
                'thumbnail': thumbnail or '',
                'platform': platform or 'Video',
                'quality': quality or '1080p',
                'status': status or 'DOWNLOADING',
                'timestamp': now_str,
                'timestamp_raw': now_ts,
                'files': files or [],
                'logs': [f"[{now_str}] Bắt đầu xử lý tải URL: {url}"] if url else [],
                'error': error
            }
            items.append(found)
        else:
            if url: found['url'] = url
            if title: found['title'] = title
            if thumbnail: found['thumbnail'] = thumbnail
            if platform: found['platform'] = platform
            if quality: found['quality'] = quality
            if status: found['status'] = status
            if files: found['files'] = files
            if error: found['error'] = error

            if log_msg:
                if 'logs' not in found or not isinstance(found['logs'], list):
                    found['logs'] = []
                found['logs'].append(f"[{now_str}] {log_msg}")

        # Keep top 100 history items
        items.sort(key=lambda x: x.get('timestamp_raw', 0), reverse=True)
        items = items[:100]
        _save_history_raw(items)
        return found

def add_log_to_history(task_id, log_msg):
    add_or_update_history(task_id, log_msg=log_msg)

def clear_all_history():
    with _lock:
        _save_history_raw([])
