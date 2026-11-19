#!/usr/bin/env python3
"""
Agent k4: Instagram Reels Publisher.
Formats high-engagement Instagram Reels captions with viral gaming hashtags,
ensures mandatory credits to the original creator, and handles publishing via
Meta Graph API (or Instagram Reels Queue).
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
INSTAGRAM_QUEUE_FILE = BASE_DIR / "final_clips" / "instagram_queue.json"
CONFIG_FILE = BASE_DIR / "credentials" / "instagram_config.json"

SESSION_FILE = BASE_DIR / "credentials" / "instagram_session.json"

DEFAULT_INSTAGRAM_HASHTAGS = [
    "#reels", "#reelsinstagram", "#gaming", "#gamingreels",
    "#gta5", "#gta6", "#gtav", "#grandtheftauto", "#rockstargames",
    "#gamingmemes", "#viralreels", "#explorepage", "#pcgaming", "#ps5"
]

DEFAULT_CONFIG = {
    "instagram_user_id": os.environ.get("INSTAGRAM_USER_ID", ""),
    "access_token": os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
    "page_handle": "@GamerClipsOfficial",
    "auto_publish_enabled": True
}

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
    import re
    m = re.search(r"clip_(\d+)", clip_base)
    if m:
        num = int(m.group(1))
        idx = (num - 1) // 4
        if 0 <= idx < len(registry):
            return registry[idx]
    return {
        "creator_name": "Gamer Creator",
        "channel_handle": "@GamingCreator",
        "channel_url": "https://youtube.com",
        "video_url": "https://youtube.com"
    }

def format_instagram_caption(item: dict) -> str:
    """
    Crafts an engaging, viral Instagram caption with prominent creator credit.
    """
    file_path = item.get("file", "")
    source = item.get("creator_attribution") or get_source_for_clip(file_path)

    creator_name = source.get("creator_name", "Gamer")
    channel_handle = source.get("channel_handle", f"@{creator_name.replace(' ', '')}")
    video_url = source.get("video_url", "https://youtube.com")
    raw_title = item.get("title", f"{creator_name} GTA Moment").replace("#shorts", "").strip()

    caption = (
        f"🔥 {raw_title}\n\n"
        f"Would you be able to survive this in GTA 6? Drop your thoughts below! 👇\n\n"
        f"✨ CREDITS TO ORIGINAL CREATOR:\n"
        f"• Creator: {creator_name} ({channel_handle})\n"
        f"• Original Video: {video_url}\n\n"
        f"📌 Follow for daily GTA 5 & GTA 6 clips and highlights!\n"
        f"⚠️ Tag or DM for credit updates or removal. All rights reserved to respective owners.\n\n"
        f"{' '.join(DEFAULT_INSTAGRAM_HASHTAGS)}"
    )
    return caption

def sync_instagram_queue():
    """
    Syncs ready clips from upload_queue.json into instagram_queue.json.
    """
    upload_queue = load_json(UPLOAD_QUEUE_FILE, [])
    insta_queue = load_json(INSTAGRAM_QUEUE_FILE, [])

    existing_files = {q.get("file") for q in insta_queue}

    added_count = 0
    for item in upload_queue:
        file_path = item.get("file")
        if file_path not in existing_files:
            caption = format_instagram_caption(item)
            insta_queue.append({
                "file": file_path,
                "title": item.get("title"),
                "caption": caption,
                "status": "ready_to_publish",
                "posted": False,
                "instagram_media_id": None,
                "published_at": None,
                "creator": item.get("creator_attribution", {}).get("creator_name", "Gamer")
            })
            added_count += 1

    save_json(INSTAGRAM_QUEUE_FILE, insta_queue)
    return insta_queue, added_count

def publish_to_instagram(item: dict, dry_run: bool = False) -> dict:
    file_path = BASE_DIR / item.get("file")
    if not file_path.exists():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    caption = item.get("caption") or format_instagram_caption(item)
    config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
    login_method = config.get("login_method", "direct")
    username = config.get("username")
    password = config.get("password")
    access_token = config.get("access_token") or os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    ig_user_id = config.get("instagram_user_id") or os.environ.get("INSTAGRAM_USER_ID")

    print(f"\n📸 [k4-instagram-publisher] Preparing Reel: {file_path.name}")
    print("=" * 60)
    print(caption)
    print("=" * 60)

    # Check if credentials exist
    has_direct_creds = SESSION_FILE.exists() or (username and password)
    has_meta_creds = bool(access_token and ig_user_id)

    if dry_run or (not has_direct_creds and not has_meta_creds):
        if not has_direct_creds and not has_meta_creds:
            print("[k4-instagram-publisher] Instagram account not yet configured!")
            print("👉 Run: .\\.venv\\Scripts\\python.exe scripts\\setup_instagram.py")
            print("[k4-instagram-publisher] Staging reel in instagram_queue.json as 'ready_to_publish'.")
        else:
            print("[k4-instagram-publisher] [DRY RUN] Would publish to Instagram Reels with full creator credits.")
        
        return {
            "status": "staged_ready",
            "file": item.get("file"),
            "caption": caption,
            "creator_credited": True
        }

    # METHOD 1: Direct Instagrapi Upload (Handles local files automatically)
    if has_direct_creds and login_method != "meta_api":
        try:
            from instagrapi import Client
            cl = Client()
            if SESSION_FILE.exists():
                try:
                    cl.load_settings(str(SESSION_FILE))
                except Exception:
                    pass
            if username and password:
                print(f"[k4-instagram-publisher] Logging in to Instagram as @{username}...")
                cl.login(username, password)
                cl.dump_settings(str(SESSION_FILE))

            print(f"[k4-instagram-publisher] Uploading Reel ({file_path.name}) to Instagram...")
            media = cl.clip_upload(file_path, caption=caption)
            media_id = str(media.id)
            code = getattr(media, "code", "")
            reel_url = f"https://www.instagram.com/reel/{code}/" if code else f"https://www.instagram.com/p/{media_id}/"

            print(f"✅ [k4-instagram-publisher] Successfully posted Reel to Instagram!")
            print(f"Live Reel URL: {reel_url}")

            # Update Queue
            insta_queue = load_json(INSTAGRAM_QUEUE_FILE, [])
            for q in insta_queue:
                if q.get("file") == item.get("file"):
                    q["posted"] = True
                    q["status"] = "published"
                    q["instagram_media_id"] = media_id
                    q["reel_url"] = reel_url
                    q["published_at"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p IST")
                    break
            save_json(INSTAGRAM_QUEUE_FILE, insta_queue)
            return {"status": "success", "media_id": media_id, "reel_url": reel_url}
        except Exception as e:
            print(f"[k4-instagram-publisher] Direct upload error: {e}", file=sys.stderr)
            raise

    # METHOD 2: Meta Graph API (Requires publicly accessible video_url)
    if has_meta_creds:
        import requests
        print(f"[k4-instagram-publisher] Uploading Reel via Meta Graph API for Account {ig_user_id}...")
        publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        payload = {
            "media_type": "REELS",
            "caption": caption,
            "access_token": access_token
        }
        video_public_url = item.get("video_public_url")
        if video_public_url:
            payload["video_url"] = video_public_url

        try:
            r = requests.post(publish_url, data=payload, timeout=30)
            res_data = r.json()
            if "id" in res_data:
                creation_id = res_data["id"]
                pub_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
                pub_res = requests.post(pub_url, data={"creation_id": creation_id, "access_token": access_token}, timeout=30)
                pub_json = pub_res.json()
                media_id = pub_json.get("id", creation_id)
                reel_url = f"https://www.instagram.com/reel/{media_id}/"
                print(f"✅ [k4-instagram-publisher] Published Reel successfully via Graph API! Media ID: {media_id}")
                
                insta_queue = load_json(INSTAGRAM_QUEUE_FILE, [])
                for q in insta_queue:
                    if q.get("file") == item.get("file"):
                        q["posted"] = True
                        q["status"] = "published"
                        q["instagram_media_id"] = media_id
                        q["reel_url"] = reel_url
                        q["published_at"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p IST")
                        break
                save_json(INSTAGRAM_QUEUE_FILE, insta_queue)
                return {"status": "success", "media_id": media_id}
            else:
                print(f"[k4-instagram-publisher] Meta API returned: {res_data}")
                return {"status": "error", "response": res_data}
        except Exception as e:
            print(f"[k4-instagram-publisher] Error publishing to Instagram: {e}", file=sys.stderr)
            return {"status": "error", "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="k4 Instagram Reels Publisher Agent")
    parser.add_argument("--sync-queue", action="store_true", help="Sync all rendered shorts into Instagram queue")
    parser.add_argument("--list-queue", action="store_true", help="List all Instagram reels in queue")
    parser.add_argument("--publish-next", action="store_true", help="Publish next ready reel")
    parser.add_argument("--clip", type=str, help="Publish a specific clip (e.g. final_clips/clip_1.mp4)")
    parser.add_argument("--dry-run", action="store_true", help="Preview caption, hashtags and credits without publishing")
    args = parser.parse_args()

    if args.sync_queue:
        q, count = sync_instagram_queue()
        print(f"📸 [k4-instagram-publisher] Synced Instagram queue. {count} new reels added (Total: {len(q)}).")
        return

    if args.list_queue:
        q = load_json(INSTAGRAM_QUEUE_FILE, [])
        if not q:
            sync_instagram_queue()
            q = load_json(INSTAGRAM_QUEUE_FILE, [])
        print(f"\n📸 [k4-instagram-publisher] Instagram Reels Queue ({len(q)}):")
        for idx, item in enumerate(q):
            status = "✅ Posted" if item.get("posted") else "⏳ Ready"
            print(f" #{idx+1:02d} [{status}] {item.get('file')} | Creator: {item.get('creator')} | Title: {item.get('title')}")
        return

    target = None
    insta_queue = load_json(INSTAGRAM_QUEUE_FILE, [])
    if not insta_queue:
        sync_instagram_queue()
        insta_queue = load_json(INSTAGRAM_QUEUE_FILE, [])

    if args.clip:
        for item in insta_queue:
            if item.get("file") == args.clip or Path(item.get("file")).name == Path(args.clip).name:
                target = item
                break
        if not target:
            target = {
                "file": args.clip,
                "title": "GTA Viral Reel",
                "caption": format_instagram_caption({"file": args.clip})
            }
    elif args.publish_next:
        unposted = [i for i in insta_queue if not i.get("posted")]
        if not unposted:
            print("[k4-instagram-publisher] No pending reels in queue! Run --sync-queue to import new clips.")
            return
        target = unposted[0]
    else:
        print("[k4-instagram-publisher] Please specify --sync-queue, --list-queue, --publish-next, or --clip <path>.")
        return

    publish_to_instagram(target, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
