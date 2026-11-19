#!/usr/bin/env python3
"""
Master Orchestrator for the 4 Gaming Content Agents:
- k1: YouTube Gaming Researcher (GTA 5, GTA 6 & Viral Gaming)
- k2: Shorts & Meme Creator (Hook extraction, 9:16 crop, meme enhancers, karaoke captions)
- k3: YouTube Shorts Publisher (SEO titles, hashtags, creator attribution)
- k4: Instagram Reels Publisher (Instagram captions, viral hashtags, creator attribution)
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_FILE = BASE_DIR / "final_clips" / "sources_registry.json"
RESEARCH_QUEUE_FILE = BASE_DIR / "final_clips" / "research_queue.json"
UPLOAD_QUEUE_FILE = BASE_DIR / "final_clips" / "upload_queue.json"
INSTA_QUEUE_FILE = BASE_DIR / "final_clips" / "instagram_queue.json"

def load_json(path: Path, default=None):
    if default is None:
        default = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def print_status_summary():
    sources = load_json(SOURCES_FILE, [])
    research_q = load_json(RESEARCH_QUEUE_FILE, [])
    yt_queue = load_json(UPLOAD_QUEUE_FILE, [])
    ig_queue = load_json(INSTA_QUEUE_FILE, [])

    yt_pending = [q for q in yt_queue if not q.get("uploaded")]
    yt_posted = [q for q in yt_queue if q.get("uploaded")]
    ig_pending = [q for q in ig_queue if not q.get("posted")]
    ig_posted = [q for q in ig_queue if q.get("posted")]

    print("\n" + "=" * 65)
    print(" 🎮 4-AGENT GAMING SHORTS & REELS STUDIO STATUS ")
    print("=" * 65)
    print(f" 🔍 k1 (Researcher):       {len(sources)} Tracked Creators/Videos | {len(research_q)} In Queue")
    print(f" ✂️ k2 (Shorts Creator):   {len(yt_queue)} Rendered Shorts with Karaoke & Memes")
    print(f" 🚀 k3 (YouTube Pub):      {len(yt_posted)} Published | {len(yt_pending)} Pending Scheduled")
    print(f" 📸 k4 (Instagram Pub):    {len(ig_posted)} Published | {len(ig_pending)} Ready in Queue")
    print("=" * 65 + "\n")

def run_agent(agent_name: str, extra_args: list = None):
    py = sys.executable
    if extra_args is None:
        extra_args = []

    if agent_name == "k1":
        script = BASE_DIR / "scripts" / "k1_researcher.py"
    elif agent_name == "k2":
        script = BASE_DIR / "scripts" / "k2_shorts_creator.py"
    elif agent_name == "k3":
        script = BASE_DIR / "scripts" / "k3_youtube_publisher.py"
    elif agent_name == "k4":
        script = BASE_DIR / "scripts" / "k4_instagram_publisher.py"
    else:
        print(f"Unknown agent: {agent_name}. Must be k1, k2, k3, or k4.")
        return

    cmd = [py, str(script)] + extra_args
    print(f"\n▶️ Running Agent {agent_name}: {' '.join(cmd)}")
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Gaming Pipeline Orchestrator (k1, k2, k3, k4)")
    parser.add_argument("--status", action="store_true", help="Display status of all 4 agents and queues")
    parser.add_argument("--agent", choices=["k1", "k2", "k3", "k4"], help="Trigger a specific agent")
    parser.add_argument("--all", action="store_true", help="Run full pipeline: k1 -> k2 -> k3 -> k4")
    parser.add_argument("--query", type=str, help="Search query for k1 researcher")
    parser.add_argument("--clip", type=str, help="Target clip for k3 or k4")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for publishers")
    args, unknown = parser.parse_known_args()

    if args.status or (not args.agent and not args.all):
        print_status_summary()
        return

    if args.agent:
        extra = []
        if args.query:
            extra.extend(["--query", args.query])
        if args.clip:
            extra.extend(["--clip", args.clip])
        if args.dry_run:
            extra.append("--dry-run")
        extra.extend(unknown)
        run_agent(args.agent, extra)
        return

    if args.all:
        print("🌟 Executing Full Autonomous 4-Agent Pipeline...")
        # Step 1: k1 research
        q = args.query or "GTA 6 gameplay"
        run_agent("k1", ["--query", q, "--max-results", "2"])
        # Step 2: k2 create
        run_agent("k2", ["--auto-queue", "--num-clips", "2"])
        # Step 3: k3 publish youtube
        run_agent("k3", ["--publish-next", "--dry-run" if args.dry_run else "--privacy", "public"])
        # Step 4: k4 publish instagram
        run_agent("k4", ["--sync-queue"])
        run_agent("k4", ["--publish-next", "--dry-run" if args.dry_run else ""])
        print_status_summary()

if __name__ == "__main__":
    main()
