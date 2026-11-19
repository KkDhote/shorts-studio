#!/usr/bin/env python3
"""
Agent k2: Shorts & Meme Content Creator.
Analyzes gaming videos, extracts high-retention hooks, creates 9:16 vertical crops,
adds meme content and banners, burns karaoke captions, and links original creator attribution.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.meme_enhancer import add_meme_header_banner, select_meme_hook
from scripts.auto_scheduler import allocate_slots_for_new_clips

SOURCES_REGISTRY_FILE = BASE_DIR / "final_clips" / "sources_registry.json"
RESEARCH_QUEUE_FILE = BASE_DIR / "final_clips" / "research_queue.json"
UPLOAD_QUEUE_FILE = BASE_DIR / "final_clips" / "upload_queue.json"

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

def find_source_info(source_id: str = None, video_url: str = None) -> dict:
    registry = load_json(SOURCES_REGISTRY_FILE, [])
    for s in registry:
        if source_id and s.get("id") == source_id:
            return s
        if video_url and (s.get("video_url") == video_url or s.get("video_id") in video_url):
            return s
    return {
        "id": "source_custom",
        "creator_name": "Original Gaming Creator",
        "channel_handle": "@GamingCreator",
        "channel_url": "https://youtube.com",
        "video_title": "Epic Gaming Highlight",
        "video_url": video_url or "https://youtube.com"
    }

def get_next_clip_id() -> int:
    queue = load_json(UPLOAD_QUEUE_FILE, [])
    max_id = 0
    for item in queue:
        file_path = item.get("file", "")
        # match clip_(\d+)
        import re
        m = re.search(r"clip_(\d+)", file_path)
        if m:
            max_id = max(max_id, int(m.group(1)))
    # Also check directory
    final_clips_dir = BASE_DIR / "final_clips"
    for p in final_clips_dir.glob("clip_*.mp4"):
        import re
        m = re.search(r"clip_(\d+)", p.name)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id + 1

def run_k2_creator(
    input_video: str,
    source_info: dict,
    num_clips: int = 2,
    add_memes: bool = True,
    model: str = "small"
) -> list:
    """
    Executes pipeline and meme enhancement for the input video.
    """
    print(f"\n✂️ [k2-shorts-creator] Starting video analysis for: {source_info.get('video_title')}")
    print(f"[k2-shorts-creator] Original Creator: {source_info.get('creator_name')} ({source_info.get('channel_handle')})")

    # Call pipeline.py
    pipeline_script = BASE_DIR / "scripts" / "pipeline.py"
    temp_dir = BASE_DIR / "temp_work"
    final_dir = BASE_DIR / "final_clips"

    cmd = [
        sys.executable, str(pipeline_script),
        "--input", input_video,
        "--output-dir", str(final_dir),
        "--temp-dir", str(temp_dir),
        "--model", model,
        "--num-clips", str(num_clips)
    ]

    print("[k2-shorts-creator] Running transcription, hook scoring & smart cropping...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[k2-shorts-creator] Pipeline error:\n{res.stderr}", file=sys.stderr)
        raise RuntimeError("Pipeline failed to create shorts")

    try:
        pipeline_output = json.loads(res.stdout)
    except Exception:
        # Parse last json block
        lines = res.stdout.strip().split("\n")
        json_str = ""
        recording = False
        for line in lines:
            if line.strip().startswith("{"):
                recording = True
            if recording:
                json_str += line
        pipeline_output = json.loads(json_str) if json_str else {"clips": []}

    created_clips = pipeline_output.get("clips", [])
    print(f"[k2-shorts-creator] Pipeline extracted {len(created_clips)} raw clips.")

    processed_results = []
    upload_queue = load_json(UPLOAD_QUEUE_FILE, [])

    for c in created_clips:
        raw_clip_path = Path(c["file_path"])
        clip_num = get_next_clip_id()
        hook_slug = c.get("hook", "moment")[:24].replace(" ", "_")
        final_filename = f"clip_{clip_num}.mp4"
        final_clip_path = final_dir / final_filename

        hook_text = c.get("hook", "")
        meme_banner_text = select_meme_hook(hook_text)

        if add_memes:
            print(f"[k2-shorts-creator] Injecting meme header: '{meme_banner_text}'")
            success = add_meme_header_banner(
                str(raw_clip_path),
                str(final_clip_path),
                meme_text=meme_banner_text
            )
            if not success or not final_clip_path.exists():
                # fallback rename
                raw_clip_path.rename(final_clip_path)
            else:
                if raw_clip_path.exists() and raw_clip_path != final_clip_path:
                    raw_clip_path.unlink()
        else:
            raw_clip_path.rename(final_clip_path)

        # Build Title & Description with creator attribution
        creator_name = source_info.get("creator_name", "Gamer")
        channel_handle = source_info.get("channel_handle", "@Gamer")
        video_url = source_info.get("video_url", "")

        viral_title = f"{creator_name} GTA Insane Moment! 💀 #shorts"
        if "fail" in hook_text.lower():
            viral_title = f"HE REALLY FAILED THIS?! GTA 6 Moment 😭 #shorts"
        elif "stunt" in hook_text.lower() or "jump" in hook_text.lower():
            viral_title = f"INSANE Stunt by {creator_name}! 🚀 #shorts"

        description = (
            f"Watch this viral gaming highlight from {creator_name}!\n\n"
            f"🎮 Original Gameplay Credit:\n"
            f"Creator: {creator_name} ({channel_handle})\n"
            f"Original Video: {video_url}\n\n"
            f"Support the original creator! Curated under fair use for entertainment.\n\n"
            f"#Shorts #GTA5 #GTA6 #Gaming #Trending"
        )

        queue_item = {
            "file": f"final_clips/{final_filename}",
            "title": viral_title,
            "description": description,
            "tags": ["GTA6", "GTA5", "Gaming", creator_name.replace(" ", ""), "Shorts"],
            "privacy": "public",
            "category": "20",
            "uploaded": False,
            "creator_attribution": {
                "creator_name": creator_name,
                "channel_handle": channel_handle,
                "channel_url": source_info.get("channel_url", ""),
                "video_url": video_url,
                "source_id": source_info.get("id", "source_1")
            },
            "meme_banner": meme_banner_text if add_memes else None,
            "hook": hook_text,
            "duration": c.get("duration", 0),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        upload_queue.append(queue_item)
        processed_results.append(queue_item)

    # Save updated upload queue & auto-schedule
    save_json(UPLOAD_QUEUE_FILE, upload_queue)
    allocate_slots_for_new_clips(processed_results, queue_file=UPLOAD_QUEUE_FILE)

    # Update source registry with created clips
    registry = load_json(SOURCES_REGISTRY_FILE, [])
    for s in registry:
        if s.get("id") == source_info.get("id"):
            for res_item in processed_results:
                s.setdefault("clips", []).append(Path(res_item["file"]).name)
            s["clips_count"] = len(s.get("clips", []))
            s["attribution_status"] = f"Credited in Description ({source_info.get('channel_handle')})"
    save_json(SOURCES_REGISTRY_FILE, registry)

    print(f"✅ [k2-shorts-creator] Successfully processed {len(processed_results)} Shorts with meme content!")
    return processed_results

def main():
    parser = argparse.ArgumentParser(description="k2 Shorts & Meme Creator Agent")
    parser.add_argument("--auto-queue", action="store_true", help="Process the next video from k1 research queue")
    parser.add_argument("--source-id", type=str, help="Process video from sources_registry.json by ID (e.g. source_1)")
    parser.add_argument("--input", type=str, help="Direct video path or YouTube URL")
    parser.add_argument("--num-clips", type=int, default=2, help="Number of clips to generate (default: 2)")
    parser.add_argument("--no-memes", action="store_true", help="Disable meme overlays/banners")
    parser.add_argument("--model", type=str, default="small", choices=["tiny", "base", "small", "medium"])
    args = parser.parse_args()

    input_video = None
    source_info = None

    if args.auto_queue:
        queue = load_json(RESEARCH_QUEUE_FILE, [])
        pending = [q for q in queue if q.get("status") == "pending_k2_analysis"]
        if not pending:
            print("[k2-shorts-creator] No pending tasks in research queue. Run k1 to discover videos first!")
            return
        task = pending[0]
        source_info = find_source_info(source_id=task.get("source_id"), video_url=task.get("video_url"))
        input_video = task.get("video_url")
        print(f"[k2-shorts-creator] Picked task from queue: {task.get('video_title')}")
        task["status"] = "processing_by_k2"
        save_json(RESEARCH_QUEUE_FILE, queue)

    elif args.source_id:
        source_info = find_source_info(source_id=args.source_id)
        input_video = source_info.get("video_url")

    elif args.input:
        input_video = args.input
        source_info = find_source_info(video_url=args.input)

    else:
        print("[k2-shorts-creator] Please specify --auto-queue, --source-id, or --input!")
        return

    res = run_k2_creator(
        input_video=input_video,
        source_info=source_info,
        num_clips=args.num_clips,
        add_memes=not args.no_memes,
        model=args.model
    )
    print(f"\nCreated {len(res)} Shorts:")
    for r in res:
        print(f" - {r['file']} | Title: {r['title']} | Schedule: {r.get('slot_label', 'Unscheduled')}")

if __name__ == "__main__":
    main()
