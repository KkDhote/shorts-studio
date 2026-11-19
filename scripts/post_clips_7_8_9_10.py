#!/usr/bin/env python3
"""
Sequential Batch Uploader for Clips 7, 8, 9, 10 with optimized viral hashtags.
Uploads to YouTube Data API v3, records live video URLs, and updates upload_queue.json.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
QUEUE_FILE = BASE_DIR / "final_clips" / "upload_queue.json"
UPLOADER_SCRIPT = BASE_DIR / "scripts" / "upload_youtube.py"
PYTHON_EXE = sys.executable

TARGET_CLIPS = [
    "final_clips/clip_7.mp4",
    "final_clips/clip_8.mp4",
    "final_clips/clip_9.mp4",
    "final_clips/clip_10.mp4"
]

def main():
    if not QUEUE_FILE.exists():
        print("Error: upload_queue.json not found!", file=sys.stderr)
        sys.exit(1)

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.load(f)

    uploaded_results = []

    for target in TARGET_CLIPS:
        clip_item = None
        for item in queue:
            if item.get("file") == target:
                clip_item = item
                break

        if not clip_item:
            print(f"Warning: {target} not found in queue! Skipping...")
            continue

        raw_title = clip_item.get("title", "")
        if "#shorts" not in raw_title.lower():
            title = f"{raw_title} #shorts"
        else:
            title = raw_title

        desc = clip_item.get("description", "")
        extra_hashtags = "#shorts #GTA6 #GTAVI #GrandTheftAuto6 #Gaming #Trending"
        for ht in extra_hashtags.split():
            if ht.lower() not in desc.lower():
                desc += f" {ht}"

        affiliate = clip_item.get("affiliate_deal", "")
        if affiliate and affiliate not in desc:
            desc += f"\n\n⚡ Exclusive Deal: {affiliate}"

        tags = clip_item.get("tags", ["Shorts", "GTA6", "Gaming"])
        for standard_tag in ["Shorts", "GTA6", "GTAVI", "Grand Theft Auto VI", "Gaming", "YouTube Shorts"]:
            if standard_tag not in tags:
                tags.append(standard_tag)

        privacy = clip_item.get("privacy", "public")
        file_path = BASE_DIR / target

        print(f"\n{'='*60}\nUPLOADING: {title}\nFile: {file_path} ({file_path.stat().st_size / (1024*1024):.1f} MB)\n{'='*60}", flush=True)

        cmd = [
            PYTHON_EXE,
            str(UPLOADER_SCRIPT),
            "-i", str(file_path),
            "-t", title,
            "-d", desc,
            "--tags", ",".join(tags),
            "-p", privacy
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        print(proc.stdout, flush=True)

        if proc.returncode != 0:
            print(f"Error uploading {target}: {proc.stderr}", file=sys.stderr, flush=True)
            continue

        video_id = None
        video_url = None

        # Parse output for Video URL or JSON
        for line in reversed(proc.stdout.strip().split("\n")):
            line = line.strip()
            if "Upload SUCCESS! Video URL: https://youtube.com/shorts/" in line:
                video_url = line.split("Video URL: ")[-1].strip()
                video_id = video_url.split("/")[-1].strip()
                break
            if line.startswith("{") and line.endswith("}"):
                try:
                    res_json = json.loads(line)
                    if res_json.get("video_id"):
                        video_id = res_json.get("video_id")
                        video_url = res_json.get("video_url")
                        break
                except Exception:
                    pass

        if not video_url and video_id:
            video_url = f"https://youtube.com/shorts/{video_id}"

        now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %I:%M:%S %p IST")
        clip_item["uploaded"] = True
        clip_item["video_id"] = video_id
        clip_item["video_url"] = video_url
        clip_item["posted_at"] = now_ist
        clip_item["auto_posted"] = False

        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

        print(f"[+] SUCCESS! Published: {video_url}\n", flush=True)
        uploaded_results.append({
            "file": target,
            "title": title,
            "video_url": video_url,
            "video_id": video_id
        })

        time.sleep(3)

    print("\n" + "="*60, flush=True)
    print("CLIPS 7, 8, 9, 10 UPLOADED SUCCESSFULLY!", flush=True)
    print("="*60, flush=True)
    for r in uploaded_results:
        print(f"• {r['file']} ➔ {r['video_url']} ({r['title']})", flush=True)

if __name__ == "__main__":
    main()
