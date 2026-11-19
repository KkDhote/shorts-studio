#!/usr/bin/env python3
"""
Batch Pipeline Runner for Prompt 2 (Wynnsanity GTA 6 Live Premiere).
Ingests 4 highlighted moments, transcribes with word timestamps,
tracks framing at 60fps, renders viral karaoke captions, and dynamically
allocates next available 2-shorts-per-day slots.
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
        "id": "clip_13",
        "name": "Prison Prologue Lucia",
        "start_sec": 1732,
        "end_sec": 1785,
        "clip_window": (5.0, 46.0), # 41s
        "title": "GTA 6 Prison Prologue: Meeting Lucia in Leonida! ⛓️🔥",
        "description": "The opening prison sequence of GTA VI introducing protagonist Lucia Caminos!\n\n#GTA6 #Wynnsanity #LuciaGTA6 #Shorts #GTAVI",
        "tags": ["GTA6", "Wynnsanity", "LuciaGTA6", "Shorts", "GTA VI", "Leonida"],
        "pinned_comment": "⛓️ Lucia's backstory is already legendary! Who are you more excited to play as: Lucia or Jason?"
    },
    {
        "id": "clip_14",
        "name": "Heist & Police Escape",
        "start_sec": 2014,
        "end_sec": 2070,
        "clip_window": (5.0, 46.0), # 41s
        "title": "Wynnsanity GTA 6 Store Robbery & INSANE Police Escape! 🚨🔫",
        "description": "Adrenaline-fueled store robbery and intense police evasion in GTA VI!\n\n#GTA6Gameplay #WynnsanityLive #PoliceChase #Shorts #GTA6",
        "tags": ["GTA6Gameplay", "WynnsanityLive", "PoliceChase", "Shorts", "GTA6"],
        "pinned_comment": "🚨 The new 5-star police AI in GTA 6 doesn't mess around! Drop a like!"
    },
    {
        "id": "clip_15",
        "name": "Bayou Boat Navigation",
        "start_sec": 2365,
        "end_sec": 2420,
        "clip_window": (5.0, 45.0), # 40s
        "title": "Navigating the Dangerous Leonida Bayous in GTA 6! 🚤🐊",
        "description": "Jason and Lucia navigate through the murky bayous and wetlands in GTA VI!\n\n#GTA6Bayous #Wynnsanity #GrandTheftAuto6 #Shorts #Gaming",
        "tags": ["GTA6Bayous", "Wynnsanity", "GrandTheftAuto6", "Shorts", "Gaming"],
        "pinned_comment": "🐊 The wildlife and swamp environmental details are unreal! What do you think?"
    },
    {
        "id": "clip_16",
        "name": "Crime Partnership Narrative",
        "start_sec": 3402,
        "end_sec": 3460,
        "clip_window": (5.0, 46.0), # 41s
        "title": "Lucia & Jason Secret Meeting with Vice City Cartel! 🤝💥",
        "description": "Lucia and Jason deepen their criminal partnership with Vice City contacts.\n\n#GTA6Story #LuciaAndJason #WynnsanityMoments #Shorts #GTA6",
        "tags": ["GTA6Story", "LuciaAndJason", "WynnsanityMoments", "Shorts", "GTA6"],
        "pinned_comment": "🤝 Bonnie and Clyde vibes in Vice City! Subscribe for daily GTA VI Shorts!"
    }
]

STREAM_URL = "https://www.youtube.com/live/hQAHI7aD1Dk"

def run_step(desc, cmd):
    print(f"\n--- [STEP] {desc} ---", flush=True)
    start = time.time()
    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        print(f"Error in step '{desc}': exited with code {res.returncode}", file=sys.stderr, flush=True)
        sys.exit(res.returncode)
    print(f"Completed '{desc}' in {time.time() - start:.1f}s", flush=True)

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
                "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
                "--merge-output-format", "mp4",
                "--extractor-args", "youtube:player_client=android,web",
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

    # Automatically allocate next open 2-shorts-per-day slots!
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
