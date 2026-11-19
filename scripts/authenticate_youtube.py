#!/usr/bin/env python3
"""
One-Time YouTube Channel Authorization Script.
Authorizes the application to upload and manage Shorts on your YouTube Channel.
Saves credentials/token.json for persistent, headless, autonomous uploads.
"""

import sys
import webbrowser
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

CLIENT_SECRET_FILE = Path("credentials/client_secret.json")
TOKEN_FILE = Path("credentials/token.json")

def authenticate():
    if not CLIENT_SECRET_FILE.exists():
        print(f"Error: {CLIENT_SECRET_FILE} not found!", file=sys.stderr, flush=True)
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES
    )

    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline"
    )

    print("\n" + "=" * 70, flush=True)
    print("      YOUTUBE CHANNEL ONE-TIME AUTHORIZATION", flush=True)
    print("=" * 70, flush=True)
    print("Please visit the URL below in your browser to authorize your channel:\n", flush=True)
    print(auth_url, flush=True)
    print("\n" + "=" * 70, flush=True)
    print("Waiting for authorization callback on http://localhost:8080 ...\n", flush=True)

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    creds = flow.run_local_server(
        port=8080,
        open_browser=False,
        success_message="Authentication successful! You can now close this tab and return to the terminal."
    )

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"\n[+] Success! Token saved to: {TOKEN_FILE.resolve()}", flush=True)

    # Verify channel details
    youtube = build("youtube", "v3", credentials=creds)
    channels_res = youtube.channels().list(mine=True, part="snippet,statistics").execute()
    
    items = channels_res.get("items", [])
    if items:
        channel = items[0]
        title = channel["snippet"]["title"]
        subs = channel["statistics"].get("subscriberCount", "Hidden/0")
        print(f"[+] Connected YouTube Channel: {title}", flush=True)
        print(f"[+] Total Subscribers: {subs}", flush=True)
        print("\n[+] From now on, uploads will run 100% autonomously without asking permission!\n", flush=True)
    else:
        print("[!] Authenticated Google Account has no active YouTube Channel.", flush=True)
        print("    Please create a channel on YouTube.com with this account.", flush=True)

if __name__ == "__main__":
    authenticate()
