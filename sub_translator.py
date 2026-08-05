import os
import re
import sys
import json
import zlib
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

def format_srt_time(seconds):
    """Convert seconds float to SRT timestamp string '00:01:10,078'"""
    millis = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"

def convert_danmaku_xml_to_srt(xml_path, output_orig=None):
    """Convert Bilibili danmaku.xml to Original SRT instantly"""
    path = Path(xml_path)
    if not path.exists():
        return None

    stem = path.stem.replace('.danmaku', '')
    if not output_orig:
        output_orig = path.with_name(f"{stem}.orig.srt")

    try:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            root = ET.fromstring(content)
        except Exception:
            with open(path, "rb") as f:
                raw = f.read()
            text = None
            for wbits in [-15, 15 + 16, 15]:
                try:
                    text = zlib.decompress(raw, wbits).decode('utf-8', errors='ignore')
                    break
                except Exception:
                    pass
            if not text:
                text = raw.decode('utf-8', errors='ignore')
            root = ET.fromstring(text)

        items = []
        for d in root.findall('d'):
            p_attr = d.attrib.get('p', '')
            text = (d.text or '').strip()
            if not p_attr or not text:
                continue
            parts = p_attr.split(',')
            if parts and parts[0]:
                try:
                    start_sec = float(parts[0])
                    items.append((start_sec, text))
                except ValueError:
                    pass

        items.sort(key=lambda x: x[0])
        if not items:
            return None

        # Write Original SRT
        orig_blocks = []
        for idx, (start_sec, text) in enumerate(items, start=1):
            t_start = format_srt_time(start_sec)
            t_end = format_srt_time(start_sec + 3.5)
            orig_blocks.append(f"{idx}\n{t_start} --> {t_end}\n{text}")

        with open(output_orig, "w", encoding="utf-8") as f:
            f.write("\n\n".join(orig_blocks))
        print(f"[✓] Đã tạo file Phụ Đề Gốc ({len(items)} dòng) từ Danmaku XML: {output_orig.name}")

        return str(output_orig)

    except Exception as e:
        print(f"[❌] Lỗi khi chuyển đổi Danmaku XML: {e}")
        return None

def fetch_bilibili_danmaku_srt(bvid, output_orig):
    """Fetch Bilibili danmaku XML directly from Bilibili comment API and convert to SRT"""
    try:
        url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
        
        cid = data['data'][0]['cid']
        xml_url = f"https://comment.bilibili.com/{cid}.xml"
        req_xml = urllib.request.Request(xml_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req_xml, timeout=10) as res_xml:
            raw = res_xml.read()

        text = None
        for wbits in [-15, 15 + 16, 15]:
            try:
                text = zlib.decompress(raw, wbits).decode('utf-8', errors='ignore')
                break
            except Exception:
                pass

        if not text:
            text = raw.decode('utf-8', errors='ignore')

        root = ET.fromstring(text)
        items = []
        for d in root.findall('d'):
            p_attr = d.attrib.get('p', '')
            txt = (d.text or '').strip()
            if not p_attr or not txt:
                continue
            parts = p_attr.split(',')
            if parts and parts[0]:
                try:
                    start_sec = float(parts[0])
                    items.append((start_sec, txt))
                except ValueError:
                    pass

        items.sort(key=lambda x: x[0])
        if not items:
            return None

        orig_blocks = []
        for idx, (start_sec, txt) in enumerate(items, start=1):
            t_start = format_srt_time(start_sec)
            t_end = format_srt_time(start_sec + 3.5)
            orig_blocks.append(f"{idx}\n{t_start} --> {t_end}\n{txt}")

        with open(output_orig, "w", encoding="utf-8") as f:
            f.write("\n\n".join(orig_blocks))
        print(f"[✓] Đã fetch thành công {len(items)} câu phụ đề Danmaku Bilibili: {Path(output_orig).name}")
        return str(output_orig)
    except Exception as e:
        print(f"[!] Không thể fetch Danmaku Bilibili API: {e}")
        return None

def convert_vtt_to_srt(vtt_path, output_orig=None):
    """Convert VTT subtitle file (YouTube) to Original SRT format"""
    path = Path(vtt_path)
    if not path.exists():
        return None

    stem = path.stem
    stem_clean = re.sub(r'\.(en|vi|zh|zh-Hans|zh-Hant|ja|ko|es|fr|de|ru|id)$', '', stem, flags=re.IGNORECASE)
    if not output_orig:
        output_orig = path.with_name(f"{stem_clean}.orig.srt")

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
        content = re.sub(r'NOTE.*?\n\n', '', content, flags=re.DOTALL)
        content = re.sub(r'STYLE.*?\n\n', '', content, flags=re.DOTALL)
        content = re.sub(r'<\/?c[^>]*>', '', content)
        content = re.sub(r'<\d+:\d+:\d+\.\d+>', '', content)

        blocks = re.split(r'\n\s*\n', content.strip())
        srt_blocks = []
        block_idx = 1

        for block in blocks:
            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
            if not lines:
                continue

            time_line_idx = -1
            for i, line in enumerate(lines):
                if '-->' in line:
                    time_line_idx = i
                    break

            if time_line_idx != -1:
                raw_time = lines[time_line_idx]
                time_part = raw_time.split('align:')[0].split('position:')[0].split('line:')[0].strip()
                srt_time = re.sub(r'(\d+:\d+:\d+)[\.,](\d+)', r'\1,\2', time_part)
                srt_time = re.sub(r'(\d+:\d+)[\.,](\d+)', r'00:\1,\2', srt_time)

                text_lines = lines[time_line_idx + 1:]
                clean_text = " ".join(text_lines).strip()
                clean_text = re.sub(r'<[^>]+>', '', clean_text)

                if clean_text:
                    srt_blocks.append(f"{block_idx}\n{srt_time}\n{clean_text}")
                    block_idx += 1

        if srt_blocks:
            with open(output_orig, "w", encoding="utf-8") as f:
                f.write("\n\n".join(srt_blocks))
            print(f"[✓] Đã tạo file Phụ Đề Gốc ({len(srt_blocks)} dòng) từ VTT: {output_orig.name}")
            return str(output_orig)

    except Exception as e:
        print(f"[!] Lỗi khi chuyển VTT sang SRT: {e}")

    return None

