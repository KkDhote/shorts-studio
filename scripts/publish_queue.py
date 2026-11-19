#!/usr/bin/env python3
"""
Autonomous Queue Publisher.
Iterates through a JSON manifest of clips and uploads them to YouTube automatically.
Can apply interval spacing (e.g. 2 hours between uploads or scheduled drops).
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from upload_youtube import get_authenticated_service, upload_video

def process_queue(manifest_path: str, interval_minutes: int = 0):
    if not os.path.exists(manifest_path):
        print(f"[queue] Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        queue = json.load(f)

    if not queue:
        print("[queue] Queue is empty.")
        return

    print(f"[queue] Loaded {len(queue)} items from {manifest_path}")
    youtube = get_authenticated_service()

    results = []
    for idx, item in enumerate(queue):
        file_path = item.get("file")
        title = item.get("title")
        description = item.get("description", "")
        tags = item.get("tags", [])
        privacy = item.get("privacy", "public")
        schedule = item.get("schedule", None)
        category = item.get("category", "20")

        print(f"\n[queue] Processing [{idx+1}/{len(queue)}]: {file_path}")
        try:
            res = upload_video(
                youtube=youtube,
                file_path=file_path,
                title=title,
                description=description,
                tags=tags,
                category_id=category,
                privacy_status=privacy,
                publish_at=schedule
            )
            item["uploaded"] = True
            item["result"] = res
            results.append(res)
        except Exception as e:
            print(f"[queue] Error uploading {file_path}: {e}", file=sys.stderr)
            item["uploaded"] = False
            item["error"] = str(e)

        # Write updated status back to manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)

        if interval_minutes > 0 and idx < len(queue) - 1:
            print(f"[queue] Waiting {interval_minutes} minutes before next upload...")
            time.sleep(interval_minutes * 60)

    print("\n[queue] All queue items finished!")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and upload a queue of clips to YouTube.")
    parser.add_argument("-m", "--manifest", default="final_clips/upload_queue.json", help="Path to JSON manifest")
    parser.add_argument("--interval", type=int, default=0, help="Interval in minutes between successive uploads")
    args = parser.parse_args()

    process_queue(args.manifest, args.interval)
