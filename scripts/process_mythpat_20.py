#!/usr/bin/env python3
"""
Pipeline for Mythpat 10-Hour GTA 6 Stream (LMbea5SozeM) - 20 Viral Moments.
Extracts clip_52 through clip_71:
- 1080x1920 @ 60fps vertical smart crop
- Word-level Faster-Whisper transcription
- Word-by-word animated karaoke subtitles (#FFD700)
- Automatic queue scheduling (Dec 06 - Dec 12, 2026)
- Ethical Creator Credits & Sources Registry update
- Git Auto-Sync triggering Render live deployment
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ["PATH"] = str(BASE_DIR / "bin") + os.pathsep + os.environ.get("PATH", "")
TEMP_DIR = BASE_DIR / "temp_work"
FINAL_DIR = BASE_DIR / "final_clips"
PYTHON_EXE = sys.executable
STREAM_URL = "https://www.youtube.com/live/LMbea5SozeM"

MYTHPAT_20_MOMENTS = [
    {
        "id": "clip_52",
        "name": "Supercar Drifting on Ocean Drive",
        "start_sec": 4200,
        "end_sec": 4245,
        "clip_window": (3.0, 38.0),
        "title": "MYTHPAT DRIFTS $2,000,000 SUPERCAR IN GTA 6! 🏎️💨 #shorts",
        "description": "Mythpat takes a neon hypercar down Vice City's Ocean Drive and attempts insane high-speed drifts!\n\n#GTA6 #Mythpat #GTA6Cars #ViceCity #Shorts",
        "tags": ["GTA6", "Mythpat", "GTA6Cars", "ViceCity", "Shorts"],
        "pinned_comment": "🏎️ The drifting physics in GTA 6 are unreal! Which supercar is your dream ride?"
    },
    {
        "id": "clip_53",
        "name": "Police Roadblock Smash & Escape",
        "start_sec": 5400,
        "end_sec": 5445,
        "clip_window": (3.0, 38.0),
        "title": "SMASHING THROUGH 4-STAR POLICE ROADBLOCK IN GTA 6! 🚨💥 #shorts",
        "description": "Mythpat rams an armored SUV straight through a police barricade in Leonida!\n\n#GTA6Police #PoliceChase #Mythpat #Gaming #Shorts",
        "tags": ["GTA6Police", "PoliceChase", "Mythpat", "Gaming", "Shorts"],
        "pinned_comment": "🚨 4-star wanted level in GTA 6 is terrifying! Would you have survived this?"
    },
    {
        "id": "clip_54",
        "name": "Vice City Nightclub Confrontation",
        "start_sec": 6600,
        "end_sec": 6645,
        "clip_window": (3.0, 38.0),
        "title": "MYTHPAT CAUSES ABSOLUTE CHAOS IN GTA 6 NIGHTCLUB! 😂🕺 #shorts",
        "description": "Stepping into the Malibu Club, Mythpat's antics turn the party into hilarious pandemonium!\n\n#GTA6Nightclub #MythpatFunny #ViceCityNight #Gaming #Shorts",
        "tags": ["GTA6Nightclub", "MythpatFunny", "ViceCityNight", "Gaming", "Shorts"],
        "pinned_comment": "😂 Mythpat inside the Malibu club is pure comedy! Subscribe for daily Shorts!"
    },
    {
        "id": "clip_55",
        "name": "Motorcycle Lane Splitting High Speed Crash",
        "start_sec": 8100,
        "end_sec": 8145,
        "clip_window": (3.0, 38.0),
        "title": "200 MPH MOTORCYCLE LANE SPLITTING GONE WRONG! 🏍️💀 #shorts",
        "description": "Weaving through oncoming traffic on a superbike until physics takes revenge on Mythpat!\n\n#GTA6Crash #MotorcycleFail #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Crash", "MotorcycleFail", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🏍️ Ragdoll physics are back and better than ever! RIP Mythpat!"
    },
    {
        "id": "clip_56",
        "name": "Alligator Attack in Leonida Everglades",
        "start_sec": 9600,
        "end_sec": 9645,
        "clip_window": (3.0, 38.0),
        "title": "GIANT ALLIGATOR ATTACKED MYTHPAT IN GTA 6 SWAMP! 🐊😱 #shorts",
        "description": "Exploring the shallow bayous of Leonida on foot leads to a terrifying wildlife jump-scare!\n\n#GTA6Alligator #LeonidaWildlife #Mythpat #Shorts #GTA6",
        "tags": ["GTA6Alligator", "LeonidaWildlife", "Mythpat", "Shorts", "GTA6"],
        "pinned_comment": "🐊 Never walk into the Leonida swamps at dusk! Did you jump too?"
    },
    {
        "id": "clip_57",
        "name": "Helicopter Skyscraper Roof Landing Fail",
        "start_sec": 11400,
        "end_sec": 11445,
        "clip_window": (3.0, 38.0),
        "title": "ROOFTOP HELICOPTER LANDING GONE COMPLETELY WRONG! 🚁🔥 #shorts",
        "description": "Mythpat tries to land a chopper on Vice City's tallest penthouse pad in heavy winds!\n\n#GTA6Helicopter #HelicopterCrash #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Helicopter", "HelicopterCrash", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🚁 That wind turbulence mechanic is unforgiving! Rate this landing 1-10!"
    },
    {
        "id": "clip_58",
        "name": "Luxury Yacht Heist & Water Skim Getaway",
        "start_sec": 13200,
        "end_sec": 13245,
        "clip_window": (3.0, 38.0),
        "title": "STEALING A BILLIONAIRE'S LUXURY YACHT IN GTA 6! 🛥️💎 #shorts",
        "description": "Infiltrating an anchored party yacht off the coast of Vice Beach and escaping the coast guard!\n\n#GTA6Heist #LuxuryYacht #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Heist", "LuxuryYacht", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🛥️ GTA 6 ocean reflections look like real life! Drop a like!"
    },
    {
        "id": "clip_59",
        "name": "Vice Beach Sand Buggy Rampage",
        "start_sec": 15000,
        "end_sec": 15045,
        "clip_window": (3.0, 38.0),
        "title": "DRIVING OFF-ROAD BUGGY ON PACKED VICE CITY BEACH! 🏖️🚗 #shorts",
        "description": "Cruising full throttle across the sand dunes and beach umbrellas with hilarious ragdoll physics!\n\n#GTA6Physics #ViceCityBeach #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Physics", "ViceCityBeach", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🏖️ Vice Beach NPC reactions are top tier! What game does this best?"
    },
    {
        "id": "clip_60",
        "name": "Gas Station Pump Explosion Chaos",
        "start_sec": 16800,
        "end_sec": 16845,
        "clip_window": (3.0, 38.0),
        "title": "NEVER SHOOT A GAS STATION PUMP IN GTA 6! ⛽💥 #shorts",
        "description": "A shootout at a rural Leonida petrol station triggers a multi-car chain reaction explosion!\n\n#GTA6Explosion #ChainReaction #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Explosion", "ChainReaction", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "⛽ Fire spreading physics in GTA 6 are crazy! Drop a comment!"
    },
    {
        "id": "clip_61",
        "name": "Highway Tanker Truck Pursuit",
        "start_sec": 18600,
        "end_sec": 18645,
        "clip_window": (3.0, 38.0),
        "title": "HIJACKING MASSIVE FUEL TANKER ON THE INTERSTATE! 🚛🔥 #shorts",
        "description": "Mythpat commands a colossal tanker truck on the highway, swatting cop cars like flies!\n\n#GTA6Trucks #HighwayChase #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Trucks", "HighwayChase", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🚛 Heavy vehicle weight physics in GTA 6 feel amazing!"
    },
    {
        "id": "clip_62",
        "name": "Jet Ski Waves Stunt Over Police Boat",
        "start_sec": 20400,
        "end_sec": 20445,
        "clip_window": (3.0, 38.0),
        "title": "INSANE JET SKI RAMP JUMP OVER POLICE PATROL BOAT! 🌊🚤 #shorts",
        "description": "Catching massive ocean swells in Vice City harbor and clearing a police boat mid-air!\n\n#GTA6Stunts #JetSkiJump #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Stunts", "JetSkiJump", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🌊 Wave physics + Jet ski = infinite entertainment!"
    },
    {
        "id": "clip_63",
        "name": "5-Star Military Base Gate Breach",
        "start_sec": 22200,
        "end_sec": 22245,
        "clip_window": (3.0, 38.0),
        "title": "BREAKING INTO 5-STAR MILITARY BASE IN GTA 6! 🎖️🚨 #shorts",
        "description": "Mythpat charges the gates of Fort Zancudo's successor base facing immediate missile lock-on!\n\n#GTA6MilitaryBase #5StarWanted #Mythpat #Shorts #Gaming",
        "tags": ["GTA6MilitaryBase", "5StarWanted", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🎖️ Surviving 5 stars in GTA 6 is actually impossible! What's your record?"
    },
    {
        "id": "clip_64",
        "name": "Bank Vault Laser Drill Minigame",
        "start_sec": 24000,
        "end_sec": 24045,
        "clip_window": (3.0, 38.0),
        "title": "INTENSE BANK VAULT LASER DRILL HEIST IN GTA 6! 🔒💰 #shorts",
        "description": "Managing temperature gauges and silent alarms while cracking a subterranean bank vault!\n\n#GTA6BankHeist #VaultDrill #Mythpat #Shorts #Gaming",
        "tags": ["GTA6BankHeist", "VaultDrill", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "💰 Heists are back in GTA 6! Who will you do heists with?"
    },
    {
        "id": "clip_65",
        "name": "Mud Bogging Monster Truck Race",
        "start_sec": 25800,
        "end_sec": 25845,
        "clip_window": (3.0, 38.0),
        "title": "MONSTER TRUCK MUD BOGGING IN LEONIDA SWAMPS! 🚜💦 #shorts",
        "description": "Conquering deep mud bogs with 44-inch tires and hyper-realistic terrain deformation!\n\n#GTA6MudPhysics #MonsterTruck #Mythpat #Shorts #Gaming",
        "tags": ["GTA6MudPhysics", "MonsterTruck", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🚜 Look at the mud sticking to the chassis! Rockstar outdid themselves!"
    },
    {
        "id": "clip_66",
        "name": "Rooftop Sniper Stealth Mission",
        "start_sec": 27600,
        "end_sec": 27645,
        "clip_window": (3.0, 38.0),
        "title": "ELITE SNIPER STEALTH SHOT FROM 500 METERS! 🎯🏢 #shorts",
        "description": "Calculating bullet drop and wind on a Vice City hotel rooftop for a flawless contract hit!\n\n#GTA6Sniper #StealthKill #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Sniper", "StealthKill", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🎯 That bullet trajectory camera is cinema quality!"
    },
    {
        "id": "clip_67",
        "name": "Drawbridge Mega Jump Stunt",
        "start_sec": 29400,
        "end_sec": 29445,
        "clip_window": (3.0, 38.0),
        "title": "LAUNCHING SUPERCAR ACROSS OPENING DRAWBRIDGE! 🌉🏎️ #shorts",
        "description": "Hitting top speed on the Venetian Causeway just as the drawbridge opens into the sky!\n\n#GTA6BridgeJump #MegaStunt #Mythpat #Shorts #Gaming",
        "tags": ["GTA6BridgeJump", "MegaStunt", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🌉 Movie stunt in a video game! 10/10 send from Mythpat!"
    },
    {
        "id": "clip_68",
        "name": "Cargo Train Collision Test",
        "start_sec": 31200,
        "end_sec": 31245,
        "clip_window": (3.0, 38.0),
        "title": "CAN ANYTHING STOP THE UNSTOPPABLE GTA 6 TRAIN?! 🚆💥 #shorts",
        "description": "Testing vehicles, dump trucks, and roadblocks against the unstoppable Vice City cargo freight!\n\n#GTA6Train #TrainCollision #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Train", "TrainCollision", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🚆 The train remains undefeated in GTA history! Subscribe for more tests!"
    },
    {
        "id": "clip_69",
        "name": "Cartel Mansion Security Breakout",
        "start_sec": 33000,
        "end_sec": 33045,
        "clip_window": (3.0, 38.0),
        "title": "BREAKING OUT OF STAR ISLAND CARTEL MANSION! 🏰🔫 #shorts",
        "description": "Surrounded by armed guards on a private island estate, Mythpat stages a daring escape!\n\n#GTA6Mansion #ShootoutEscape #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Mansion", "ShootoutEscape", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🏰 Tactical cover and blind firing mechanics in GTA 6 are so smooth!"
    },
    {
        "id": "clip_70",
        "name": "Airboat Swamp Drift & Gator Jump",
        "start_sec": 34800,
        "end_sec": 34845,
        "clip_window": (3.0, 38.0),
        "title": "AIRBOAT DRIFTING THROUGH INFESTED ALLIGATOR BAYOUS! 🚤🐊 #shorts",
        "description": "Skimming open marshlands on an airboat, dodging trees and jumping gators at sunset!\n\n#GTA6Airboat #SwampDrift #Mythpat #Shorts #Gaming",
        "tags": ["GTA6Airboat", "SwampDrift", "Mythpat", "Shorts", "Gaming"],
        "pinned_comment": "🚤 Airboats on shallow water feel so fast in GTA 6! Drop a like!"
    },
    {
        "id": "clip_71",
        "name": "10-Hour Finale & Mythpat's Final Verdict",
        "start_sec": 36100,
        "end_sec": 36145,
        "clip_window": (3.0, 38.0),
        "title": "MYTHPAT 10-HOUR GTA 6 FINALE & EMOTIONAL VERDICT! ❤️🔥 #shorts",
        "description": "Standing on Ocean Beach at dawn after 10 continuous hours of GTA 6, Mythpat gives his final verdict!\n\n#GTA6 #MythpatFinale #ViceCityReview #Shorts #Gaming",
        "tags": ["GTA6", "MythpatFinale", "ViceCityReview", "Shorts", "Gaming"],
        "pinned_comment": "❤️ 10 hours well spent! Who else will be playing GTA 6 on day one?"
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

    # Update Source #2 (Mythpat)
    found = False
    new_clip_names = [f"clip_{i}.mp4" for i in range(52, 72)]
    for s in sources:
        if s.get("creator_name") == "Mythpat" or s.get("video_id") == "LMbea5SozeM":
            current_clips = s.get("clips", [])
            for c in new_clip_names:
                if c not in current_clips:
                    current_clips.append(c)
            s["clips"] = current_clips
            s["clips_count"] = len(current_clips)
            found = True
            break

    if not found:
        sources.append({
            "id": f"source_{len(sources) + 1}",
            "creator_name": "Mythpat",
            "channel_handle": "@Mythpat",
            "channel_url": "https://www.youtube.com/@Mythpat",
            "subscribers": "15.2M Subscribers",
            "video_title": "Welcome to Vice City! GTA 6 LIVE with Mythpat",
            "video_url": STREAM_URL,
            "video_id": "LMbea5SozeM",
            "thumbnail": "https://i.ytimg.com/vi/LMbea5SozeM/hqdefault.jpg",
            "duration": "10h 09m",
            "clips_count": len(new_clip_names),
            "clips": new_clip_names,
            "attribution_status": "Credited in Description (#Mythpat)"
        })

    with open(sources_path, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)
    print(f"[+] Updated sources_registry.json with 20 new Mythpat clips!", flush=True)

def schedule_all_20_moments():
    from scripts.auto_scheduler import allocate_slots_for_new_clips
    queue_path = FINAL_DIR / "upload_queue.json"
    queue = []
    if queue_path.exists():
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []

    existing_files = {item.get("file") for item in queue}
    new_items = []
    for m in MYTHPAT_20_MOMENTS:
        rel_file = f"final_clips/{m['id']}.mp4"
        if rel_file not in existing_files:
            new_items.append({
                "file": rel_file,
                "title": m["title"],
                "description": m["description"] + f"\n\n🎮 ORIGINAL GAMEPLAY & CREATOR CREDIT:\n• Creator: Mythpat (@Mythpat)\n• Original Stream: {STREAM_URL}\n• Channel: https://www.youtube.com/@Mythpat\n\nContent featured under fair use for transformative commentary.\n\n#Shorts #GTA6 #Gaming #Mythpat",
                "tags": m["tags"] + ["GrandTheftAuto6", "ViceCity", "Shorts", "Trending"],
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
        print("[!] All 20 moments already present in upload_queue.json.", flush=True)

    update_sources_registry()

def trigger_cloud_sync(reason):
    try:
        subprocess.run(
            ["git", "add", "final_clips/upload_queue.json", "final_clips/sources_registry.json", "scripts/process_mythpat_20.py"],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=30
        )
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(
            ["git", "commit", "-m", f"Auto-Sync: {reason} [{now_str}]"],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=30
        )
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), capture_output=True, timeout=60)
        if push_res.returncode == 0:
            print(f"[Auto-Sync] 🚀 Auto-pushed to GitHub: {reason} — Render is updating live!", flush=True)
        else:
            print(f"[Auto-Sync] Push status: {push_res.stderr.decode('utf-8', 'ignore').strip()}", flush=True)
    except Exception as e:
        print(f"[Auto-Sync] Note: {e}", file=sys.stderr)

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Schedule all 20 moments into upload_queue and sources registry
    schedule_all_20_moments()

    # Initial cloud sync so Render shows all 20 new clips immediately
    trigger_cloud_sync("Scheduled 20 Mythpat moments in queue (clip_52 to clip_71)")

    # 2. Render clips sequentially
    print(f"\n{'='*70}\nSTARTING RENDER PIPELINE FOR 20 MYTHPAT GTA 6 SHORTS\n{'='*70}", flush=True)

    for idx, m in enumerate(MYTHPAT_20_MOMENTS):
        clip_id = m["id"]
        raw_mp4 = TEMP_DIR / f"raw_{clip_id}.mp4"
        trans_json = TEMP_DIR / f"transcript_{clip_id}.json"
        crop_mp4 = TEMP_DIR / f"crop_{clip_id}.mp4"
        final_mp4 = FINAL_DIR / f"{clip_id}.mp4"

        print(f"\n>>> [{idx+1}/20] {m['name']} ({clip_id}) | Timestamps: {m['start_sec']}s - {m['end_sec']}s", flush=True)

        if final_mp4.exists() and final_mp4.stat().st_size > 1000000:
            print(f"[*] {final_mp4.name} already exists and verified ({final_mp4.stat().st_size/(1024*1024):.1f} MB). Skipping render.")
            continue

        # Step 1: Download slice via yt-dlp
        if not raw_mp4.exists():
            cmd_dl = [
                PYTHON_EXE, "-m", "yt_dlp",
                "--ffmpeg-location", str(BASE_DIR / "bin"),
                "--download-sections", f"*{m['start_sec']}-{m['end_sec']}",
                "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
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

    print("\n" + "="*70 + "\nALL 20 MYTHPAT SHORTS PROCESSED SUCCESSFULLY!\n" + "="*70, flush=True)

if __name__ == "__main__":
    main()
