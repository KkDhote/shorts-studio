"""
Ingest module for Universal Video Clipper.
Handles YouTube URLs (via yt-dlp) and local video files.
Ensures output is a clean MP4 container with max 1080p resolution and merged audio.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_ffmpeg_path() -> str:
    """Find ffmpeg binary in workspace bin, venv, or system PATH."""
    workspace_dir = Path(__file__).resolve().parent.parent
    local_bin = workspace_dir / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin)

    venv_bin = workspace_dir / ".venv" / "Scripts" / "ffmpeg.exe" if sys.platform == "win32" else workspace_dir / ".venv" / "bin" / "ffmpeg"
    if venv_bin.exists():
        return str(venv_bin)

    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg

    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Find ffprobe binary in workspace bin, venv, or system PATH."""
    workspace_dir = Path(__file__).resolve().parent.parent
    local_bin = workspace_dir / "bin" / ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
    if local_bin.exists():
        return str(local_bin)

    venv_bin = workspace_dir / ".venv" / "Scripts" / "ffprobe.exe" if sys.platform == "win32" else workspace_dir / ".venv" / "bin" / "ffprobe"
    if venv_bin.exists():
        return str(venv_bin)

    which_ffprobe = shutil.which("ffprobe")
    if which_ffprobe:
        return which_ffprobe

    return "ffprobe"


def probe_video(file_path: str) -> dict:
    """Probe video file using ffprobe to obtain duration, width, height, and fps."""
    ffprobe_bin = get_ffprobe_path()
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration,size",
        "-of", "json",
        file_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})

        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))

        duration_str = stream.get("duration") or fmt.get("duration") or "0"
        duration = float(duration_str)

        fps_str = stream.get("r_frame_rate", "30/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 30.0
        else:
            fps = float(fps_str)

        return {
            "width": width,
            "height": height,
            "duration": duration,
            "fps": fps,
            "file_size": int(fmt.get("size", 0))
        }
    except Exception as e:
        return {"error": str(e), "width": 0, "height": 0, "duration": 0.0, "fps": 30.0}


def is_url(string: str) -> bool:
    return string.startswith("http://") or string.startswith("https://") or string.startswith("www.")


def ingest_youtube(url: str, output_path: Path) -> dict:
    """Download video from YouTube using yt-dlp with anti-throttling options."""
    ffmpeg_bin = get_ffmpeg_path()
    ffmpeg_dir = str(Path(ffmpeg_bin).parent)

    output_tmpl = str(output_path.with_suffix("")) + ".%(ext)s"

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--format", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "--ffmpeg-location", ffmpeg_dir,
        "--extractor-args", "youtube:player_client=android,web",
        "--retries", "5",
        "--fragment-retries", "5",
        "--retry-sleep", "2",
        "--no-playlist",
        "--print-json",
        "-o", output_tmpl,
        url
    ]

    print(f"[ingest] Downloading YouTube video from {url}...", file=sys.stderr)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"yt-dlp failed (code {res.returncode}):\n{res.stderr}")

    info = {}
    for line in res.stdout.strip().split("\n"):
        try:
            info = json.loads(line)
            break
        except json.JSONDecodeError:
            continue

    actual_file = output_path.with_suffix(".mp4")
    if not actual_file.exists():
        # Look for downloaded file in directory matching name
        parent_dir = output_path.parent
        matches = list(parent_dir.glob(output_path.stem + ".*"))
        if matches:
            actual_file = matches[0]
        else:
            raise FileNotFoundError(f"Expected output file {actual_file} was not found.")

    probe_data = probe_video(str(actual_file))
    return {
        "status": "success",
        "file_path": str(actual_file.resolve()),
        "title": info.get("title", output_path.stem),
        "duration": probe_data.get("duration", info.get("duration", 0.0)),
        "width": probe_data.get("width", 0),
        "height": probe_data.get("height", 0),
        "fps": probe_data.get("fps", 30.0),
        "uploader": info.get("uploader", ""),
        "source": "youtube"
    }


def ingest_local(local_path: Path, output_path: Path) -> dict:
    """Ingest a local video file, converting/remuxing to MP4 if necessary."""
    if not local_path.exists():
        raise FileNotFoundError(f"Local file does not exist: {local_path}")

    ffmpeg_bin = get_ffmpeg_path()
    output_mp4 = output_path.with_suffix(".mp4")

    print(f"[ingest] Processing local video {local_path}...", file=sys.stderr)

    # Remux or transcode to standard MP4 with H.264/AAC if not already MP4 container
    if local_path.suffix.lower() == ".mp4":
        shutil.copy2(local_path, output_mp4)
    else:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(local_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_mp4)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg transcode failed:\n{res.stderr}")

    probe_data = probe_video(str(output_mp4))
    return {
        "status": "success",
        "file_path": str(output_mp4.resolve()),
        "title": local_path.stem,
        "duration": probe_data.get("duration", 0.0),
        "width": probe_data.get("width", 0),
        "height": probe_data.get("height", 0),
        "fps": probe_data.get("fps", 30.0),
        "source": "local"
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest video from YouTube or local file.")
    parser.add_argument("--input", "-i", required=True, help="YouTube URL or local video file path")
    parser.add_argument("--output-dir", "-d", default="./temp_work", help="Directory to save ingested video")
    parser.add_argument("--output-name", "-n", default="source", help="Base filename for ingested video")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_path = out_dir / args.output_name

    try:
        if is_url(args.input):
            result = ingest_youtube(args.input, target_path)
        else:
            result = ingest_local(Path(args.input), target_path)

        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        err_res = {"status": "error", "message": str(e)}
        print(json.dumps(err_res, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
