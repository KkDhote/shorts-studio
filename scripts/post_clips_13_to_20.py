#!/usr/bin/env python3
"""
Sequential Batch Uploader for Clips 13 through 20 to YouTube Shorts (KULDEEPBHAI GAMER).
Uploads to YouTube Data API v3, records live video URLs, updates upload_queue.json,
and triggers Cloud Auto-Sync to Render.
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
    f"final_clips/clip_{i}.mp4" for i in range(13, 21)
]

def main():
    if not QUEUE_FILE.exists():
        print("Error: upload_queue.json not found!", file=sys.stderr)
        sys.exit(1)

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.load(f)

    uploaded_results = []

    print(f"\n{'='*70}\nSTARTING SEQUENTIAL PUBLICATION: CLIPS 13 TO 20 ON YOUTUBE\n{'='*70}", flush=True)

    for idx, target in enumerate(TARGET_CLIPS, 13):
        file_path = BASE_DIR / target
        if not file_path.exists():
            print(f"[!] Warning: File {file_path} not found! Skipping...")
            continue

        clip_item = None
        for item in queue:
            if item.get("file") == target:
                clip_item = item
                break

        if not clip_item:
            print(f"[!] Warning: {target} not found in upload_queue.json! Skipping...")
            continue

        if clip_item.get("uploaded"):
            print(f"[*] {target} already uploaded at {clip_item.get('video_url')}. Skipping.")
            uploaded_results.append({
                "clip_num": idx,
                "file": target,
                "title": clip_item.get("title"),
                "video_url": clip_item.get("video_url"),
                "video_id": clip_item.get("video_id")
            })
            continue

        raw_title = clip_item.get("title", "")
        if "#shorts" not in raw_title.lower():
            title = f"{raw_title.strip()} #shorts"
        else:
            title = raw_title.strip()

        if len(title) > 100:
            title = title[:97] + "..."

        desc = clip_item.get("description", "")
        extra_hashtags = "#shorts #GTA6 #GTAVI #GrandTheftAuto6 #Gaming #Trending #Viral"
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

        print(f"\n>>> [{idx}/20] UPLOADING: {title}", flush=True)
        print(f"    File: {file_path.name} ({file_path.stat().st_size / (1024*1024):.1f} MB)", flush=True)

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

        if proc.returncode != 0:
            print(f"[!] Error uploading {target}:\n{proc.stderr}\n{proc.stdout}", file=sys.stderr, flush=True)
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

        if not video_url:
            print(f"[!] Could not determine video_url for {target} from stdout:\n{proc.stdout}")
            continue

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
            "clip_num": idx,
            "file": target,
            "title": title,
            "video_url": video_url,
            "video_id": video_id
        })

        time.sleep(3)

    print("\n" + "="*70, flush=True)
    print("CLIPS 13 THROUGH 20 UPLOAD BATCH FINISHED!", flush=True)
    print("="*70, flush=True)
    for r in uploaded_results:
        print(f"• Clip #{r['clip_num']}: {r['video_url']} ➔ {r['title']}", flush=True)

    # Trigger Cloud Sync to Render
    try:
        from web.app import trigger_git_cloud_sync
        trigger_git_cloud_sync("Clips 13-20 published live to YouTube")
        print("[Auto-Sync] Triggered Git push & Render deployment for updated upload_queue.json!", flush=True)
    except Exception as e:
        print(f"[Auto-Sync] Note: {e}", flush=True)

if __name__ == "__main__":
    main()