def create_fallback_srt(video_path, title_text="Video Subtitle", duration_sec=15):
    """Generate a clean multi-block SRT subtitle file for videos without native subtitles (Douyin / TikTok)"""
    v_path = Path(video_path)
    if not v_path.exists():
        return None

    base_stem = v_path.stem
    output_orig = v_path.with_name(f"{base_stem}.orig.srt")

    try:
        duration = float(duration_sec or 15.0)
        if duration <= 0:
            duration = 15.0

        raw_chunks = re.split(r'[\n\r\_\.\!\?\,\;\:\s]+', str(title_text or '').strip())
        chunks = [c.strip() for c in raw_chunks if c.strip()]

        if not chunks:
            chunks = ["Douyin/TikTok Video Subtitle"]

        if len(chunks) > 30:
            chunks = chunks[:30]

        step = duration / len(chunks)
        srt_blocks = []

        for idx, chunk in enumerate(chunks, start=1):
            t_start_sec = (idx - 1) * step
            t_end_sec = idx * step
            t_start = format_srt_time(t_start_sec)
            t_end = format_srt_time(t_end_sec)
            srt_blocks.append(f"{idx}\n{t_start} --> {t_end}\n{chunk}")

        with open(output_orig, "w", encoding="utf-8") as f:
            f.write("\n\n".join(srt_blocks))
        print(f"[✓] Đã tạo file Phụ Đề Gốc Multi-block ({len(chunks)} câu) cho Douyin/TikTok: {output_orig.name}")
        return str(output_orig)

    except Exception as e:
        print(f"[!] Lỗi khi tạo fallback SRT: {e}")
        return None

def process_all_subtitles(video_path, title_text=None, duration_sec=15, url=None):
    """Process video subtitles across Bilibili, YouTube, Douyin, and TikTok. Always returns a valid .orig.srt path."""
    v_path = Path(video_path)
    if not v_path.exists():
        return None

    base_stem = v_path.stem
    parent_dir = v_path.parent
    target_orig_file = v_path.with_name(f"{base_stem}.orig.srt")

    # Clean up any old small fallback file from previous test runs so we always generate fresh subtitles
    if target_orig_file.exists() and target_orig_file.stat().st_size <= 300:
        try:
            target_orig_file.unlink()
        except Exception:
            pass

    # 1. Bilibili API Fetch (If BV ID is in URL or filename)
    bv_match = None
    if url:
        bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
    if not bv_match:
        bv_match = re.search(r'(BV[a-zA-Z0-9]+)', base_stem)

    if bv_match:
        bvid = bv_match.group(1)
        fetched = fetch_bilibili_danmaku_srt(bvid, target_orig_file)
        if fetched and Path(fetched).exists() and Path(fetched).stat().st_size > 300:
            return str(target_orig_file)

    # 2. Process XML danmaku if present (Bilibili local file)
    xml_files = list(parent_dir.glob(f"{base_stem}*.xml"))
    for xml_f in xml_files:
        o = convert_danmaku_xml_to_srt(xml_f, output_orig=target_orig_file)
        if o and Path(o).exists() and Path(o).stat().st_size > 300:
            return str(target_orig_file)

    # 3. Process VTT files if present (YouTube)
    vtt_files = list(parent_dir.glob(f"{base_stem}*.vtt"))
    for vtt_f in vtt_files:
        o = convert_vtt_to_srt(vtt_f, output_orig=target_orig_file)
        if o and Path(o).exists() and Path(o).stat().st_size > 300:
            return str(target_orig_file)

    # 4. Process existing SRT files if present (excluding target_orig_file itself)
    srt_files = list(parent_dir.glob(f"{base_stem}*.srt"))
    for srt_f in srt_files:
        if srt_f != target_orig_file and srt_f.stat().st_size > 300:
            try:
                shutil.copy(srt_f, target_orig_file)
                return str(target_orig_file)
            except Exception:
                pass

    # 5. Multi-block SRT for Douyin / TikTok / Short Videos without explicit closed-caption tracks
    created_orig = create_fallback_srt(video_path, title_text=title_text, duration_sec=duration_sec)
    return created_orig
