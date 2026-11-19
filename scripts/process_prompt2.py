#!/usr/bin/env python3
"""
Batch Pipeline Runner for Prompt 2 (Mythpat GTA 6 Stream).
Ingests 4 highlighted moments, transcribes with word timestamps,
tracks framing at 60fps, renders viral karaoke captions, and queues for 2-shorts/day.
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

MOMENTS = [
    {
        "id": "clip_5",
        "name": "Store Robbery",
        "start_sec": 2117,
        "end_sec": 2211,
        "clip_window": (10.0, 50.0), # 40s window inside downloaded section
        "title": "Mythpat GTA 6 Convenience Store Robbery Gone Crazy! 🔫😂",
        "description": "Mythpat attempts a high-tension store robbery in GTA VI!\n\n#GTA6 #Mythpat #GamingShorts #Shorts #GTAVI",
        "tags": ["GTA6", "Mythpat", "GamingShorts", "Shorts", "GTA VI", "Lucia"],
        "pinned_comment": "😂 Mythpat's reactions in GTA 6 are unmatched! Subscribe for daily Shorts!"
    },
    {
        "id": "clip_6",
        "name": "Boat Chase Escape",
        "start_sec": 2300,
        "end_sec": 2335,
        "clip_window": (5.0, 31.0), # 26s full intense chase
        "title": "INSANE High Speed Boat Chase Escape in GTA 6! 🚤💥",
        "description": "Mythpat outruns the cops through Vice City waterways!\n\n#GTA6Gameplay #MythpatLive #BoatChase #Shorts #Gaming",
        "tags": ["GTA6Gameplay", "MythpatLive", "BoatChase", "Shorts", "Gaming"],
        "pinned_comment": "🚤 Best water physics in any game ever? What do you think?"
    },
    {
        "id": "clip_7",
        "name": "Swamp Shootout Combat",
        "start_sec": 3377,
        "end_sec": 3445,
        "clip_window": (5.0, 48.0), # 43s intense shootout
        "title": "INTENSE Swamp Shootout Gameplay in GTA 6! 🎯🔥",
        "description": "Mythpat survives a brutal shootout in the Leonida wetlands.\n\n#GTA6Combat #MythpatGTA #GrandTheftAuto6 #Shorts #Gaming",
        "tags": ["GTA6Combat", "MythpatGTA", "GrandTheftAuto6", "Shorts", "Gaming"],
        "pinned_comment": "🎯 That tactical cover system is next level! Drop a like!"
    },
    {
        "id": "clip_8",
        "name": "Plane Control Escape",
        "start_sec": 3454,
        "end_sec": 3530,
        "clip_window": (10.0, 52.0), # 42s plane takeoff
        "title": "Mythpat Takes Control of a Plane in GTA 6 Open World! ✈️🌊",
        "description": "Insane aerial escape over Leonida and Vice City with Mythpat!\n\n#GTA6Exfiltration #PlaneEscape #MythpatMoments #Shorts #Gaming",
        "tags": ["GTA6Exfiltration", "PlaneEscape", "MythpatMoments", "Shorts", "GTA6"],
        "pinned_comment": "✈️ Look at that draw distance! Drop a comment if you're hyped for GTA 6!"
    }
]

STREAM_URL = "https://www.youtube.com/live/LMbea5SozeM"

def run_step(desc, cmd):
    print(f"\n--- [STEP] {desc} ---")
    start = time.time()
    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        print(f"Error in step '{desc}': exited with code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)
    print(f"Completed '{desc}' in {time.time() - start:.1f}s")

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

        print(f"\n{'='*60}\nPROCESSING [{idx+1}/4]: {m['name']} ({clip_id})\n{'='*60}")

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
            "clip_id": clip_id,
            "name": m["name"],
            "file": f"final_clips/{clip_id}.mp4",
            "title": m["title"],
            "description": m["description"],
            "tags": m["tags"],
            "pinned_comment": m["pinned_comment"],
            "duration": round(end_w - start_w, 1)
        })

    # Update Queue manifest with 2-shorts-per-day schedule
    queue_path = FINAL_DIR / "upload_queue.json"
    queue = []
    if queue_path.exists():
        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

    # Schedule dates: Nov 21 & Nov 22
    schedule_slots = [
        ("Nov 21", "12:30 PM IST", "Day 3 - Afternoon Slot"),
        ("Nov 21", "07:30 PM IST", "Day 3 - Evening Golden Hour"),
        ("Nov 22", "12:30 PM IST", "Day 4 - Afternoon Slot"),
        ("Nov 22", "07:30 PM IST", "Day 4 - Evening Golden Hour"),
    ]

    for idx, r in enumerate(results):
        day, slot, label = schedule_slots[idx]
        queue.append({
            "file": r["file"],
            "title": r["title"],
            "description": r["description"],
            "tags": r["tags"],
            "privacy": "public",
            "category": "20",
            "uploaded": False,
            "schedule": slot,
            "slot_label": f"{day} - {label} ({slot})",
            "pinned_comment": r["pinned_comment"]
        })

    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

    print("\n[+] Successfully updated upload_queue.json with 4 new clips!")

    # Ephemeral cleanup of temp_work
    for item in TEMP_DIR.glob("*"):
        try:
            if item.is_file():
                item.unlink()
        except Exception:
            pass
    print("[+] Wiped temp_work/ clean.")

if __name__ == "__main__":
    main()
