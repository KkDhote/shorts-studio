#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
QUEUE_FILE = BASE_DIR / "final_clips" / "upload_queue.json"

with open(QUEUE_FILE, "r", encoding="utf-8") as f:
    queue = json.load(f)

clip_item = None
for item in queue:
    if item.get("file") == "final_clips/clip_2.mp4":
        clip_item = item
        break

if not clip_item:
    print("clip_2.mp4 not found in queue!")
    sys.exit(1)

title = clip_item.get("title", "INSANE 5-Star Boat Escape in GTA 6 Waterways! 🚤💨 #shorts")
desc = clip_item.get("description", "")
affiliate = clip_item.get("affiliate_deal", "")
if affiliate and affiliate not in desc:
    desc += f"\n\n⚡ Exclusive Deal: {affiliate}"

tags = clip_item.get("tags", ["GTA6Gameplay", "CarryMinatiLive", "BoatChase", "GTA6Shorts", "Shorts"])
privacy = clip_item.get("privacy", "public")

cmd = [
    sys.executable,
    str(BASE_DIR / "scripts" / "upload_youtube.py"),
    "-i", str(BASE_DIR / "final_clips" / "clip_2.mp4"),
    "-t", title,
    "-d", desc,
    "--tags", ",".join(tags) if isinstance(tags, list) else tags,
    "-p", privacy
]

print(f"Uploading clip_2.mp4 to YouTube Channel KULDEEPBHAI GAMER...")
proc = subprocess.run(cmd, capture_output=True, text=True)
print(proc.stdout)
if proc.returncode != 0:
    print(f"Upload failed: {proc.stderr}", file=sys.stderr)
    sys.exit(proc.returncode)

# Parse output json
res_json = {}
for line in proc.stdout.strip().split("\n"):
    try:
        res_json = json.loads(line)
        break
    except Exception:
        continue

video_url = res_json.get("video_url")
video_id = res_json.get("video_id")
print(f"\n🎉 Successfully published to YouTube: {video_url}")

# Update upload_queue.json
now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %I:%M:%S %p IST")
clip_item["uploaded"] = True
clip_item["video_id"] = video_id
clip_item["video_url"] = video_url
clip_item["posted_at"] = now_ist
clip_item["auto_posted"] = False

with open(QUEUE_FILE, "w", encoding="utf-8") as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

print(f"Updated upload_queue.json with live YouTube link.")
