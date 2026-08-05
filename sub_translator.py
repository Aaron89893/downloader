import os
import re
import sys
import json
import zlib
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
    """Generate a clean fallback SRT subtitle file for videos without native subtitles (Douyin / TikTok)"""
    v_path = Path(video_path)
    if not v_path.exists():
        return None

    base_stem = v_path.stem
    output_orig = v_path.with_name(f"{base_stem}.orig.srt")

    try:
        t_start = format_srt_time(0.0)
        t_end = format_srt_time(float(duration_sec or 15.0))
        text = title_text if title_text else "Douyin/TikTok Video Subtitle"

        srt_content = f"1\n{t_start} --> {t_end}\n{text}\n"

        with open(output_orig, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"[✓] Đã tạo file Phụ Đề Gốc Fallback (Douyin/TikTok): {output_orig.name}")
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

    xml_files = list(parent_dir.glob(f"{base_stem}*.xml"))
    vtt_files = list(parent_dir.glob(f"{base_stem}*.vtt"))
    srt_files = list(parent_dir.glob(f"{base_stem}*.srt"))

    created_orig = None

    # 1. Process XML danmaku if present (Bilibili local file)
    for xml_f in xml_files:
        o = convert_danmaku_xml_to_srt(xml_f)
        if o:
            created_orig = o
            break

    # 2. Process VTT files if present (YouTube)
    if not created_orig:
        for vtt_f in vtt_files:
            o = convert_vtt_to_srt(vtt_f)
            if o:
                created_orig = o
                break

    # 3. Process existing SRT files if present
    if not created_orig:
        for srt_f in srt_files:
            if not srt_f.name.endswith('.orig.srt'):
                orig_file = srt_f.with_name(f"{base_stem}.orig.srt")
                if not orig_file.exists():
                    srt_f.rename(orig_file)
                created_orig = str(orig_file)
                break
            elif srt_f.stat().st_size > 200:
                created_orig = str(srt_f)
                break

    # 4. Check if this is a Bilibili video (BV id in filename or url) and fetch 400+ Danmaku comments from Bilibili API
    bv_match = None
    if url:
        bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
    if not bv_match:
        bv_match = re.search(r'(BV[a-zA-Z0-9]+)', base_stem)

    if not created_orig or (Path(created_orig).exists() and Path(created_orig).stat().st_size <= 200 and bv_match):
        if bv_match:
            bvid = bv_match.group(1)
            target_srt = v_path.with_name(f"{base_stem}.orig.srt")
            fetched = fetch_bilibili_danmaku_srt(bvid, target_srt)
            if fetched:
                created_orig = fetched

    # 5. Fallback: Generate clean SRT for platforms without caption tracks (Douyin / TikTok / Short Videos)
    if not created_orig or not Path(created_orig).exists():
        created_orig = create_fallback_srt(video_path, title_text=title_text, duration_sec=duration_sec)

    return created_orig
