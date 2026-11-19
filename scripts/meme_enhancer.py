#!/usr/bin/env python3
"""
Meme Enhancer Engine for Gaming Shorts & Reels (k2).
Adds viral meme hooks, top meme banners, sound impact cues, and GTA-style visual effects.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEME_HOOK_TEMPLATES = [
    "BRO WAS NOT READY FOR THIS 💀",
    "GTA 6 PHYSICS GONE WRONG 😂",
    "HE REALLY THOUGHT HE COULD ESCAPE 🚨",
    "WAIT TILL THE END... 😱",
    "TOP 1% GAMER MOMENT 🔥",
    "NPC LOGIC IN GTA BE LIKE 😭",
    "NO WAY HE SURVIVED THAT 🤯",
    "WHEN THE COP AI IS ON STEROIDS 💀"
]

def get_ffmpeg_path() -> str:
    local_bin = BASE_DIR / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin)
    venv_bin = BASE_DIR / ".venv" / "Scripts" / "ffmpeg.exe" if sys.platform == "win32" else BASE_DIR / ".venv" / "bin" / "ffmpeg"
    if venv_bin.exists():
        return str(venv_bin)
    return "ffmpeg"

def select_meme_hook(text_context: str = "") -> str:
    """
    Select or generate an engaging meme hook based on text context.
    """
    lower = text_context.lower()
    if "police" in lower or "cop" in lower or "busted" in lower or "escape" in lower:
        return "HE REALLY THOUGHT HE COULD ESCAPE 🚨"
    if "car" in lower or "drive" in lower or "stunt" in lower or "fly" in lower or "jump" in lower:
        return "GTA 6 PHYSICS GONE WRONG 😂"
    if "dead" in lower or "kill" in lower or "die" in lower or "fail" in lower or "wasted" in lower:
        return "BRO WAS NOT READY FOR THIS 💀"
    if "omg" in lower or "insane" in lower or "what" in lower or "kya" in lower:
        return "WAIT TILL THE END... 😱"
    return MEME_HOOK_TEMPLATES[0]

def add_meme_header_banner(input_video: str, output_video: str, meme_text: str = None) -> bool:
    """
    Burns a bold viral meme headline banner at the top of the 9:16 short.
    Uses pure FFmpeg drawbox and drawtext filters.
    """
    if not meme_text:
        meme_text = select_meme_hook()

    ffmpeg_bin = get_ffmpeg_path()
    escaped_text = meme_text.replace(":", "\\:").replace("'", "\\'")

    # Filter: Draw a semi-transparent dark banner behind text at top (Y=180 to 300)
    # Draw high-contrast white text with black outline and drop shadow at Y=220
    vf_filter = (
        f"drawbox=y=160:color=black@0.65:width=iw:height=140:t=fill,"
        f"drawtext=text='{escaped_text}':font='Arial':fontsize=42:fontcolor=white:"
        f"bordercolor=black:borderw=4:shadowcolor=black:shadowx=3:shadowy=3:"
        f"x=(w-text_w)/2:y=205"
    )

    cmd = [
        ffmpeg_bin, "-y",
        "-i", input_video,
        "-vf", vf_filter,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        output_video
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[meme_enhancer] Failed to burn meme banner: {e.stderr[:200]}", file=sys.stderr)
        return False

def add_wasted_dramatic_effect(input_video: str, output_video: str, timestamp_sec: float) -> bool:
    """
    Applies a dramatic slow-motion or red/grayscale flash around a fail/death moment.
    """
    ffmpeg_bin = get_ffmpeg_path()
    start_eff = max(0, timestamp_sec - 0.5)
    end_eff = timestamp_sec + 2.0

    # Draw GTA 'WASTED' text in red at timestamp
    vf_filter = (
        f"drawtext=text='WASTED':font='Impact':fontsize=96:fontcolor=red:"
        f"bordercolor=black:borderw=6:x=(w-text_w)/2:y=(h-text_h)/2:"
        f"enable='between(t,{start_eff},{end_eff})'"
    )

    cmd = [
        ffmpeg_bin, "-y",
        "-i", input_video,
        "-vf", vf_filter,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        output_video
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except Exception as e:
        print(f"[meme_enhancer] Failed wasted effect: {e}", file=sys.stderr)
        return False
