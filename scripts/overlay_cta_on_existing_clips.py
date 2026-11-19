#!/usr/bin/env python3
"""
Adds visual Subscribe and Comment overlay badge to all unposted Shorts in final_clips.
- Adds Top Pill badge: 🔔 SUBSCRIBE & COMMENT 👇
- Adds Outro CTA (final 4.5s): 🔔 SUBSCRIBE FOR DAILY GTA 6! 💬 DROP A COMMENT BELOW 👇
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "final_clips"
TEMP_DIR = BASE_DIR / "temp_work"
FFMPEG = str(BASE_DIR / "bin" / "ffmpeg.exe")
FFPROBE = str(BASE_DIR / "bin" / "ffprobe.exe")

def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def get_duration(video_path: Path) -> float:
    cmd = [
        FFPROBE, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 35.0

def process_clip(clip_path: Path):
    duration = get_duration(clip_path)
    if duration <= 2.0:
        return

    cta_start = "0:00:00.50"
    cta_end = format_ass_time(duration)
    outro_start = format_ass_time(max(0.0, duration - 4.5))

    ass_content = f"""[Script Info]
Title: Viral Shorts CTA Overlay
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopPill,Arial Black,34,&H00FFFFFF&,&H0000D7FF&,&H00000000&,&H90000000&,-1,0,0,0,100,100,1,0,1,4,2,8,40,40,160,1
Style: OutroCTA,Arial Black,52,&H0000D7FF&,&H00FFFFFF&,&H00000000&,&HA0000000&,-1,0,0,0,108,108,2,0,1,6,4,2,50,50,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,{cta_start},{cta_end},TopPill,,0,0,0,,{{\\bord4\\shad2\\c&H00D7FF&}}🔔 SUBSCRIBE {{\\c&H00FFFFFF&}}& {{\\c&H00D7FF&}}COMMENT 👇
Dialogue: 2,{outro_start},{cta_end},OutroCTA,,0,0,0,,{{\\an2\\pos(540,1400)\\bord5\\shad3\\c&H00D7FF&}}🔔 SUBSCRIBE FOR DAILY GTA 6!\\N{{\\fs40\\c&H00FFFFFF&}}💬 DROP A COMMENT BELOW 👇
"""

    ass_file = TEMP_DIR / f"cta_{clip_path.stem}.ass"
    ass_file.write_text(ass_content, encoding="utf-8")

    temp_out = TEMP_DIR / f"cta_out_{clip_path.name}"

    cmd = [
        FFMPEG, "-y",
        "-i", str(clip_path),
        "-vf", f"subtitles={ass_file.name}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy",
        str(temp_out)
    ]

    res = subprocess.run(cmd, cwd=str(ass_file.parent), capture_output=True, text=True)
    if res.returncode == 0 and temp_out.exists() and temp_out.stat().st_size > 1000000:
        # Atomic replace
        temp_out.replace(clip_path)
        print(f"[+] Added visual Subscribe & Comment badge to {clip_path.name}!", flush=True)
    else:
        print(f"[!] Warning: Failed to process {clip_path.name}: {res.stderr}", file=sys.stderr)

    # Clean up temp ass
    try:
        ass_file.unlink(missing_ok=True)
    except Exception:
        pass

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    queue_path = FINAL_DIR / "upload_queue.json"
    if not queue_path.exists():
        print("upload_queue.json not found!")
        return

    with open(queue_path, "r", encoding="utf-8") as f:
        queue = json.load(f)

    # Filter unposted clips
    unposted_files = [Path(item["file"]) for item in queue if not item.get("uploaded", False)]

    print(f"Found {len(unposted_files)} unposted clips to process with Subscribe & Comment visual overlays.")

    for idx, p in enumerate(unposted_files, 1):
        full_path = BASE_DIR / p
        if full_path.exists() and full_path.stat().st_size > 1000000:
            print(f"[{idx}/{len(unposted_files)}] Processing {full_path.name}...")
            process_clip(full_path)
        else:
            print(f"[{idx}/{len(unposted_files)}] Skipping {p.name} (not yet rendered or not found).")

    print("\n✅ All existing unposted clips updated with visual Subscribe & Comment overlays!")

if __name__ == "__main__":
    main()
