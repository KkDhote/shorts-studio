#!/usr/bin/env python3
"""
Shorts Studio & Profit Maximizer: Web App & Autonomous Auto-Pilot Engine.
Provides 2 dedicated views:
  1. Clips Studio (Ready to post & Already published)
  2. Channel Growth & Monetization Analytics
Includes background Auto-Pilot worker that automatically publishes clips
if the creator forgets or misses the scheduled window.
"""

import os
import sys
import json
import glob
import time
import threading
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from scripts.auto_scheduler import sync_unassigned_clips, allocate_slots_for_new_clips
FINAL_CLIPS_DIR = BASE_DIR / "final_clips"
CREDENTIALS_DIR = BASE_DIR / "credentials"
MANIFEST_FILE = FINAL_CLIPS_DIR / "upload_queue.json"
SETTINGS_FILE = BASE_DIR / "final_clips" / "autopilot_settings.json"
AUTOPILOT_LOG_FILE = BASE_DIR / "final_clips" / "autopilot_history.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "client_secret.json"

app = Flask(__name__, static_folder="static", template_folder="static")

DEFAULT_SETTINGS = {
    "autopilot_enabled": True,
    "shorts_per_day": 3,
    "fallback_timeout_minutes": 5,
    "auto_schedule_next_peak": True,
    "notify_on_post": True
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)

def load_queue():
    if MANIFEST_FILE.exists():
        try:
            return sync_unassigned_clips(MANIFEST_FILE)
        except Exception:
            try:
                with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
    return []

def save_queue(queue):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def log_autopilot_event(event):
    history = []
    if AUTOPILOT_LOG_FILE.exists():
        try:
            with open(AUTOPILOT_LOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.insert(0, event)
    with open(AUTOPILOT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:50], f, indent=2, ensure_ascii=False)

def get_authenticated_youtube():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    if os.environ.get("YOUTUBE_TOKEN_JSON"):
        try:
            creds_data = json.loads(os.environ["YOUTUBE_TOKEN_JSON"])
            creds = Credentials.from_authorized_user_info(creds_data)
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            print(f"[app] Error loading YOUTUBE_TOKEN_JSON env: {e}", file=sys.stderr)

    if not TOKEN_FILE.exists():
        return None

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)
    return build("youtube", "v3", credentials=creds)

# -------------------------------------------------------------
# AUTONOMOUS AUTO-PILOT WORKER THREAD
# -------------------------------------------------------------
def autopilot_daemon_loop():
    """
    Background worker that runs every 30 seconds.
    If the creator forgets to post a scheduled clip, Auto-Pilot
    automatically triggers publication to protect channel momentum!
    """
    print("[Auto-Pilot] Autonomous Scheduler Thread Initialized.")
    while True:
        try:
            settings = load_settings()
            if settings.get("autopilot_enabled", True):
                queue = load_queue()
                now_utc = datetime.now(timezone.utc)
                now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))

                for item in queue:
                    if item.get("uploaded", False):
                        continue

                    schedule_str = item.get("schedule")
                    file_path = item.get("file")
                    if not file_path or not os.path.exists(file_path):
                        continue

                    should_auto_post = False
                    reason = ""

                    if schedule_str:
                        try:
                            # Parse ISO 8601 or simple time
                            sched_dt = datetime.fromisoformat(schedule_str.replace("Z", "+00:00"))
                            grace = timedelta(minutes=int(settings.get("fallback_timeout_minutes", 5)))
                            if now_utc >= (sched_dt + grace):
                                should_auto_post = True
                                reason = f"Scheduled drop time ({schedule_str}) passed and was unreviewed."
                        except Exception:
                            pass

                    # Check scheduled date and slot
                    sched_date_str = item.get("scheduled_date") # e.g. "2026-11-19"
                    valid_slots = ["12:30 PM IST", "05:00 PM IST", "08:30 PM IST", "04:30 PM IST", "07:30 PM IST", "09:45 PM IST"]
                    if schedule_str in valid_slots:
                        date_target = sched_date_str or now_ist.strftime('%Y-%m-%d')
                        target_hour_min = schedule_str.replace(" IST", "")
                        target_dt = datetime.strptime(f"{date_target} {target_hour_min}", "%Y-%m-%d %I:%M %p").replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
                        grace = timedelta(minutes=int(settings.get("fallback_timeout_minutes", 5)))
                        if now_ist >= (target_dt + grace):
                            should_auto_post = True
                            reason = f"Scheduled drop slot ({date_target} {schedule_str}) passed. Autonomous fallback triggered!"

                    # 3-Shorts-Per-Day Algorithmic Safeguard
                    shorts_per_day = int(settings.get("shorts_per_day", 3))
                    today_str = now_ist.strftime("%Y-%m-%d")

                    # Count how many shorts have been posted today
                    posts_today = sum(
                        1 for q in queue 
                        if q.get("uploaded", False) and str(q.get("posted_at", "")).startswith(today_str)
                    )

                    if posts_today >= shorts_per_day:
                        # Daily quota met; prevent spam and preserve algorithm retention
                        continue

                    if should_auto_post:
                        print(f"\n[Auto-Pilot] 🤖 TRIGGERED for '{item.get('title')}': {reason}")
                        print(f"[Auto-Pilot] Publishing {file_path} autonomously to YouTube...")

                        python_exe = sys.executable
                        uploader_script = str(BASE_DIR / "scripts" / "upload_youtube.py")

                        title = item.get("title", "Viral Short #shorts")
                        desc = item.get("description", "")
                        affiliate = item.get("affiliate_deal", "")
                        if affiliate and affiliate not in desc:
                            desc += f"\n\n⚡ Exclusive Deal: {affiliate}"

                        tags = item.get("tags", ["Shorts", "Gaming"])
                        cmd = [
                            python_exe,
                            uploader_script,
                            "-i", file_path,
                            "-t", title,
                            "-d", desc,
                            "--tags", ",".join(tags) if isinstance(tags, list) else tags,
                            "-p", item.get("privacy", "public")
                        ]

                        proc = subprocess.run(cmd, capture_output=True, text=True)
                        if proc.returncode == 0:
                            res_json = json.loads(proc.stdout.strip().split("\n")[-1])
                            item["uploaded"] = True
                            item["video_id"] = res_json.get("video_id")
                            item["video_url"] = res_json.get("video_url")
                            item["auto_posted"] = True
                            item["posted_at"] = now_ist.strftime("%Y-%m-%d %I:%M:%S %p IST")
                            save_queue(queue)

                            log_autopilot_event({
                                "file": file_path,
                                "title": title,
                                "video_url": res_json.get("video_url"),
                                "reason": reason,
                                "timestamp": now_ist.strftime("%Y-%m-%d %I:%M:%S %p IST"),
                                "status": "published_successfully"
                            })
                            print(f"[Auto-Pilot] ✅ Successfully published {res_json.get('video_url')}!\n")
                        else:
                            print(f"[Auto-Pilot] ❌ Upload failed: {proc.stderr}\n")

        except Exception as e:
            print(f"[Auto-Pilot] Error in loop: {e}", file=sys.stderr)

        time.sleep(30)

