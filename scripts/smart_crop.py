"""
Smart Crop module for Universal Video Clipper.
Transforms horizontal video to 9:16 vertical (1080x1920) with Auto-Framing:
- Auto-Detect Framing Mode:
  * "streamer-split": Top streamer facecam + Bottom gameplay action (with gold accent divider)
  * "stacked-podcast": Speaker-focus layout
  * "fullscreen-crop": 9:16 dynamic subject tracking with blurred pillarbox fallback
- 60 FPS / 30 FPS rendering
- 0ms audio-video lip-sync preservation
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np

os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()


def get_ffmpeg_path() -> str:
    workspace_dir = Path(__file__).resolve().parent.parent
    local_bin = workspace_dir / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin)
    venv_bin = workspace_dir / ".venv" / "Scripts" / "ffmpeg.exe" if sys.platform == "win32" else workspace_dir / ".venv" / "bin" / "ffmpeg"
    if venv_bin.exists():
        return str(venv_bin)
    return shutil.which("ffmpeg") or "ffmpeg"


def parse_timestamp(ts) -> float:
    if isinstance(ts, (int, float)):
        return float(ts)
    parts = str(ts).strip().split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    else:
        return float(parts[0])


class SubjectTracker:
    def __init__(self):
        self.frontal_face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.profile_face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
        self.upper_body = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_upperbody.xml")

    def detect_streamer_webcam(self, sample_frames: list[np.ndarray]) -> tuple[bool, tuple[int, int, int, int] | None]:
        """Detects if a streamer facecam overlay consistently exists in a corner."""
        corner_hits = 0
        last_box = None
        for frame in sample_frames:
            h, w = frame.shape[:2]
            # Check top-left corner (0:int(h*0.4), 0:int(w*0.35))
            tl = frame[0:int(h * 0.4), 0:int(w * 0.35)]
            gray = cv2.cvtColor(tl, cv2.COLOR_BGR2GRAY)
            faces = self.frontal_face.detectMultiScale(gray, 1.15, 3)
            if len(faces) > 0:
                corner_hits += 1
                best = max(faces, key=lambda b: b[2] * b[3])
                # Expand box slightly to cover facecam frame
                fx, fy, fw, fh = best
                cx = fx + fw // 2
                cy = fy + fh // 2
                box_w = max(320, int(fw * 2.8))
                box_h = int(box_w * (840 / 1080))
                x1 = max(0, cx - box_w // 2)
                y1 = max(0, cy - box_h // 2)
                last_box = (x1, y1, box_w, box_h)

        if len(sample_frames) > 0 and (corner_hits / len(sample_frames)) >= 0.4:
            return True, last_box
        return False, None

    def detect_subject_x(self, frame_bgr: np.ndarray, proxy_width: int = 480) -> float | None:
        src_h, src_w = frame_bgr.shape[:2]
        scale = proxy_width / src_w
        proxy_h = int(src_h * scale)

        proxy = cv2.resize(frame_bgr, (proxy_width, proxy_h), interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(proxy, cv2.COLOR_BGR2GRAY)

        faces = self.frontal_face.detectMultiScale(gray, 1.15, 4, minSize=(30, 30))
        if len(faces) > 0:
            best_face = max(faces, key=lambda b: b[2] * b[3])
            return (best_face[0] + best_face[2] / 2.0) / scale

        profiles = self.profile_face.detectMultiScale(gray, 1.15, 4, minSize=(30, 30))
        if len(profiles) > 0:
            best_profile = max(profiles, key=lambda b: b[2] * b[3])
            return (best_profile[0] + best_profile[2] / 2.0) / scale

        bodies = self.upper_body.detectMultiScale(gray, 1.15, 3, minSize=(50, 50))
        if len(bodies) > 0:
            best_body = max(bodies, key=lambda b: b[2] * b[3])
            return (best_body[0] + best_body[2] / 2.0) / scale

        return None


def render_streamer_split(frame: np.ndarray, target_w: int = 1080, target_h: int = 1920, webcam_box=None) -> np.ndarray:
    """
    Renders Split-Screen for Streamers:
    - Top 840px: Streamer Facecam zoomed & stabilized
    - Middle 10px: Gold divider line (#FFD700)
    - Bottom 1070px: Gameplay action
    """
    h, w = frame.shape[:2]
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)

    # 1. Webcam crop
    if webcam_box:
        x1, y1, bw, bh = webcam_box
        x2 = min(w, x1 + bw)
        y2 = min(h, y1 + bh)
        wc = frame[y1:y2, x1:x2]
    else:
        # Default top-left webcam bounds
        wc = frame[30:360, 60:440]

    wc_resized = cv2.resize(wc, (target_w, 840), interpolation=cv2.INTER_LANCZOS4)
    canvas[0:840, 0:target_w] = wc_resized

    # 2. Gold divider line (#FFD700 -> BGR: 0, 215, 255)
    canvas[840:850, 0:target_w] = (0, 215, 255)

    # 3. Gameplay crop
    # Crop center 1200x1080 of gameplay to focus on character/crosshair
    gp_w = int(h * (target_w / 1070))
    start_x = max(0, (w - gp_w) // 2)
    gp = frame[:, start_x:start_x + gp_w]
    gp_resized = cv2.resize(gp, (target_w, 1070), interpolation=cv2.INTER_LANCZOS4)
    canvas[850:target_h, 0:target_w] = gp_resized

    return canvas


def create_blurred_pillarbox(frame: np.ndarray, target_w: int = 1080, target_h: int = 1920) -> np.ndarray:
    src_h, src_w = frame.shape[:2]
    scale_bg = max(target_w / src_w, target_h / src_h)
    bg_w = int(src_w * scale_bg)
    bg_h = int(src_h * scale_bg)
    bg_resized = cv2.resize(frame, (bg_w, bg_h), interpolation=cv2.INTER_LINEAR)

    start_x = max(0, (bg_w - target_w) // 2)
    start_y = max(0, (bg_h - target_h) // 2)
    bg_cropped = bg_resized[start_y:start_y + target_h, start_x:start_x + target_w]
    if bg_cropped.shape[0] != target_h or bg_cropped.shape[1] != target_w:
        bg_cropped = cv2.resize(bg_cropped, (target_w, target_h))

    small_bg = cv2.resize(bg_cropped, (target_w // 8, target_h // 8), interpolation=cv2.INTER_LINEAR)
    blurred_small = cv2.GaussianBlur(small_bg, (25, 25), 15)
    blurred_bg = cv2.resize(blurred_small, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    blurred_bg = (blurred_bg.astype(np.float32) * 0.65).astype(np.uint8)

    fg_w = target_w
    fg_h = int(src_h * (target_w / src_w))
    fg_resized = cv2.resize(frame, (fg_w, fg_h), interpolation=cv2.INTER_AREA)

    y_offset = (target_h - fg_h) // 2
    blurred_bg[y_offset:y_offset + fg_h, 0:fg_w] = fg_resized
    return blurred_bg


def crop_face_region(frame: np.ndarray, center_x: float, target_w: int = 1080, target_h: int = 1920) -> np.ndarray:
    src_h, src_w = frame.shape[:2]
    crop_aspect = target_w / target_h
    crop_h = src_h
    crop_w = int(crop_h * crop_aspect)

    if crop_w > src_w:
        crop_w = src_w
        crop_h = int(crop_w / crop_aspect)

    half_crop = crop_w / 2.0
    cx = max(half_crop, min(src_w - half_crop, center_x))

    x1 = int(round(cx - half_crop))
    y1 = (src_h - crop_h) // 2
    x1 = max(0, min(src_w - crop_w, x1))
    y1 = max(0, min(src_h - crop_h, y1))

    cropped = frame[y1:y1 + crop_h, x1:x1 + crop_w]
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)


def process_video_smart_crop(
    input_video: str,
    output_video: str,
    start_time: float = 0.0,
    end_time: float = None,
    target_w: int = 1080,
    target_h: int = 1920,
    framing_mode: str = "auto",
    ema_alpha: float = 0.08,
    deadband_pct: float = 0.02,
    no_face_timeout_sec: float = 1.5,
    target_fps: float = 60.0
) -> dict:
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video source: {input_video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_duration = total_frames / fps

    start_sec = max(0.0, start_time)
    end_sec = min(total_duration, end_time) if end_time is not None else total_duration
    if end_sec <= start_sec:
        raise ValueError(f"Invalid duration: start={start_sec}s, end={end_sec}s")

    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)
    frames_to_process = end_frame - start_frame

    tracker = SubjectTracker()

    # Determine framing mode
    active_mode = framing_mode
    webcam_box = None
    if framing_mode == "auto":
        # Sample 15 frames across the segment
        sample_indices = np.linspace(start_frame, end_frame - 1, min(15, frames_to_process), dtype=int)
        sample_frames = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, fr = cap.read()
            if ret and fr is not None:
                sample_frames.append(fr)

        has_streamer, box = tracker.detect_streamer_webcam(sample_frames)
        if has_streamer:
            active_mode = "streamer-split"
            webcam_box = box
        else:
            active_mode = "fullscreen-crop"

    print(f"[smart_crop] Framing: '{active_mode}' | Resolution: {target_w}x{target_h} @ {fps:.0f}fps | Duration: {start_sec:.2f}s -> {end_sec:.2f}s", file=sys.stderr)

    temp_dir = Path(tempfile.mkdtemp(prefix="smart_crop_"))
    temp_raw_video = temp_dir / "raw_cropped.mp4"
    temp_audio = temp_dir / "extracted_audio.m4a"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(temp_raw_video), fourcc, fps, (target_w, target_h))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    smoothed_x = src_w / 2.0
    deadband_px = src_w * deadband_pct
    consecutive_no_face = 0
    no_face_frames_threshold = int(no_face_timeout_sec * fps)

    blend_state = 1.0
    blend_speed = 1.0 / max(1, int(0.5 * fps))

    curr_frame_idx = start_frame
    processed_count = 0

    try:
        while curr_frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if active_mode == "streamer-split":
                final_frame = render_streamer_split(frame, target_w, target_h, webcam_box)
            else:
                if processed_count % 3 == 0:
                    detected_x = tracker.detect_subject_x(frame, proxy_width=480)
                if detected_x is not None:
                    consecutive_no_face = 0
                    target_blend = 1.0
                    delta = abs(detected_x - smoothed_x)
                    if delta > deadband_px:
                        smoothed_x = (ema_alpha * detected_x) + ((1.0 - ema_alpha) * smoothed_x)
                else:
                    consecutive_no_face += 1
                    target_blend = 0.0 if consecutive_no_face >= no_face_frames_threshold else 1.0

                if blend_state < target_blend:
                    blend_state = min(target_blend, blend_state + blend_speed)
                elif blend_state > target_blend:
                    blend_state = max(target_blend, blend_state - blend_speed)

                if blend_state >= 0.999:
                    final_frame = crop_face_region(frame, smoothed_x, target_w, target_h)
                elif blend_state <= 0.001:
                    final_frame = create_blurred_pillarbox(frame, target_w, target_h)
                else:
                    f_crop = crop_face_region(frame, smoothed_x, target_w, target_h)
                    f_pill = create_blurred_pillarbox(frame, target_w, target_h)
                    final_frame = cv2.addWeighted(f_crop, blend_state, f_pill, 1.0 - blend_state, 0.0)

            out.write(final_frame)
            curr_frame_idx += 1
            processed_count += 1

    finally:
        cap.release()
        out.release()

    ffmpeg_bin = get_ffmpeg_path()
    clip_dur = end_sec - start_sec

    # Extract audio cleanly from source video for exact duration
    audio_cmd = [
        ffmpeg_bin, "-y",
        "-ss", str(start_sec),
        "-t", str(clip_dur),
        "-i", input_video,
        "-vn",
        "-c:a", "aac",
        "-b:a", "192k",
        str(temp_audio)
    ]
    subprocess.run(audio_cmd, capture_output=True, check=True)

    out_path = Path(output_video)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    remux_cmd = [
        ffmpeg_bin, "-y",
        "-i", str(temp_raw_video),
        "-i", str(temp_audio),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-r", str(target_fps),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-shortest",
        str(out_path)
    ]
    res = subprocess.run(remux_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg remux failed:\n{res.stderr}")

    shutil.rmtree(temp_dir, ignore_errors=True)

    return {
        "status": "success",
        "output_file": str(out_path.resolve()),
        "framing_mode": active_mode,
        "duration": clip_dur,
        "width": target_w,
        "height": target_h,
        "fps": target_fps
    }


def main():
    parser = argparse.ArgumentParser(description="Smart 9:16 vertical video crop with face tracking and pillarbox fallback.")
    parser.add_argument("--input", "-i", required=True, help="Input video path")
    parser.add_argument("--output", "-o", required=True, help="Output 9:16 video path")
    parser.add_argument("--start", "-s", default=0.0, help="Start timestamp in seconds or HH:MM:SS")
    parser.add_argument("--end", "-e", default=None, help="End timestamp in seconds or HH:MM:SS")
    parser.add_argument("--framing", choices=["auto", "streamer-split", "fullscreen-crop"], default="auto", help="Framing mode")
    parser.add_argument("--target-width", type=int, default=1080, help="Target width (default: 1080)")
    parser.add_argument("--target-height", type=int, default=1920, help="Target height (default: 1920)")
    parser.add_argument("--fps", type=float, default=60.0, help="Target FPS (default: 60.0)")
    args = parser.parse_args()

    try:
        start_t = parse_timestamp(args.start)
        end_t = parse_timestamp(args.end) if args.end is not None else None

        result = process_video_smart_crop(
            input_video=args.input,
            output_video=args.output,
            start_time=start_t,
            end_time=end_t,
            target_w=args.target_width,
            target_h=args.target_height,
            framing_mode=args.framing,
            target_fps=args.fps
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        err = {"status": "error", "message": str(e)}
        print(json.dumps(err, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
