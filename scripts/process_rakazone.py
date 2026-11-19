#!/usr/bin/env python3
"""
Batch Pipeline Runner for Prompt 2 (RakaZone Gaming GTA 6 Live Stream).
Ingests 4 highlighted moments, transcribes with word timestamps,
tracks framing at 60fps, renders viral karaoke captions, dynamically
allocates 3-shorts-per-day slots, updates sources registry, and cleans temp_work.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["PATH"] = str(BASE_DIR / "bin") + os.pathsep + os.environ.get("PATH", "")
TEMP_DIR = BASE_DIR / "temp_work"
FINAL_DIR = BASE_DIR / "final_clips"
PYTHON_EXE = sys.executable

sys.path.insert(0, str(BASE_DIR))
from scripts.auto_scheduler import allocate_slots_for_new_clips

MOMENTS = [
    {
        "id": "clip_17",
        "name": "Vice City Intro & Welcome",
        "start_sec": 90,
        "end_sec": 140,
        "clip_window": (4.0, 44.0), # 40s
        "title": "RakaZone Experiences GTA 6 Vice City for the First Time! 🌆🤯",
        "description": "RakaZone Gaming first look at Vice City and next-gen Leonida graphics in GTA VI!\n\n#GTA6 #RakaZoneGaming #ViceCity #GTA6Graphics #Shorts",
        "tags": ["GTA6", "RakaZoneGaming", "ViceCity", "GTA6Graphics", "Shorts", "GTA VI"],
        "pinned_comment": "🌆 The lighting and environment in Vice City look unreal! Drop a like if you're hyped!"
    },
    {
        "id": "clip_18",
        "name": "RakaZone Streamer Funny Reaction",
        "start_sec": 460,
        "end_sec": 505,
        "clip_window": (4.0, 44.0), # 40s
        "title": "RakaZone's Funniest Moments in GTA 6 Live Stream! 😂🔥",
        "description": "Hilarious live stream reactions and viewer interactions with RakaZone Gaming in GTA 6!\n\n#GTA6Live #RakaZone #FunnyMoments #Shorts #GTAVI",
        "tags": ["GTA6Live", "RakaZone", "FunnyMoments", "Shorts", "GTAVI"],
        "pinned_comment": "😂 RakaZone's stream energy never fails! Subscribe for daily GTA VI Shorts!"
    },
    {
        "id": "clip_19",
        "name": "Cinematic Narrative Cutscene",
        "start_sec": 1665,
        "end_sec": 1710,
        "clip_window": (4.0, 45.0), # 41s
        "title": "GTA 6 Story Mode INSANE Cinematic Cutscene! 🎬💥",
        "description": "Key cinematic scene showcasing the dark storyline and character dynamics of Vice City in GTA VI!\n\n#GTA6Story #RakaZoneGaming #Cinematic #Shorts #GTA6",
        "tags": ["GTA6Story", "RakaZoneGaming", "Cinematic", "Shorts", "GTA6"],
        "pinned_comment": "🎬 Rockstar storytelling at its peak! What are your theories on the storyline?"
    },
    {
        "id": "clip_20",
        "name": "High Stakes Mission Sequence",
        "start_sec": 2410,
        "end_sec": 2455,
        "clip_window": (4.0, 45.0), # 41s
        "title": "GTA 6 High-Stakes Mission & Vice City Underworld! 🚨🔫",
        "description": "Intense gameplay sequence demonstrating missions and action mechanics in GTA VI!\n\n#GTA6Gameplay #RakaZone #GTA6Combat #Shorts #Gaming",
        "tags": ["GTA6Gameplay", "RakaZone", "GTA6Combat", "Shorts", "Gaming"],
        "pinned_comment": "🚨 Vice City action is heating up! Drop a comment if you're playing GTA VI day one!"
    }
]

STREAM_URL = "https://www.youtube.com/watch?v=GCkc4t1ZWYs"

def run_step(desc, cmd):
    print(f"\n--- [STEP] {desc} ---", flush=True)
    start = time.time()
    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        print(f"Error in step '{desc}': exited with code {res.returncode}", file=sys.stderr, flush=True)
        sys.exit(res.returncode)
    print(f"Completed '{desc}' in {time.time() - start:.1f}s", flush=True)

def update_sources_registry():
    sources_path = FINAL_DIR / "sources_registry.json"
    sources = []
    if sources_path.exists():
        try:
            with open(sources_path, "r", encoding="utf-8") as f:
                sources = json.load(f)
        except Exception:
            sources = []

    exists = any(s.get("video_id") == "GCkc4t1ZWYs" for s in sources)
    if not exists:
        new_source = {
            "id": f"source_{len(sources) + 1}",
            "creator_name": "RakaZone Gaming",
            "channel_handle": "@RakaZoneGaming",
            "channel_url": "https://www.youtube.com/@RakaZoneGaming",
            "subscribers": "536K Subscribers",
            "video_title": "GTA 6 Gameplay Walkthrough Part 1 Live Stream India & Giveaways",
            "video_url": STREAM_URL,
            "video_id": "GCkc4t1ZWYs",
            "thumbnail": "https://i.ytimg.com/vi/GCkc4t1ZWYs/hqdefault.jpg",
            "duration": "10h 51m",
            "clips_count": 4,
            "clips": ["clip_17.mp4", "clip_18.mp4", "clip_19.mp4", "clip_20.mp4"],
            "attribution_status": "Credited in Description (#RakaZoneGaming)"
        }
        sources.append(new_source)
        with open(sources_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
        print("[+] Updated sources_registry.json with RakaZone Gaming!", flush=True)

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for idx, m in enumerate(MOMENTS):
        clip_id = m["id"]
        raw_mp4 = TEMP_DIR / f"raw_{clip_id}.mp4"
        trans_json = TEMP_DIR / f"transcript_{clip_id}.json"
        crop_mp4 = TEMP_DIR / f"crop_{clip_id}.mp4"
        final_mp4 = FINAL_DIR / f"{clip_id}.mp4"

        print(f"\n{'='*60}\nPROCESSING [{idx+1}/4]: {m['name']} ({clip_id})\n{'='*60}", flush=True)

        # 1. Download slice via yt-dlp
        if not raw_mp4.exists():
            cmd_dl = [
                PYTHON_EXE, "-m", "yt_dlp",
                "--ffmpeg-location", str(BASE_DIR / "bin"),
                "--download-sections", f"*{m['start_sec']}-{m['end_sec']}",
                "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "--merge-output-format", "mp4",
                "-o", str(raw_mp4),
                STREAM_URL
            ]
            run_step(f"Download section {m['start_sec']}-{m['end_sec']}", cmd_dl)

        # 2. Transcribe word-level
        if not trans_json.exists():
            cmd_trans = [
                PYTHON_EXE, "scripts/transcribe.py",
                "-i", str(raw_mp4),
                "-o", str(trans_json),
                "--model", "base"
            ]
            run_step(f"Transcribe {clip_id}", cmd_trans)

        # 3. Smart Crop at 60 FPS
        start_w, end_w = m["clip_window"]
        if not crop_mp4.exists():
            cmd_crop = [
                PYTHON_EXE, "scripts/smart_crop.py",
                "-i", str(raw_mp4),
                "-o", str(crop_mp4),
                "-s", str(start_w),
                "-e", str(end_w),
                "--framing", "auto",
                "--fps", "60"
            ]
            run_step(f"Smart Crop {clip_id} @ 60fps", cmd_crop)

        # 4. Render Captions
        cmd_caps = [
            PYTHON_EXE, "scripts/render_captions.py",
            "-i", str(crop_mp4),
            "-t", str(trans_json),
            "-o", str(final_mp4),
            "-s", str(start_w),
            "-e", str(end_w),
            "--fps", "60"
        ]
        run_step(f"Render Karaoke Captions {clip_id}", cmd_caps)

        results.append({
            "file": f"final_clips/{clip_id}.mp4",
            "title": m["title"],
            "description": m["description"],
            "tags": m["tags"],
            "privacy": "public",
            "category": "20",
            "uploaded": False,
            "pinned_comment": m["pinned_comment"]
        })

    # Automatically allocate next open 3-shorts-per-day slots!
    queue_path = FINAL_DIR / "upload_queue.json"
    queue = []
    if queue_path.exists():
        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

    # Allocate slots dynamically
    allocated_clips = allocate_slots_for_new_clips(results, queue_path)
    for c in allocated_clips:
        queue.append(c)

    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

    print("\n[+] Successfully auto-scheduled 4 new clips into upload_queue.json!", flush=True)

    # Update sources registry
    update_sources_registry()

    # Ephemeral cleanup of temp_work
    for item in TEMP_DIR.glob("*"):
        try:
            if item.is_file():
                item.unlink()
        except Exception:
            pass
    print("[+] Wiped temp_work/ clean.", flush=True)

if __name__ == "__main__":
    main()
