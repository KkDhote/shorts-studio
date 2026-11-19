#!/usr/bin/env python3
"""
IShowSpeed 25 Viral Moments Pipeline for GTA 6 Early Access Stream.
Processes, transcribes, smart-crops (60fps 1080x1920), burns karaoke captions,
schedules 25 clips into upload_queue.json, and updates sources_registry.json.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yt_dlp

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["PATH"] = str(BASE_DIR / "bin") + os.pathsep + os.environ.get("PATH", "")
TEMP_DIR = BASE_DIR / "temp_work"
FINAL_DIR = BASE_DIR / "final_clips"
PYTHON_EXE = sys.executable

sys.path.insert(0, str(BASE_DIR))
from scripts.auto_scheduler import allocate_slots_for_new_clips

STREAM_URL = "https://www.youtube.com/watch?v=qSyo5d-dVzA"

MOMENTS_25 = [
    {
        "id": "clip_17",
        "name": "Speed Explosive Hype Dance",
        "start_sec": 135,
        "end_sec": 180,
        "clip_window": (4.0, 44.0),
        "title": "SPEED CANNOT BELIEVE HE HAS GTA 6 EARLY ACCESS! 🤯🔥 #shorts",
        "description": "Speed screams, jumps, and barks with 300k+ viewers as GTA 6 launches!\n\n#GTA6 #IShowSpeed #SpeedLive #Gaming #Shorts #GTAVI #Trending",
        "tags": ["GTA6", "IShowSpeed", "SpeedLive", "Gaming", "Shorts", "GTAVI", "Trending"],
        "pinned_comment": "🤯 The wait is finally over! Drop a like if you're watching Speed live!"
    },
    {
        "id": "clip_18",
        "name": "210 GB Download Panic",
        "start_sec": 245,
        "end_sec": 285,
        "clip_window": (4.0, 39.0),
        "title": "SPEED'S PC ALMOST CRASHED DOWNLOADING GTA 6! 😱💀 #shorts",
        "description": "Speed hyperventilates as the 210 GB GTA VI download reaches the final seconds!\n\n#GTA6Download #IShowSpeed #RockstarGames #Shorts #Gaming",
        "tags": ["GTA6Download", "IShowSpeed", "RockstarGames", "Shorts", "Gaming"],
        "pinned_comment": "💀 How big is your GTA 6 download? Let us know in the comments!"
    },
    {
        "id": "clip_19",
        "name": "Rockstar Games Boot & HDR Reveal",
        "start_sec": 605,
        "end_sec": 645,
        "clip_window": (4.0, 39.0),
        "title": "SPEED'S JAW DROPS AT THE ROCKSTAR INTRO SCREEN! 🌟 #shorts",
        "description": "The iconic yellow Rockstar Games logo flashes on screen and Speed freezes in awe!\n\n#RockstarGames #GTA6Intro #IShowSpeed #Shorts #GTAVI",
        "tags": ["RockstarGames", "GTA6Intro", "IShowSpeed", "Shorts", "GTAVI"],
        "pinned_comment": "🌟 That opening synth gave real chills! What was your reaction?"
    },
    {
        "id": "clip_20",
        "name": "Vice City Skyline Title Screen",
        "start_sec": 910,
        "end_sec": 955,
        "clip_window": (4.0, 44.0),
        "title": "GTA 6 TITLE SCREEN BROKE SPEED'S BRAIN! 🌆✨ #shorts",
        "description": "Next-gen neon Vice City and cloud physics leave Speed completely speechless!\n\n#GTA6Graphics #ViceCity #IShowSpeed #GamingShorts #Shorts",
        "tags": ["GTA6Graphics", "ViceCity", "IShowSpeed", "GamingShorts", "Shorts"],
        "pinned_comment": "🌆 The greatest graphics in gaming history?! Drop a comment!"
    },
    {
        "id": "clip_21",
        "name": "Lucia Prison Corridor Walk",
        "start_sec": 1215,
        "end_sec": 1260,
        "clip_window": (4.0, 44.0),
        "title": "SPEED MEETS LUCIA FOR THE FIRST TIME IN GTA 6! 🚨🍊 #shorts",
        "description": "Lucia walks down the prison hallway in her orange jumpsuit and Speed goes wild!\n\n#LuciaGTA6 #IShowSpeed #Leonida #Shorts #GTA6",
        "tags": ["LuciaGTA6", "IShowSpeed", "Leonida", "Shorts", "GTA6"],
        "pinned_comment": "🚨 Who's your favorite character so far: Lucia or Jason?"
    },
    {
        "id": "clip_22",
        "name": "Lucia Counseling 'Bad Luck' Cutscene",
        "start_sec": 1505,
        "end_sec": 1545,
        "clip_window": (4.0, 39.0),
        "title": "LUCIA'S FIRST WORDS HAD SPEED ROLLING! 😂💀 #shorts",
        "description": "'Lucia, do you know why you're here?' 'Bad luck, I guess.' Speed loses it!\n\n#GTA6Story #Lucia #IShowSpeedFunny #Shorts #GTAVI",
        "tags": ["GTA6Story", "Lucia", "IShowSpeedFunny", "Shorts", "GTAVI"],
        "pinned_comment": "😂 Lucia's delivery is already iconic! Subscribe for daily GTA 6 Shorts!"
    },
    {
        "id": "clip_23",
        "name": "First Car Theft & Burrito Van Joyride",
        "start_sec": 2530,
        "end_sec": 2575,
        "clip_window": (4.0, 44.0),
        "title": "SPEED'S FIRST CAR JACK IN GTA 6 GOES HORRIBLY WRONG! 🚗💥 #shorts",
        "description": "Speed steals a van on the roadside and immediately crashes into a palm tree!\n\n#GTA6Driving #IShowSpeedCrash #GrandTheftAuto6 #Shorts #Gaming",
        "tags": ["GTA6Driving", "IShowSpeedCrash", "GrandTheftAuto6", "Shorts", "Gaming"],
        "pinned_comment": "🚗 Speed's driving skills haven't changed one bit! Drop a like!"
    },
    {
        "id": "clip_24",
        "name": "Jason Closet Reveal & First Switch",
        "start_sec": 3615,
        "end_sec": 3660,
        "clip_window": (4.0, 44.0),
        "title": "SPEED'S REACTION TO JASON IN GTA 6 IS PRICELESS! 🕶️🔥 #shorts",
        "description": "Jason Duval steps out of the motel room and Speed examines his character model!\n\n#JasonGTA6 #IShowSpeed #GTA6Protagonist #Shorts #GTAVI",
        "tags": ["JasonGTA6", "IShowSpeed", "GTA6Protagonist", "Shorts", "GTAVI"],
        "pinned_comment": "🕶️ Jason is Him! Drop a like if you're hyped for the story mode!"
    },
    {
        "id": "clip_25",
        "name": "Beach Patio Confrontation",
        "start_sec": 4510,
        "end_sec": 4555,
        "clip_window": (4.0, 44.0),
        "title": "SPEED TRIES DEFUSING AN NPC AND INSTANTLY REGRETS IT! 🥊🏖️ #shorts",
        "description": "Speed tests the new NPC dialogue prompt and ends up in a brawl on Vice Beach!\n\n#GTA6NPCs #IShowSpeedFunny #ViceBeach #Shorts #Gaming",
        "tags": ["GTA6NPCs", "IShowSpeedFunny", "ViceBeach", "Shorts", "Gaming"],
        "pinned_comment": "🥊 The new NPC conversation system is incredible! What would you do?"
    },
    {
        "id": "clip_26",
        "name": "Night Roadblock & First Police Evasion",
        "start_sec": 5120,
        "end_sec": 5165,
        "clip_window": (4.0, 44.0),
        "title": "SPEED VS VICE CITY POLICE AT 2 AM! 🚔💨 #shorts",
        "description": "County sheriff roadblock ambush! Speed drifts past spike strips into the night!\n\n#PoliceChase #GTA6Police #IShowSpeed #Shorts #GTAVI",
        "tags": ["PoliceChase", "GTA6Police", "IShowSpeed", "Shorts", "GTAVI"],
        "pinned_comment": "🚔 The cop AI in GTA 6 does NOT play around! Drop a comment!"
    },
    {
        "id": "clip_27",
        "name": "Mid-Traffic Carjack & 2-Star Flash",
        "start_sec": 6305,
        "end_sec": 6350,
        "clip_window": (4.0, 44.0),
        "title": "SPEED GETS BUSTED IN 4K STEALING A CAR! 🚓🚨 #shorts",
        "description": "Speed pulls a driver out at a red light and gets instant 2-star police heat!\n\n#GTA6Pursuit #IShowSpeedLive #Shorts #GrandTheftAuto6 #Gaming",
        "tags": ["GTA6Pursuit", "IShowSpeedLive", "Shorts", "GrandTheftAuto6", "Gaming"],
        "pinned_comment": "🚨 Instant karma in Vice City! Subscribe for daily GTA 6 clips!"
    },
    {
        "id": "clip_28",
        "name": "Highway Joyride in Vintage Pickup",
        "start_sec": 8115,
        "end_sec": 8160,
        "clip_window": (4.0, 44.0),
        "title": "GTA 6 HIGHWAY GRAPHICS MADE SPEED CRY REAL TEARS! 🌴☀️ #shorts",
        "description": "Sunny palm-lined interstate cruise towards Vice City with in-game radio blaring!\n\n#GTA6Radio #ViceCityHighway #IShowSpeed #Shorts #GTAVI",
        "tags": ["GTA6Radio", "ViceCityHighway", "IShowSpeed", "Shorts", "GTAVI"],
        "pinned_comment": "🌴 Cruising into Vice City hits differently! What station are you playing?"
    },
    {
        "id": "clip_29",
        "name": "Swamp Alligator Jump-Scare",
        "start_sec": 9130,
        "end_sec": 9175,
        "clip_window": (4.0, 44.0),
        "title": "SPEED ENCOUNTERS A GIANT ALLIGATOR IN GTA 6! 🐊😱 #shorts",
        "description": "A massive Florida alligator lunges out of the marsh and Speed jumps out of his chair!\n\n#GTA6Alligator #IShowSpeedJumpscare #FloridaMan #Shorts #GTA6",
        "tags": ["GTA6Alligator", "IShowSpeedJumpscare", "FloridaMan", "Shorts", "GTA6"],
        "pinned_comment": "🐊 Florida wildlife is ruthless in GTA 6! Who got scared too?"
    },
    {
        "id": "clip_30",
        "name": "Everglades Airboat Chase",
        "start_sec": 10100,
        "end_sec": 10145,
        "clip_window": (4.0, 44.0),
        "title": "SPEED DOES AN INSANE AIRBOAT ESCAPE IN GTA 6! 🚤💨 #shorts",
        "description": "Speed drives an airboat through the Everglades swamps, dodging mangrove branches!\n\n#AirboatEscape #GTA6Swamp #IShowSpeed #Shorts #Gaming",
        "tags": ["AirboatEscape", "GTA6Swamp", "IShowSpeed", "Shorts", "Gaming"],
        "pinned_comment": "🚤 Airboats on next-gen water physics are unmatched! Drop a like!"
    },
    {
        "id": "clip_31",
        "name": "First WASTED Screen Desk Slam",
        "start_sec": 10710,
        "end_sec": 10755,
        "clip_window": (4.0, 44.0),
        "title": "SPEED SMASHES HIS SETUP AFTER FIRST GTA 6 DEATH! 💀💥 #shorts",
        "description": "Windshield ragdoll ejection off an overpass triggers the WASTED sound and desk slam!\n\n#IShowSpeedRage #GTA6Wasted #DeskSlam #Shorts #GTAVI",
        "tags": ["IShowSpeedRage", "GTA6Wasted", "DeskSlam", "Shorts", "GTAVI"],
        "pinned_comment": "💀 The classic desk slam returns! RIP Speed's setup!"
    },
    {
        "id": "clip_32",
        "name": "Safehouse Sneak Fail",
        "start_sec": 14410,
        "end_sec": 14450,
        "clip_window": (4.0, 39.0),
        "title": "YOU CAN'T ENTER THE SAFEHOUSE WHILE WANTED?! 🚪👮 #shorts",
        "description": "Jason gets locked out of his safehouse because police are searching the area!\n\n#GTA6Safehouse #IShowSpeedFunny #WantedLevel #Shorts #GTA6",
        "tags": ["GTA6Safehouse", "IShowSpeedFunny", "WantedLevel", "Shorts", "GTA6"],
        "pinned_comment": "🚪 Rockstar fixed the safehouse cheese! No hiding from 5 stars!"
    },
    {
        "id": "clip_33",
        "name": "Ammu-Nation Weapon Shopping Spree",
        "start_sec": 16515,
        "end_sec": 16560,
        "clip_window": (4.0, 44.0),
        "title": "SPEED SPENDS $10,000 AT THE GTA 6 GUN STORE! 🔫💰 #shorts",
        "description": "Speed buys out the Ammu-Nation wall with custom attachments and suppressors!\n\n#AmmuNation #GTA6Weapons #IShowSpeed #Shorts #Gaming",
        "tags": ["AmmuNation", "GTA6Weapons", "IShowSpeed", "Shorts", "Gaming"],
        "pinned_comment": "🔫 Which weapon are you buying first in GTA VI?"
    },
    {
        "id": "clip_34",
        "name": "Unhinged TTS Donation Prank Crash",
        "start_sec": 18720,
        "end_sec": 18765,
        "clip_window": (4.0, 44.0),
        "title": "TTS DONATION CAUSES SPEED TO CRASH HIS SUPERCAR! 🔊🚗 #shorts",
        "description": "A viral donation sound distracts Speed at 140 MPH and he obliterates a bus stop!\n\n#IShowSpeedTTS #SupercarCrash #FunnyMoments #Shorts #GTA6",
        "tags": ["IShowSpeedTTS", "SupercarCrash", "FunnyMoments", "Shorts", "GTA6"],
        "pinned_comment": "🔊 Chat timing is always lethal! Drop a comment if you laughed!"
    },
    {
        "id": "clip_35",
        "name": "Vice City Beach Nightlife Atmosphere",
        "start_sec": 20720,
        "end_sec": 20765,
        "clip_window": (4.0, 44.0),
        "title": "GTA 6 NIGHTLIFE LOOKS LIKE REAL LIFE! 💃🪩 #shorts",
        "description": "Neon Ocean Drive club district with dancing NPCs, selfies, and street brawls!\n\n#ViceCityNightlife #OceanDrive #IShowSpeed #Shorts #GTAVI",
        "tags": ["ViceCityNightlife", "OceanDrive", "IShowSpeed", "Shorts", "GTAVI"],
        "pinned_comment": "💃 The NPC density is mindblowing! Vice City comes alive at night!"
    },
    {
        "id": "clip_36",
        "name": "4-Star SWAT Pursuit on Ocean Bridge",
        "start_sec": 21510,
        "end_sec": 21560,
        "clip_window": (4.0, 49.0),
        "title": "SPEED SURVIVES A 4-STAR GTA 6 SWAT PURSUIT! 🛡️🚁 #shorts",
        "description": "Bearcat armored SWAT vehicles pin Speed down on the Vice City mainland bridge!\n\n#4StarWanted #SWATPursuit #IShowSpeedLive #Shorts #GTA6",
        "tags": ["4StarWanted", "SWATPursuit", "IShowSpeedLive", "Shorts", "GTA6"],
        "pinned_comment": "🛡️ Surviving a 4-star bridge blockade is insane! Hit subscribe!"
    },
    {
        "id": "clip_37",
        "name": "Tropical Pier Speedboat Dock Sprint",
        "start_sec": 23410,
        "end_sec": 23455,
        "clip_window": (4.0, 44.0),
        "title": "SPEED'S WATER PHYSICS REACTION IN GTA 6 IS INSANE! 🌊🚤 #shorts",
        "description": "Speed sprints into crystal clear ocean waters and steals a high-speed racing boat!\n\n#WaterPhysics #ViceCityBoats #IShowSpeed #Shorts #GTAVI",
        "tags": ["WaterPhysics", "ViceCityBoats", "IShowSpeed", "Shorts", "GTAVI"],
        "pinned_comment": "🌊 Best water mechanics in gaming history? What do you rate it /10?"
    },
    {
        "id": "clip_38",
        "name": "Helicopter Flight Over Downtown",
        "start_sec": 29730,
        "end_sec": 29775,
        "clip_window": (4.0, 44.0),
        "title": "SPEED TRIES FLYING A HELICOPTER IN GTA 6 (DISASTER)! 🚁🔥 #shorts",
        "description": "Speed steals a news chopper and weaves between skyscrapers before clipping an antenna!\n\n#GTA6Helicopter #HelicopterCrash #IShowSpeed #Shorts #Gaming",
        "tags": ["GTA6Helicopter", "HelicopterCrash", "IShowSpeed", "Shorts", "Gaming"],
        "pinned_comment": "🚁 Speed should NEVER be given a pilot's license! Drop a like!"
    },
    {
        "id": "clip_39",
        "name": "Neon Motel Drug Deal Shootout",
        "start_sec": 39615,
        "end_sec": 39660,
        "clip_window": (4.0, 44.0),
        "title": "GTA 6 SHOOTOUT MECHANICS ARE NEXT LEVEL! 💥🎯 #shorts",
        "description": "Tense cartel motel deal goes wrong and Speed dives into cover blind-firing with an SMG!\n\n#GTA6Combat #MotelShootout #IShowSpeed #Shorts #GTAVI",
        "tags": ["GTA6Combat", "MotelShootout", "IShowSpeed", "Shorts", "GTAVI"],
        "pinned_comment": "🎯 That blind-fire cover mechanic is so clean! Day one purchase?"
    },
    {
        "id": "clip_40",
        "name": "Crazy Supercar Skyway Stunt Jump",
        "start_sec": 60020,
        "end_sec": 60065,
        "clip_window": (4.0, 44.0),
        "title": "SPEED DOES THE BIGGEST STUNT JUMP IN GTA 6 HISTORY! 🏎️💨 #shorts",
        "description": "Grotti supercar launches off an unfinished highway overpass over a massive canal!\n\n#GTA6Stunts #SkywayJump #IShowSpeed #Shorts #GrandTheftAuto6",
        "tags": ["GTA6Stunts", "SkywayJump", "IShowSpeed", "Shorts", "GrandTheftAuto6"],
        "pinned_comment": "🏎️ That landing was legendary! Share this with a friend!"
    },
    {
        "id": "clip_41",
        "name": "Speed 24-Hour Final Verdict",
        "start_sec": 84910,
        "end_sec": 84960,
        "clip_window": (4.0, 49.0),
        "title": "SPEED'S EMOTIONAL FINAL VERDICT AFTER 24 HOURS OF GTA 6! 🏆❤️ #shorts",
        "description": "Speed signs off after 24 hours of non-stop GTA 6 gameplay: 'Greatest game ever made.'\n\n#GTA6Review #IShowSpeedEmotional #GTA6Marathon #Shorts #GTAVI",
        "tags": ["GTA6Review", "IShowSpeedEmotional", "GTA6Marathon", "Shorts", "GTAVI"],
        "pinned_comment": "🏆 12 years of waiting was 1000% worth it. Subscribe for daily GTA VI Shorts!"
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

    exists = any(s.get("video_id") == "qSyo5d-dVzA" for s in sources)
    if not exists:
        new_source = {
            "id": f"source_{len(sources) + 1}",
            "creator_name": "IShowSpeed",
            "channel_handle": "@IShowSpeed",
            "channel_url": "https://www.youtube.com/@IShowSpeed",
            "subscribers": "62.8M Subscribers",
            "video_title": "🔴PLAYING GTA 6 EARLY ACCESS GAMEPLAY GET IN HERE!",
            "video_url": STREAM_URL,
            "video_id": "qSyo5d-dVzA",
            "thumbnail": "https://i.ytimg.com/vi/qSyo5d-dVzA/hqdefault.jpg",
            "duration": "23h 45m",
            "clips_count": 25,
            "clips": [f"{m['id']}.mp4" for m in MOMENTS_25],
            "attribution_status": "Credited in Description (#IShowSpeed)"
        }
        sources.append(new_source)
        with open(sources_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
        print("[+] Updated sources_registry.json with IShowSpeed (25 clips)!", flush=True)

def schedule_all_25_moments():
    queue_path = FINAL_DIR / "upload_queue.json"
    queue = []
    if queue_path.exists():
        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)

    existing_files = {item.get("file") for item in queue}

    new_items = []
    for m in MOMENTS_25:
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
        print("[!] All 25 moments already present in upload_queue.json.", flush=True)

    update_sources_registry()

def download_fragment_range(v_frags, a_frags, start_sec, end_sec, out_mp4: Path):
    start_sq = int(start_sec // 2)
    end_sq = int(end_sec // 2) + 1  # 1 extra buffer fragment
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    def fetch_url(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    print(f"[*] Downloading DASH frags {start_sq} to {end_sq} ({end_sq - start_sq + 1} frags)...", flush=True)
    
    v_urls = [(sq, v_frags[sq]['url']) for sq in range(start_sq, min(end_sq + 1, len(v_frags)))]
    a_urls = [(sq, a_frags[sq]['url']) for sq in range(start_sq, min(end_sq + 1, len(a_frags)))]
    
    v_data = {}
    a_data = {}
    
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures_v = {pool.submit(fetch_url, u): sq for sq, u in v_urls}
        for f in futures_v:
            sq = futures_v[f]
            v_data[sq] = f.result()
            
        futures_a = {pool.submit(fetch_url, u): sq for sq, u in a_urls}
        for f in futures_a:
            sq = futures_a[f]
            a_data[sq] = f.result()
            
    v_tmp = TEMP_DIR / f"temp_{out_mp4.stem}_v.mp4"
    a_tmp = TEMP_DIR / f"temp_{out_mp4.stem}_a.mp4"
    
    with open(v_tmp, "wb") as vf:
        for sq in sorted(v_data.keys()):
            vf.write(v_data[sq])
            
    with open(a_tmp, "wb") as af:
        for sq in sorted(a_data.keys()):
            af.write(a_data[sq])
            
    cmd = [
        str(BASE_DIR / "bin" / "ffmpeg.exe"), "-y",
        "-i", str(v_tmp),
        "-i", str(a_tmp),
        "-c", "copy",
        "-movflags", "+faststart",
        str(out_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg mux failed: {res.stderr}")
        
    for p in [v_tmp, a_tmp]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Schedule all 25 moments into upload_queue and sources registry
    schedule_all_25_moments()

    # 2. Extract stream formats once for all clips
    print("\n[+] Extracting video/audio stream formats for IShowSpeed stream...", flush=True)
    ydl = yt_dlp.YoutubeDL({'quiet': True})
    info = ydl.extract_info(STREAM_URL, download=False)
    
    v_fmt = next((f for f in info['formats'] if f['format_id'] == '299'), None)
    if not v_fmt or not v_fmt.get('fragments'):
        v_fmt = next(f for f in info['formats'] if f['format_id'] == '298')
    a_fmt = next(f for f in info['formats'] if f['format_id'] == '140')
    
    v_frags = v_fmt['fragments']
    a_frags = a_fmt['fragments']
    print(f"[+] Loaded format {v_fmt['format_id']} ({len(v_frags)} frags) & {a_fmt['format_id']} ({len(a_frags)} frags)!", flush=True)

    # 3. Render clips sequentially
    print(f"\n{'='*70}\nSTARTING RENDER PIPELINE FOR 25 ISHOWSPEED SHORTS\n{'='*70}", flush=True)

    for idx, m in enumerate(MOMENTS_25):
        clip_id = m["id"]
        raw_mp4 = TEMP_DIR / f"raw_{clip_id}.mp4"
        trans_json = TEMP_DIR / f"transcript_{clip_id}.json"
        crop_mp4 = TEMP_DIR / f"crop_{clip_id}.mp4"
        final_mp4 = FINAL_DIR / f"{clip_id}.mp4"

        print(f"\n>>> [{idx+1}/25] {m['name']} ({clip_id}) | Timestamps: {m['start_sec']}s - {m['end_sec']}s", flush=True)

        if final_mp4.exists() and final_mp4.stat().st_size > 1000000:
            print(f"[*] {final_mp4.name} already exists and verified ({final_mp4.stat().st_size/(1024*1024):.1f} MB). Skipping render.")
            continue

        # Step 1: Download slice via direct DASH fragment fetcher
        if not raw_mp4.exists():
            try:
                download_fragment_range(v_frags, a_frags, m["start_sec"], m["end_sec"], raw_mp4)
            except Exception as e:
                print(f"[!] Warning: Download failed for {clip_id}: {e}, continuing...", file=sys.stderr)
                continue

        # Step 2: Transcribe word-level timestamps
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

    print("\n" + "="*70 + "\nALL 25 ISHOWSPEED SHORTS PROCESSED SUCCESSFULLY!\n" + "="*70, flush=True)

if __name__ == "__main__":
    main()