# Start background thread
autopilot_thread = threading.Thread(target=autopilot_daemon_loop, daemon=True)
autopilot_thread.start()

# -------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory(FINAL_CLIPS_DIR, filename)

@app.route("/api/status", methods=["GET"])
def api_status():
    queue = load_queue()
    uploaded_count = sum(1 for item in queue if item.get("uploaded", False))
    ready_count = len(queue) - uploaded_count
    settings = load_settings()

    return jsonify({
        "channel_title": "KULDEEPBHAI GAMER",
        "autopilot_enabled": settings.get("autopilot_enabled", True),
        "queue_stats": {
            "total_clips": len(queue),
            "uploaded": uploaded_count,
            "ready": ready_count
        }
    })

@app.route("/api/clips", methods=["GET"])
def api_clips():
    queue = load_queue()
    queue_map = {item["file"]: item for item in queue}

    all_files = sorted(glob.glob(str(FINAL_CLIPS_DIR / "*.mp4")))
    clips_data = []

    for f in all_files:
        rel_path = f"final_clips/{os.path.basename(f)}"
        file_size = os.path.getsize(f) / (1024 * 1024)

        item = queue_map.get(rel_path, {})
        clips_data.append({
            "file": rel_path,
            "filename": os.path.basename(f),
            "size_mb": round(file_size, 2),
            "title": item.get("title", f"GTA VI Viral Highlight #{os.path.basename(f)}"),
            "description": item.get("description", ""),
            "tags": item.get("tags", ["Shorts", "GTA6", "Gaming"]),
            "privacy": item.get("privacy", "public"),
            "schedule": item.get("schedule", None),
            "approved": item.get("approved", False),
            "uploaded": item.get("uploaded", False),
            "video_url": item.get("video_url", None),
            "auto_posted": item.get("auto_posted", False),
            "posted_at": item.get("posted_at", None),
            "pinned_comment": item.get("pinned_comment", "🔥 Which moment was your favorite? Subscribe for daily GTA VI Shorts!"),
            "affiliate_deal": item.get("affiliate_deal", "")
        })

    return jsonify({"clips": clips_data})

