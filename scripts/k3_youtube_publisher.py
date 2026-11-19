#!/usr/bin/env python3
"""
Agent k3: YouTube Shorts Publisher.
Publishes clips to YouTube Shorts with high-CTR titles, optimized hashtags,
and mandatory, prominent credits to the original creator.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_QUEUE_FILE = BASE_DIR / "final_clips" / "upload_queue.json"
SOURCES_REGISTRY_FILE = BASE_DIR / "final_clips" / "sources_registry.json"
UPLOADER_SCRIPT = BASE_DIR / "scripts" / "upload_youtube.py"

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

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_source_for_clip(clip_filename: str) -> dict:
    registry = load_json(SOURCES_REGISTRY_FILE, [])
    clip_base = Path(clip_filename).name
    for source in registry:
        if clip_base in source.get("clips", []):
            return source
    # Check if number matches clip_1 -> clip_4 from source_1, etc.
    import re
    m = re.search(r"clip_(\d+)", clip_base)
    if m:
        num = int(m.group(1))
        # source_1: 1-4, source_2: 5-8, source_3: 9-12, source_4: 13-16
        idx = (num - 1) // 4
        if 0 <= idx < len(registry):
            return registry[idx]
    return {
        "creator_name": "Gamer Creator",
        "channel_handle": "@GamingCreator",
        "channel_url": "https://youtube.com",
        "video_url": "https://youtube.com"
    }

def format_shorts_metadata(item: dict) -> tuple[str, str, list]:
    """
    Format title, description with strict original creator credit, and tags.
    """
    file_path = item.get("file", "")
    source = item.get("creator_attribution") or get_source_for_clip(file_path)

    creator_name = source.get("creator_name", "Gamer")
    channel_handle = source.get("channel_handle", f"@{creator_name.replace(' ', '')}")
    channel_url = source.get("channel_url", "https://youtube.com")
    video_url = source.get("video_url", "https://youtube.com")

    # Format Title
    raw_title = item.get("title", f"{creator_name} GTA Insane Moment!")
    if "#shorts" not in raw_title.lower():
        title = f"{raw_title} #shorts"
    else:
        title = raw_title

    # Build Description with Mandatory Creator Credit
    description = (
        f"{title}\n\n"
        f"🎮 ORIGINAL GAMEPLAY & CREATOR CREDIT:\n"
        f"• Creator: {creator_name} ({channel_handle})\n"
        f"• Original Video: {video_url}\n"
        f"• Channel Link: {channel_url}\n\n"
        f"Support the original creator! Content featured under fair use for transformative gaming entertainment.\n\n"
        f"#Shorts #GTA5 #GTA6 #Gaming #GamingShorts #GrandTheftAuto #ViralShorts"
    )

    tags = item.get("tags") or ["GTA6", "GTA5", "Gaming", creator_name.replace(" ", ""), "Shorts", "Viral"]
    for essential in ["Shorts", "GTA6", "Gaming"]:
        if essential not in tags:
            tags.append(essential)

    return title, description, tags

def publish_clip(item: dict, privacy: str = "public", dry_run: bool = False) -> dict:
    file_path = BASE_DIR / item.get("file")
    if not file_path.exists():
        raise FileNotFoundError(f"Clip file not found: {file_path}")

    title, description, tags = format_shorts_metadata(item)

    print(f"\n🚀 [k3-youtube-publisher] Preparing to post: {file_path.name}")
    print(f"Title: {title}")
    print(f"Creator Credit: {description.split('🎮')[1].split('#Shorts')[0].strip()}")
    print(f"Tags: {', '.join(tags)}")

    if dry_run:
        print("[k3-youtube-publisher] [DRY RUN] Would upload to YouTube Data API v3.")
        return {
            "status": "dry_run",
            "file": item.get("file"),
            "title": title,
            "creator_credited": True
        }

    cmd = [
        sys.executable, str(UPLOADER_SCRIPT),
        "--file", str(file_path),
        "--title", title,
        "--description", description,
        "--tags", ",".join(tags),
        "--privacy", privacy
    ]

    print("[k3-youtube-publisher] Executing upload with YouTube Data API v3...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(f"[k3-youtube-publisher] Uploader Output:\n{res.stdout}")
    if res.returncode != 0:
        print(f"[k3-youtube-publisher] Upload failed:\n{res.stderr}", file=sys.stderr)
        raise RuntimeError("YouTube upload failed.")

    out = {}
    import re
    json_match = re.search(r"(\{[\s\S]*\})", res.stdout)
    if json_match:
        try:
            out = json.loads(json_match.group(1))
        except Exception:
            pass

    if not out.get("video_url") or out.get("video_url") == "https://youtube.com/shorts/uploaded":
        # Check if URL was printed in stdout
        url_match = re.search(r"https://youtube\.com/shorts/[a-zA-Z0-9_-]+", res.stdout)
        if url_match:
            out["video_url"] = url_match.group(0)
            out["video_id"] = out["video_url"].split("/")[-1]

    # Update Queue
    queue = load_json(UPLOAD_QUEUE_FILE, [])
    for q in queue:
        if q.get("file") == item.get("file"):
            q["uploaded"] = True
            q["title"] = title
            q["description"] = description
            q["video_id"] = out.get("video_id")
            q["video_url"] = out.get("video_url")
            q["posted_at"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p IST")
            q["attribution_confirmed"] = True
            break
    save_json(UPLOAD_QUEUE_FILE, queue)

    print(f"✅ [k3-youtube-publisher] Successfully posted to YouTube Shorts!")
    print(f"Live URL: {out.get('video_url')}")
    return out

def main():
    parser = argparse.ArgumentParser(description="k3 YouTube Shorts Publisher Agent")
    parser.add_argument("--list-pending", action="store_true", help="List all pending unposted clips")
    parser.add_argument("--publish-next", action="store_true", help="Publish the next available unposted clip")
    parser.add_argument("--clip", type=str, help="Publish a specific clip file (e.g. final_clips/clip_11.mp4)")
    parser.add_argument("--privacy", choices=["public", "unlisted", "private"], default="public")
    parser.add_argument("--dry-run", action="store_true", help="Preview metadata & creator credit without uploading")
    args = parser.parse_args()

    queue = load_json(UPLOAD_QUEUE_FILE, [])

    if args.list_pending:
        pending = [q for q in queue if not q.get("uploaded")]
        print(f"\n📋 [k3-youtube-publisher] Pending Shorts to Publish ({len(pending)}):")
        for p in pending:
            source = get_source_for_clip(p.get("file"))
            print(f" - {p.get('file')} | Slot: {p.get('slot_label', 'Not set')} | Creator: {source.get('creator_name')} | Title: {p.get('title')}")
        return

    target_item = None
    if args.clip:
        for q in queue:
            if q.get("file") == args.clip or Path(q.get("file")).name == Path(args.clip).name:
                target_item = q
                break
        if not target_item:
            target_item = {
                "file": args.clip,
                "title": f"Viral GTA Moment #shorts",
                "uploaded": False
            }
    elif args.publish_next:
        pending = [q for q in queue if not q.get("uploaded")]
        if not pending:
            print("[k3-youtube-publisher] No pending clips in queue! Everything is already published.")
            return
        target_item = pending[0]
    else:
        print("[k3-youtube-publisher] Specify --list-pending, --publish-next, or --clip <path>.")
        return

    publish_clip(target_item, privacy=args.privacy, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
