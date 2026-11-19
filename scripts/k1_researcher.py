#!/usr/bin/env python3
"""
Agent k1: Gaming Video Researcher.
Discovers and monitors viral GTA 5, GTA 6, and trending gaming videos on YouTube.
Extracts complete creator attribution and queues videos for Shorts analysis by k2.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_REGISTRY_FILE = BASE_DIR / "final_clips" / "sources_registry.json"
RESEARCH_QUEUE_FILE = BASE_DIR / "final_clips" / "research_queue.json"

DEFAULT_GAMING_QUERIES = [
    "GTA 6 gameplay",
    "GTA 5 funny moments",
    "GTA 6 leaks",
    "GTA 5 insane stunts",
    "Techno Gamerz GTA",
    "theRadBrad GTA",
    "CarryMinati GTA 6",
    "Mythpat GTA 5"
]

def load_json_file(file_path: Path, default=None):
    if default is None:
        default = []
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[k1-researcher] Warning reading {file_path.name}: {e}", file=sys.stderr)
            return default
    return default

def save_json_file(file_path: Path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_duration(seconds: float) -> str:
    secs = int(seconds or 0)
    mins = secs // 60
    rem_secs = secs % 60
    hours = mins // 60
    rem_mins = mins % 60
    if hours > 0:
        return f"{hours}h {rem_mins:02d}m"
    return f"{rem_mins}m {rem_secs:02d}s"

def search_youtube_videos(query: str, max_results: int = 5) -> list:
    """
    Search YouTube via yt-dlp metadata extraction without downloading video files.
    """
    print(f"[k1-researcher] Searching YouTube for gaming query: '{query}' (limit: {max_results})...")
    search_target = f"ytsearch{max_results}:{query}"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        search_target,
        "--dump-single-json",
        "--flat-playlist",
        "--no-playlist",
        "--ignore-errors"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode != 0 and not res.stdout:
            print(f"[k1-researcher] yt-dlp search error: {res.stderr[:200]}", file=sys.stderr)
            return []
        data = json.loads(res.stdout)
        entries = data.get("entries", [])
        results = []
        for e in entries:
            if not e or not isinstance(e, dict):
                continue
            video_id = e.get("id")
            title = e.get("title", "")
            uploader = e.get("uploader") or e.get("channel") or "Gaming Creator"
            channel_url = e.get("channel_url") or f"https://www.youtube.com/@{uploader.replace(' ', '')}"
            duration = e.get("duration") or 0
            view_count = e.get("view_count") or 0
            url = e.get("url") or f"https://www.youtube.com/watch?v={video_id}"
            if not url.startswith("http"):
                url = f"https://www.youtube.com/watch?v={video_id}"
            
            results.append({
                "video_id": video_id,
                "video_title": title,
                "video_url": url,
                "creator_name": uploader,
                "channel_handle": f"@{uploader.replace(' ', '')}",
                "channel_url": channel_url,
                "duration_seconds": duration,
                "duration": format_duration(duration),
                "view_count": view_count,
                "thumbnail": e.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            })
        return results
    except Exception as e:
        print(f"[k1-researcher] Search failed: {e}", file=sys.stderr)
        return []

def register_candidate_video(video_info: dict) -> dict:
    """
    Register a gaming video into sources_registry and research_queue.
    """
    registry = load_json_file(SOURCES_REGISTRY_FILE, [])
    research_queue = load_json_file(RESEARCH_QUEUE_FILE, [])

    # Check if already in registry
    for item in registry:
        if item.get("video_id") == video_info.get("video_id") or item.get("video_url") == video_info.get("video_url"):
            print(f"[k1-researcher] Video already registered: {video_info.get('video_title')}")
            return item

    next_id = f"source_{len(registry) + 1}"
    record = {
        "id": next_id,
        "creator_name": video_info.get("creator_name", "Gaming Creator"),
        "channel_handle": video_info.get("channel_handle", "@GamingCreator"),
        "channel_url": video_info.get("channel_url", "https://youtube.com"),
        "subscribers": video_info.get("subscribers", "Verified Creator"),
        "video_title": video_info.get("video_title", ""),
        "video_url": video_info.get("video_url", ""),
        "video_id": video_info.get("video_id", ""),
        "thumbnail": video_info.get("thumbnail", ""),
        "duration": video_info.get("duration", "N/A"),
        "duration_seconds": video_info.get("duration_seconds", 0),
        "view_count": video_info.get("view_count", 0),
        "clips_count": 0,
        "clips": [],
        "attribution_status": f"Pending ({video_info.get('channel_handle')})",
        "discovered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    registry.append(record)
    save_json_file(SOURCES_REGISTRY_FILE, registry)

    # Add to research queue for k2
    task = {
        "id": f"task_{len(research_queue) + 1}",
        "source_id": next_id,
        "video_title": record["video_title"],
        "video_url": record["video_url"],
        "creator_name": record["creator_name"],
        "channel_handle": record["channel_handle"],
        "channel_url": record["channel_url"],
        "status": "pending_k2_analysis",
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    research_queue.append(task)
    save_json_file(RESEARCH_QUEUE_FILE, research_queue)

    print(f"[k1-researcher] Successfully registered candidate [{next_id}]: '{record['video_title']}' by {record['creator_name']}")
    return record

def main():
    parser = argparse.ArgumentParser(description="k1 Gaming Video Researcher Agent")
    parser.add_argument("--query", type=str, help="Search query (e.g. 'GTA 6 gameplay', 'GTA 5 stunts')")
    parser.add_argument("--creator", type=str, help="Search videos by specific creator name")
    parser.add_argument("--url", type=str, help="Directly register a YouTube video URL")
    parser.add_argument("--max-results", type=int, default=3, help="Max videos to discover per search")
    parser.add_argument("--list-queue", action="store_true", help="List all pending research candidates")
    parser.add_argument("--list-sources", action="store_true", help="List all tracked sources and creators")
    args = parser.parse_args()

    if args.list_sources:
        sources = load_json_file(SOURCES_REGISTRY_FILE, [])
        print(f"\n🎮 [k1-researcher] Tracked Sources & Creators ({len(sources)}):")
        for s in sources:
            print(f" - [{s.get('id')}] {s.get('video_title')} | Creator: {s.get('creator_name')} ({s.get('channel_handle')})")
        return

    if args.list_queue:
        queue = load_json_file(RESEARCH_QUEUE_FILE, [])
        print(f"\n📋 [k1-researcher] Pending Research Queue ({len(queue)}):")
        for q in queue:
            print(f" - [{q.get('source_id')}] Status: {q.get('status')} | {q.get('video_title')} (by {q.get('creator_name')})")
        return

    if args.url:
        print(f"[k1-researcher] Inspecting direct URL: {args.url}")
        # Probe metadata
        cmd = [sys.executable, "-m", "yt_dlp", args.url, "--dump-single-json", "--no-playlist", "--ignore-errors"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                uploader = data.get("uploader") or data.get("channel") or "Gaming Creator"
                info = {
                    "video_id": data.get("id"),
                    "video_title": data.get("title"),
                    "video_url": args.url,
                    "creator_name": uploader,
                    "channel_handle": f"@{uploader.replace(' ', '')}",
                    "channel_url": data.get("channel_url") or f"https://www.youtube.com/@{uploader.replace(' ', '')}",
                    "duration_seconds": data.get("duration", 0),
                    "duration": format_duration(data.get("duration", 0)),
                    "view_count": data.get("view_count", 0),
                    "thumbnail": data.get("thumbnail") or f"https://i.ytimg.com/vi/{data.get('id')}/hqdefault.jpg"
                }
                register_candidate_video(info)
                return
        except Exception as e:
            print(f"[k1-researcher] Direct URL probe failed: {e}", file=sys.stderr)

    query = args.query
    if args.creator:
        query = f"{args.creator} GTA 5 GTA 6" if not query else f"{args.creator} {query}"
    if not query:
        query = DEFAULT_GAMING_QUERIES[0]

    found_videos = search_youtube_videos(query, max_results=args.max_results)
    if not found_videos:
        print(f"[k1-researcher] No videos discovered for query '{query}'. (Check network connectivity)")
        return

    print(f"[k1-researcher] Discovered {len(found_videos)} gaming candidate videos:")
    for v in found_videos:
        register_candidate_video(v)

if __name__ == "__main__":
    main()