@app.route("/api/growth", methods=["GET"])
def api_growth():
    """
    Returns channel growth analytics:
    Subscribers, Views, Videos, YPP progress, video performance table.
    """
    try:
        youtube = get_authenticated_youtube()
        if not youtube:
            return jsonify({"connected": False, "error": "No token found"}), 400

        ch_res = youtube.channels().list(mine=True, part="snippet,statistics,contentDetails").execute()
        ch = ch_res["items"][0]
        stats = ch["statistics"]

        subs = int(stats.get("subscriberCount", 0))
        views = int(stats.get("viewCount", 0))
        video_count = int(stats.get("videoCount", 0))

        # Fetch recent uploads
        uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        pl_res = youtube.playlistItems().list(playlistId=uploads_id, part="snippet,contentDetails", maxResults=12).execute()
        video_ids = [item["contentDetails"]["videoId"] for item in pl_res.get("items", [])]

        recent_videos = []
        if video_ids:
            v_res = youtube.videos().list(id=",".join(video_ids), part="snippet,statistics").execute()
            for v in v_res.get("items", []):
                snippet = v["snippet"]
                v_stats = v["statistics"]
                recent_videos.append({
                    "id": v["id"],
                    "title": snippet["title"],
                    "url": f"https://youtube.com/shorts/{v['id']}",
                    "published_at": snippet["publishedAt"][:10],
                    "thumbnail": snippet["thumbnails"]["default"]["url"],
                    "views": int(v_stats.get("viewCount", 0)),
                    "likes": int(v_stats.get("likeCount", 0)),
                    "comments": int(v_stats.get("commentCount", 0))
                })

        # Calculate YPP Milestones
        sub_progress = min(round((subs / 1000) * 100, 1), 100)
        shorts_view_progress = min(round((views / 10000000) * 100, 3), 100)

        # Autopilot history
        history = []
        if AUTOPILOT_LOG_FILE.exists():
            try:
                with open(AUTOPILOT_LOG_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        return jsonify({
            "connected": True,
            "channel": {
                "title": ch["snippet"]["title"],
                "custom_url": ch["snippet"].get("customUrl", ""),
                "thumbnail": ch["snippet"]["thumbnails"]["default"]["url"],
                "subscribers": subs,
                "total_views": views,
                "total_videos": video_count
            },
            "milestones": {
                "subscribers": {"current": subs, "target": 1000, "percent": sub_progress},
                "shorts_views": {"current": views, "target": 10000000, "percent": shorts_view_progress}
            },
            "recent_videos": recent_videos,
            "autopilot_history": history
        })

    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 500

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        data = request.json or {}
        current = load_settings()
        current.update(data)
        save_settings(current)
        return jsonify({"status": "success", "settings": current})
    return jsonify({"settings": load_settings()})

@app.route("/api/update-clip", methods=["POST"])
def api_update_clip():
    data = request.json or {}
    file_target = data.get("file")
    if not file_target:
        return jsonify({"error": "Missing file"}), 400

    queue = load_queue()
    found = False
    for item in queue:
        if item.get("file") == file_target:
            item["title"] = data.get("title", item.get("title"))
            item["schedule"] = data.get("schedule", item.get("schedule"))
            item["affiliate_deal"] = data.get("affiliate_deal", item.get("affiliate_deal"))
            item["privacy"] = data.get("privacy", item.get("privacy", "public"))
            found = True
            break
    if not found:
        queue.append(data)
    save_queue(queue)
    return jsonify({"status": "success"})

@app.route("/api/publish-now", methods=["POST"])
def api_publish_now():
    data = request.json or {}
    file_target = data.get("file")
    if not file_target:
        return jsonify({"error": "Missing file"}), 400

    queue = load_queue()
    clip_item = next((item for item in queue if item.get("file") == file_target), None)

    title = data.get("title") or (clip_item.get("title") if clip_item else "Viral Short")
    description = clip_item.get("description", "") if clip_item else ""
    affiliate = data.get("affiliate_deal") or (clip_item.get("affiliate_deal") if clip_item else "")
    if affiliate and affiliate not in description:
        description += f"\n\n⚡ Exclusive Deal: {affiliate}"

    tags = clip_item.get("tags", ["Shorts", "Gaming"]) if clip_item else ["Shorts", "Gaming"]
    privacy = data.get("privacy", "public")

    python_exe = sys.executable
    uploader_script = str(BASE_DIR / "scripts" / "upload_youtube.py")

    cmd = [
        python_exe,
        uploader_script,
        "-i", file_target,
        "-t", title,
        "-d", description,
        "--tags", ",".join(tags) if isinstance(tags, list) else tags,
        "-p", privacy
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        res_json = json.loads(proc.stdout.strip().split("\n")[-1])

        now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %I:%M:%S %p IST")
        for item in queue:
            if item.get("file") == file_target:
                item["uploaded"] = True
                item["video_id"] = res_json.get("video_id")
                item["video_url"] = res_json.get("video_url")
                item["posted_at"] = now_ist
                item["auto_posted"] = False
                break
        save_queue(queue)

        return jsonify({"status": "success", "result": res_json})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr or e.stdout}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/sources", methods=["GET"])
def api_sources():
    sources_file = BASE_DIR / "final_clips" / "sources_registry.json"
    if sources_file.exists():
        try:
            with open(sources_file, "r", encoding="utf-8") as f:
                sources = json.load(f)
            return jsonify({"status": "success", "sources": sources})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "success", "sources": []})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n🚀 Shorts Studio & Growth Hub running at: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
