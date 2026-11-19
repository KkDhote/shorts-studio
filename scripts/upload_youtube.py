#!/usr/bin/env python3
"""
Autonomous YouTube Shorts Uploader & Publisher.
Uses the official YouTube Data API v3 with persistent OAuth 2.0 refresh tokens.
Once authenticated once, runs headlessly in the background without user intervention.
"""

import os
import sys
import json
import time
import random
import argparse
from pathlib import Path

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# YouTube Data API upload scope
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]
BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_FILE = BASE_DIR / "credentials" / "token.json"
CLIENT_SECRET_FILE = BASE_DIR / "credentials" / "client_secret.json"

# Retry constants for exponential backoff
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    TimeoutError,
    ConnectionResetError,
)
MAX_RETRIES = 5

def get_authenticated_service(client_secret_path: Path = CLIENT_SECRET_FILE, token_path: Path = TOKEN_FILE):
    """
    Authenticate and return YouTube service.
    Refreshes token automatically if expired.
    """
    creds = None
    token_path.parent.mkdir(parents=True, exist_ok=True)

    if os.environ.get("YOUTUBE_TOKEN_JSON"):
        try:
            token_data = json.loads(os.environ["YOUTUBE_TOKEN_JSON"])
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"[upload_youtube] Warning: Token from YOUTUBE_TOKEN_JSON env could not be loaded: {e}", file=sys.stderr)

    if not creds and token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            print(f"[upload_youtube] Warning: Existing token could not be loaded: {e}", file=sys.stderr)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[upload_youtube] Refreshing expired OAuth token automatically...", file=sys.stderr)
            creds.refresh(Request())
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        else:
            if not client_secret_path.exists():
                raise FileNotFoundError(
                    f"OAuth client secrets file not found at: {client_secret_path.resolve()}\n"
                    "Please download your client_secret.json from Google Cloud Console "
                    "and place it in the credentials/ directory."
                )
            print("[upload_youtube] Initiating one-time browser authentication flow...", file=sys.stderr)
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            print(f"[upload_youtube] Successfully saved persistent token to {token_path}", file=sys.stderr)

    return build("youtube", "v3", credentials=creds)

def upload_video(
    youtube,
    file_path: str,
    title: str,
    description: str,
    tags: list = None,
    category_id: str = "20",  # 20 = Gaming, 22 = People & Blogs, 24 = Entertainment
    privacy_status: str = "public",  # public, unlisted, private
    publish_at: str = None,  # ISO 8601 string for scheduled release (requires privacy_status='private')
    chunksize: int = 4 * 1024 * 1024  # 4MB chunks
):
    """
    Upload a video with resumable upload and exponential backoff.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")

    # Enforce YouTube Shorts metadata best practices
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title.strip()} #shorts"
    if len(title) > 100:
        title = title[:97] + "..."

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or ["Shorts", "Gaming", "Viral"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy_status,
            "selfDeclaredMadeForKids": False,
        }
    }

    if publish_at:
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(
        file_path,
        mimetype="video/mp4",
        chunksize=chunksize,
        resumable=True
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"[upload_youtube] Starting upload for '{title}' ({os.path.basename(file_path)})...")
    response = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"[upload_youtube] Upload progress: {progress}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                retry += 1
                if retry > MAX_RETRIES:
                    raise
                sleeptime = random.random() * (2 ** retry)
                print(f"[upload_youtube] HTTP {e.resp.status}. Retrying in {sleeptime:.1f}s...")
                time.sleep(sleeptime)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            retry += 1
            if retry > MAX_RETRIES:
                raise
            sleeptime = random.random() * (2 ** retry)
            print(f"[upload_youtube] Retriable exception: {e}. Retrying in {sleeptime:.1f}s...")
            time.sleep(sleeptime)

    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"[upload_youtube] Upload SUCCESS! Video URL: {video_url}")

    return {
        "status": "success",
        "video_id": video_id,
        "video_url": video_url,
        "title": title,
        "privacy": body["status"]["privacyStatus"],
        "publish_at": publish_at
    }

def main():
    parser = argparse.ArgumentParser(description="Upload vertical video clips directly to YouTube Shorts.")
    parser.add_argument("-i", "--file", required=True, help="Path to video file (e.g. final_clips/clip_1.mp4)")
    parser.add_argument("-t", "--title", required=True, help="Shorts title (max 100 chars)")
    parser.add_argument("-d", "--description", default="", help="Shorts description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("-p", "--privacy", choices=["public", "unlisted", "private"], default="public", help="Visibility")
    parser.add_argument("-s", "--schedule", default=None, help="Scheduled publish time in ISO 8601 (e.g., 2026-11-20T14:00:00Z)")
    parser.add_argument("-c", "--category", default="20", help="YouTube Category ID (20=Gaming, 24=Entertainment)")
    parser.add_argument("--client-secret", default=str(CLIENT_SECRET_FILE), help="Path to client_secret.json")
    parser.add_argument("--token", default=str(TOKEN_FILE), help="Path to token.json")

    args = parser.parse_args()

    tags_list = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else []

    try:
        service = get_authenticated_service(Path(args.client_secret), Path(args.token))
        res = upload_video(
            youtube=service,
            file_path=args.file,
            title=args.title,
            description=args.description,
            tags=tags_list,
            category_id=args.category,
            privacy_status=args.privacy,
            publish_at=args.schedule
        )
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
