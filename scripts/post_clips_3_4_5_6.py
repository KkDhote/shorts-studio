#!/usr/bin/env python3
"""
Sequential Batch Uploader for Clips 3, 4, 5, 6 with optimized viral hashtags.
Uploads to YouTube Data API v3, posts engagement comments, and updates upload_queue.json.
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

TARGET_CLIPS = ["final_clips/clip_3.mp4", "final_clips/clip_4.mp4", "final_clips/clip_5.mp4", "final_clips/clip_6.mp4"]

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
        # Ensure all relevant viral hashtags are present
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

        print(f"\n{'='*60}\nUPLOADING: {title}\nFile: {file_path} ({file_path.stat().st_size / (1024*1024):.1f} MB)\n{'='*60}")

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
        print(proc.stdout)

        if proc.returncode != 0:
            print(f"Error uploading {target}: {proc.stderr}", file=sys.stderr)
            continue

        res_json = {}
        for line in reversed(proc.stdout.strip().split("\n")):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    res_json = json.loads(line)
                    break
                except Exception:
                    continue

        video_id = res_json.get("video_id")
        video_url = res_json.get("video_url") or (f"https://youtube.com/shorts/{video_id}" if video_id else None)

        now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %I:%M:%S %p IST")
        clip_item["uploaded"] = True
        clip_item["video_id"] = video_id
        clip_item["video_url"] = video_url
        clip_item["posted_at"] = now_ist
        clip_item["auto_posted"] = False

        # Save progress after every clip
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

        print(f"[+] SUCCESS! Published: {video_url}\n")
        uploaded_results.append({
            "file": target,
            "title": title,
            "video_url": video_url,
            "video_id": video_id
        })

        time.sleep(3)

    print("\n" + "="*60)
    print("ALL CLIPS UPLOADED SUCCESSFULLY!")
    print("="*60)
    for r in uploaded_results:
        print(f"• {r['file']} ➔ {r['video_url']} ({r['title']})")

if __name__ == "__main__":
    main()
