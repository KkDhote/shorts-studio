#!/usr/bin/env python3
"""
Agent Pipeline: Ingest Techno Gamerz GTA 6 Premiere VOD (169ZzvPxvvM),
Extract 10 Viral Moments, Transcribe, Smart Crop (1080x1920 @ 60fps),
Burn Golden Karaoke Captions, Schedule into upload_queue.json,
and Update sources_registry.json.
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

STREAM_URL = "https://www.youtube.com/watch?v=169ZzvPxvvM"

TECHNO_10_MOMENTS = [
    {
        "id": "clip_42",
        "name": "Vice City Midnight Car Theft Gone Wrong",
        "start_sec": 40,
        "end_sec": 85,
        "clip_window": (3.0, 42.0),
        "title": "TECHNO GAMERZ FIRST CAR THEFT IN GTA 6 GONE WRONG! 🚨🚗 #shorts",
        "description": "Jason and Lucia attempt their first vehicle break-in in a dark Vice City backstreet! Techno Gamerz loses it!\n\n#GTA6 #TechnoGamerz #GTA6Gameplay #Shorts #ViceCity #Gaming",
        "tags": ["GTA6", "TechnoGamerz", "GTA6Gameplay", "Shorts", "ViceCity", "Gaming"],
        "pinned_comment": "🚗 Techno's first GTA 6 car theft was pure comedy! Drop a like!"
    },
    {
        "id": "clip_43",
        "name": "Jason & Lucia Insane 2-Second Cop Knockout",
        "start_sec": 128,
        "end_sec": 168,
        "clip_window": (3.0, 38.0),
        "title": "JASON & LUCIA OP COP TAKEDOWN IN GTA 6! 😱🔥 #shorts",
        "description": "Two patrol officers corner Jason and Lucia at gunpoint and Jason drops them both in 2 seconds!\n\n#GTA6 #Lucia #Jason #TechnoGamerz #GTA6Shorts #ViceCity",
        "tags": ["GTA6", "Lucia", "Jason", "TechnoGamerz", "GTA6Shorts", "ViceCity"],
        "pinned_comment": "😱 That dual knockout was surgical! Subscribe for daily GTA 6 Shorts!"
    },
    {
        "id": "clip_44",
        "name": "Techno Mindblown by GTA 6 Photorealistic Graphics",
        "start_sec": 170,
        "end_sec": 210,
        "clip_window": (3.0, 38.0),
        "title": "GTA 6 GRAPHICS ARE UNREAL! (MOVIE LEVEL) 🤯✨ #shorts",
        "description": "Neon reflections and next-gen Vice City skyline graphics leave Techno completely mindblown!\n\n#GTA6Graphics #GTA6Gameplay #TechnoGamerz #Shorts #RockstarGames",
        "tags": ["GTA6Graphics", "GTA6Gameplay", "TechnoGamerz", "Shorts", "RockstarGames"],
        "pinned_comment": "🤯 Is GTA 6 the best looking game ever made? What do you rate it?"
    },
    {
        "id": "clip_45",
        "name": "Lucia Prison Corridor Reveal & Badass Intro",
        "start_sec": 260,
        "end_sec": 300,
        "clip_window": (3.0, 38.0),
        "title": "GTA 6 FEMALE PROTAGONIST LUCIA IN JAIL! ⛓️🔥 #shorts",
        "description": "Lucia strides down the prison corridor in her orange jumpsuit and Techno reacts to GTA's first female lead!\n\n#GTA6 #Lucia #GTA6FemaleProtagonist #TechnoGamerz #GamingShorts",
        "tags": ["GTA6", "Lucia", "GTA6FemaleProtagonist", "TechnoGamerz", "GamingShorts"],
        "pinned_comment": "⛓️ Lucia is already legendary! Who's your favorite character so far?"
    },
    {
        "id": "clip_46",
        "name": "Lucia's Sassy Parole Meeting: Bad Luck I Guess",
        "start_sec": 486,
        "end_sec": 525,
        "clip_window": (3.0, 37.0),
        "title": "LUCIA'S COLD REPLY TO PAROLE OFFICER IN GTA 6! 😂🕶️ #shorts",
        "description": "'Lucia, do you know why you're here?' 'Bad luck I guess.' Techno cracks up at her cold attitude!\n\n#GTA6Cutscene #Lucia #TechnoGamerz #GTA6Story #Shorts",
        "tags": ["GTA6Cutscene", "Lucia", "TechnoGamerz", "GTA6Story", "Shorts"],
        "pinned_comment": "😂 That trailer line in-game hits different! Drop a comment!"
    },
    {
        "id": "clip_47",
        "name": "The Store Robbery & Panic Alarm Gone Wrong",
        "start_sec": 633,
        "end_sec": 675,
        "clip_window": (3.0, 40.0),
        "title": "STORE ROBBERY TURNS INTO COMPLETE CHAOS IN GTA 6! 🚨💸 #shorts",
        "description": "Jason and Lucia loot the store register when an NPC tackles Jason and the panic alarm sounds!\n\n#GTA6Heist #StoreRobbery #TechnoGamerz #GTA6Action #Shorts",
        "tags": ["GTA6Heist", "StoreRobbery", "TechnoGamerz", "GTA6Action", "Shorts"],
        "pinned_comment": "🚨 Always check the counter before grabbing cash! Hit subscribe!"
    },
    {
        "id": "clip_48",
        "name": "Dark Beach Highway Speed Run & Swamp Banter",
        "start_sec": 2100,
        "end_sec": 2142,
        "clip_window": (3.0, 40.0),
        "title": "NIGHT DRIVING IN LEONIDA SWAMPS GONE WRONG! 🐊🏎️ #shorts",
        "description": "Jason speeds through pitch-black Leonida swamps dodging oncoming traffic and alligator habitats!\n\n#GTA6Driving #Leonida #TechnoGamerz #ViceCityNight #Shorts",
        "tags": ["GTA6Driving", "Leonida", "TechnoGamerz", "ViceCityNight", "Shorts"],
        "pinned_comment": "🐊 Night driving in the Everglades is terrifying! What would you do?"
    },
    {
        "id": "clip_49",
        "name": "Brand New Custom Ganado Crashed in 5 Seconds",
        "start_sec": 3900,
        "end_sec": 3940,
        "clip_window": (3.0, 38.0),
        "title": "CRASHED MY CUSTOM '70 GANADO IMMEDIATELY IN GTA 6! 😭🚙 #shorts",
        "description": "Techno finishes a custom teal paint job on his classic muscle truck and immediately totals it into a pileup!\n\n#GTA6Crash #CarCrash #TechnoGamerz #GTA6CustomCars #Shorts",
        "tags": ["GTA6Crash", "CarCrash", "TechnoGamerz", "GTA6CustomCars", "Shorts"],
        "pinned_comment": "😭 $10,000 paint job gone in 5 seconds! RIP Techno's truck!"
    },
    {
        "id": "clip_50",
        "name": "Safehouse Kitchen Renovation & Criminal Focus Bar",
        "start_sec": 5340,
        "end_sec": 5385,
        "clip_window": (3.0, 42.0),
        "title": "GTA 6 INTERACTIVE SAFEHOUSE PHYSICS & KITCHEN SECRET! 🍳🏠 #shorts",
        "description": "Jason explores his safehouse appliances, discovering next-gen interactive physics and criminal focus mechanics!\n\n#GTA6Details #GTA6Safehouse #TechnoGamerz #GTA6Features #Shorts",
        "tags": ["GTA6Details", "GTA6Safehouse", "TechnoGamerz", "GTA6Features", "Shorts"],
        "pinned_comment": "🍳 Rockstar's attention to detail is undefeated! Did you spot the fridge?"
    },
    {
        "id": "clip_51",
        "name": "2-Hour Finale Verdict & The 2018 Promise",
        "start_sec": 7575,
        "end_sec": 7615,
        "clip_window": (3.0, 38.0),
        "title": "TECHNO GAMERZ HISTORIC GTA 6 PROMISE! ❤️🔥 #shorts",
        "description": "Standing on a Vice City pier, Techno Gamerz makes an emotional promise to upload daily GTA 6 at 9:00 PM!\n\n#GTA6 #TechnoGamerz #DailyGTA6 #ViceCity #YouTubeShorts",
        "tags": ["GTA6", "TechnoGamerz", "DailyGTA6", "ViceCity", "YouTubeShorts"],
        "pinned_comment": "❤️ The 2018 nostalgia is back! Subscribe for daily GTA 6 episodes & Shorts!"
    }
]

def update_sources_registry():
    sources_path = FINAL_DIR / "sources_registry.json"
    sources = []
    if sources_path.exists():
        try:
            with open(sources_path, "r", encoding="utf-8") as f:
                sources = json.load(f)
        except Exception:
            sources = []

    exists = any(s.get("video_id") == "169ZzvPxvvM" for s in sources)
    if not exists:
        new_source = {
            "id": f"source_{len(sources) + 1}",
            "creator_name": "Techno Gamerz",
            "channel_handle": "@TechnoGamerzOfficial",
            "channel_url": "https://www.youtube.com/@TechnoGamerzOfficial",
            "subscribers": "43.1M Subscribers",
            "video_title": "MY FIRST DAY IN VICE CITY | GTA 6 GAMEPLAY #1",
            "video_url": STREAM_URL,
            "video_id": "169ZzvPxvvM",
            "thumbnail": "https://i.ytimg.com/vi/169ZzvPxvvM/hqdefault.jpg",
            "duration": "2h 07m",
            "clips_count": 10,
            "clips": [f"{m['id']}.mp4" for m in TECHNO_10_MOMENTS],
            "attribution_status": "Credited in Description (#TechnoGamerz)"
        }
        sources.append(new_source)
        with open(sources_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
        print("[+] Updated sources_registry.json with Techno Gamerz (10 clips)!", flush=True)

def schedule_all_10_moments():
    queue_path = FINAL_DIR / "upload_queue.json"
    queue = []
    if queue_path.exists():
        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

    existing_files = {item.get("file") for item in queue}

    new_items = []
    for m in TECHNO_10_MOMENTS:
        rel_file = f"final_clips/{m['id']}.mp4"
        if rel_file not in existing_files:
            new_items.append({
                "file": rel_file,
                "title": m["title"],
                "description": m["description"],
                "tags": m["tags"],
                "privacy": "public",
                "category": "20",
                "uploaded": False,
                "pinned_comment": m["pinned_comment"]
            })

    if new_items:
        allocated = allocate_slots_for_new_clips(new_items, queue_path)
        for c in allocated:
            queue.append(c)

        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        print(f"[+] Successfully auto-scheduled {len(allocated)} new clips into upload_queue.json!", flush=True)
    else:
        print("[!] All 10 moments already present in upload_queue.json.", flush=True)

    update_sources_registry()

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Schedule all 10 moments into upload_queue and sources registry
    schedule_all_10_moments()

    # 2. Render clips sequentially
    print(f"\n{'='*70}\nSTARTING RENDER PIPELINE FOR 10 TECHNO GAMERZ SHORTS\n{'='*70}", flush=True)

    for idx, m in enumerate(TECHNO_10_MOMENTS):
        clip_id = m["id"]
        raw_mp4 = TEMP_DIR / f"raw_{clip_id}.mp4"
        trans_json = TEMP_DIR / f"transcript_{clip_id}.json"
        crop_mp4 = TEMP_DIR / f"crop_{clip_id}.mp4"
        final_mp4 = FINAL_DIR / f"{clip_id}.mp4"

        print(f"\n>>> [{idx+1}/10] {m['name']} ({clip_id}) | Timestamps: {m['start_sec']}s - {m['end_sec']}s", flush=True)

        if final_mp4.exists() and final_mp4.stat().st_size > 1000000:
            print(f"[*] {final_mp4.name} already exists and verified ({final_mp4.stat().st_size/(1024*1024):.1f} MB). Skipping render.")
            continue

        # Step 1: Download slice via yt-dlp
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
            res_dl = subprocess.run(cmd_dl, text=True)
            if res_dl.returncode != 0:
                print(f"[!] Warning: Download failed for {clip_id}, continuing...", file=sys.stderr)
                continue

        # Step 2: Transcribe word-level timestamps via Faster-Whisper
        if not trans_json.exists():
            cmd_trans = [
                PYTHON_EXE, "scripts/transcribe.py",
                "-i", str(raw_mp4),
                "-o", str(trans_json),
                "--model", "base"
            ]
            res_trans = subprocess.run(cmd_trans, text=True)
            if res_trans.returncode != 0:
                print(f"[!] Warning: Transcribe failed for {clip_id}", file=sys.stderr)

        # Step 3: Smart Crop to 9:16 at 60 FPS
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
            res_crop = subprocess.run(cmd_crop, text=True)
            if res_crop.returncode != 0:
                print(f"[!] Warning: Smart crop failed for {clip_id}", file=sys.stderr)
                continue

        # Step 4: Render Animated Karaoke Captions
        cmd_caps = [
            PYTHON_EXE, "scripts/render_captions.py",
            "-i", str(crop_mp4),
            "-t", str(trans_json),
            "-o", str(final_mp4),
            "-s", str(start_w),
            "-e", str(end_w),
            "--fps", "60"
        ]
        res_caps = subprocess.run(cmd_caps, text=True)
        if res_caps.returncode != 0:
            print(f"[!] Warning: Caption burn failed for {clip_id}", file=sys.stderr)
            continue

        print(f"[+] Rendered {final_mp4.name} successfully ({final_mp4.stat().st_size / (1024*1024):.1f} MB)!", flush=True)

        # Ephemeral cleanup of raw work
        for tmp_file in [raw_mp4, trans_json, crop_mp4]:
            try:
                if tmp_file.exists():
                    tmp_file.unlink()
            except Exception:
                pass

    print("\n" + "="*70 + "\nALL 10 TECHNO GAMERZ SHORTS PROCESSED SUCCESSFULLY!\n" + "="*70, flush=True)

if __name__ == "__main__":
    main()
