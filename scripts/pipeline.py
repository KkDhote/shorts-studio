"""
Autonomous End-to-End Pipeline Runner for Universal Video Clipper.
Orchestrates:
1. Ingest (YouTube / local)
2. Transcribe (faster-whisper word-level)
3. Viral Hook Scoring & Candidate Selection (30-58s window, sentence boundaries, hook detection)
4. Smart 9:16 Cropping (MediaPipe face tracking + pillarbox fallback)
5. Viral Karaoke Captions (ASS highlight burn CRF 20, AAC 192k)
6. Output Verification & Ephemeral Cleanup
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


HOOK_KEYWORDS = [
    # English hook triggers
    "why", "how", "secret", "never", "always", "truth", "stop", "don't", "dont",
    "if you", "imagine", "nobody", "everyone", "mistake", "warning", "insane",
    "crazy", "money", "rich", "billionaire", "millionaire", "hack", "trick",
    "did you know", "here is", "this is why", "the biggest", "what happens",
    "you won't believe", "shocking", "rule", "game changer", "everything",
    # Hindi / Hinglish hook triggers
    "kyun", "kaise", "sach", "raaz", "galti", "mat karna", "ruko", "dekho",
    "suno", "yeh mat karo", "asli", "paisa", "crore", "lakh", "faayda", "nuksaan"
]


def slugify(text: str, max_len: int = 32) -> str:
    """Converts a phrase into a clean filename slug."""
    clean = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    slug = re.sub(r"[-\s]+", "-", clean)
    return slug[:max_len] or "clip"


def score_viral_segments(
    transcript: dict,
    min_dur: float = 30.0,
    max_dur: float = 58.0,
    top_k: int = 3
) -> list[dict]:
    """
    Identifies high-retention 30-58s segments from transcript.
    Enforces complete sentence boundaries and scores based on:
    - Hook strength in the first 3 seconds
    - Curiosity gaps & question words
    - Pacing / speech density (words per second)
    - Strong punchline / ending resolution
    """
    segments = transcript.get("segments", [])
    if not segments:
        return []

    # Map segments to sentence-level units
    candidates = []
    n = len(segments)

    for i in range(n):
        seg_start = segments[i]["start"]
        first_text = segments[i]["text"].lower()

        # Check hook strength in opening
        hook_score = 0.0
        for kw in HOOK_KEYWORDS:
            if kw in first_text[:60]:
                hook_score += 15.0
        if any(p in first_text[:40] for p in ["?", "!"]):
            hook_score += 10.0

        for j in range(i, n):
            seg_end = segments[j]["end"]
            dur = seg_end - seg_start

            if dur < min_dur:
                continue
            if dur > max_dur:
                break

            # Boundary check: Ensure segment ends on a complete sentence
            end_text = segments[j]["text"].strip()
            ends_sentence = any(end_text.endswith(p) for p in [".", "!", "?", "।"])

            if not ends_sentence and (dur + 4.0 <= max_dur) and (j + 1 < n):
                # Prefer waiting for a complete sentence boundary if within duration
                continue

            # Calculate total words and density
            window_segments = segments[i:j + 1]
            total_words = sum(len(s.get("words", s.get("text", "").split())) for s in window_segments)
            wps = total_words / max(1.0, dur)

            # Ideal pacing for Shorts is 2.2 to 3.8 words per second
            if 2.2 <= wps <= 3.8:
                pacing_score = 25.0
            elif 1.6 <= wps < 2.2 or 3.8 < wps <= 4.5:
                pacing_score = 15.0
            else:
                pacing_score = 5.0

            # Ending punchline score
            punchline_score = 15.0 if any(end_text.endswith(p) for p in ["!", "?"]) else 8.0

            # Total score
            total_score = hook_score + pacing_score + punchline_score

            first_sentence = segments[i]["text"].strip().split(".")[0]
            slug = slugify(first_sentence)

            candidates.append({
                "start": round(seg_start, 2),
                "end": round(seg_end, 2),
                "duration": round(dur, 2),
                "score": round(total_score, 1),
                "hook_text": first_sentence,
                "slug": slug,
                "start_seg_idx": i,
                "end_seg_idx": j
            })

    # Sort descending by score
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Greedily pick top non-overlapping clips
    selected = []
    for cand in candidates:
        overlap = False
        for s in selected:
            # Overlap if intervals intersect by > 8 seconds
            if not (cand["end"] < s["start"] + 8.0 or cand["start"] > s["end"] - 8.0):
                overlap = True
                break
        if not overlap:
            selected.append(cand)
            if len(selected) >= top_k:
                break

    return selected


def run_pipeline(
    input_source: str,
    output_dir: str = "./final_clips",
    temp_dir: str = "./temp_work",
    whisper_model: str = "small",
    num_clips: int = 3,
    cleanup: bool = True
) -> dict:
    workspace_dir = Path(__file__).resolve().parent.parent
    scripts_dir = workspace_dir / "scripts"
    py_exec = sys.executable

    out_path = Path(output_dir).resolve()
    temp_path = Path(temp_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    temp_path.mkdir(parents=True, exist_ok=True)

    print(f"[pipeline] === STARTING VERTICAL CLIPPING PIPELINE ===", file=sys.stderr)
    print(f"[pipeline] Source: {input_source}", file=sys.stderr)
    print(f"[pipeline] Output Directory: {out_path}", file=sys.stderr)

    # 1. Ingest
    ingest_script = scripts_dir / "ingest.py"
    ingest_cmd = [
        py_exec, str(ingest_script),
        "--input", input_source,
        "--output-dir", str(temp_path),
        "--output-name", "source"
    ]
    print(f"[pipeline] [Phase 1/5] Ingesting video...", file=sys.stderr)
    res_ingest = subprocess.run(ingest_cmd, capture_output=True, text=True)
    if res_ingest.returncode != 0:
        raise RuntimeError(f"Ingest failed:\n{res_ingest.stderr}")
    ingest_data = json.loads(res_ingest.stdout)
    source_video = ingest_data["file_path"]
    print(f"[pipeline] Ingested: {source_video} (Duration: {ingest_data.get('duration', 0):.1f}s)", file=sys.stderr)

    # 2. Transcribe
    transcribe_script = scripts_dir / "transcribe.py"
    transcript_json = temp_path / "transcript.json"
    transcribe_cmd = [
        py_exec, str(transcribe_script),
        "--input", source_video,
        "--output", str(transcript_json),
        "--model", whisper_model
    ]
    print(f"[pipeline] [Phase 2/5] Transcribing with faster-whisper ({whisper_model})...", file=sys.stderr)
    res_trans = subprocess.run(transcribe_cmd, capture_output=True, text=True)
    if res_trans.returncode != 0:
        raise RuntimeError(f"Transcription failed:\n{res_trans.stderr}")
    with open(transcript_json, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)

    # 3. Viral Hook Scoring
    print(f"[pipeline] [Phase 3/5] Scoring high-retention viral segments...", file=sys.stderr)
    clips = score_viral_segments(transcript_data, min_dur=30.0, max_dur=58.0, top_k=num_clips)
    if not clips:
        # Fallback to default first 45 seconds if video is short
        dur = min(45.0, ingest_data.get("duration", 45.0))
        clips = [{
            "start": 0.0,
            "end": dur,
            "duration": dur,
            "score": 50.0,
            "hook_text": "Highlight clip",
            "slug": "highlight"
        }]

    print(f"[pipeline] Selected {len(clips)} viral candidate(s):", file=sys.stderr)
    for idx, c in enumerate(clips):
        print(f"  Clip #{idx+1:02d}: {c['start']}s -> {c['end']}s ({c['duration']}s) [Score: {c['score']}] '{c['hook_text']}'", file=sys.stderr)

    # 4. Smart Crop & 5. Render Captions for each clip
    smart_crop_script = scripts_dir / "smart_crop.py"
    render_captions_script = scripts_dir / "render_captions.py"

    rendered_clips = []

    for idx, clip in enumerate(clips):
        clip_num = idx + 1
        clip_name = f"clip_{clip_num:02d}_{clip['slug']}.mp4"
        raw_crop_path = temp_path / f"temp_crop_{clip_num:02d}.mp4"
        final_clip_path = out_path / clip_name

        print(f"\n[pipeline] [Phase 4/5] Smart Cropping Clip #{clip_num:02d} ({clip['start']}s -> {clip['end']}s)...", file=sys.stderr)
        crop_cmd = [
            py_exec, str(smart_crop_script),
            "--input", source_video,
            "--output", str(raw_crop_path),
            "--start", str(clip["start"]),
            "--end", str(clip["end"]),
            "--target-width", "1080",
            "--target-height", "1920"
        ]
        res_crop = subprocess.run(crop_cmd, capture_output=True, text=True)
        if res_crop.returncode != 0:
            print(f"[pipeline] Error cropping clip #{clip_num:02d}:\n{res_crop.stderr}", file=sys.stderr)
            continue

        print(f"[pipeline] [Phase 5/5] Burning Karaoke Captions into Clip #{clip_num:02d}...", file=sys.stderr)
        cap_cmd = [
            py_exec, str(render_captions_script),
            "--input", str(raw_crop_path),
            "--transcript", str(transcript_json),
            "--output", str(final_clip_path),
            "--start", str(clip["start"]),
            "--end", str(clip["end"]),
            "--font", "Arial Black",
            "--font-size", "54",
            "--highlight", "#FFD700",
            "--margin-v", "280"
        ]
        res_cap = subprocess.run(cap_cmd, capture_output=True, text=True)
        if res_cap.returncode != 0:
            print(f"[pipeline] Error rendering captions for clip #{clip_num:02d}:\n{res_cap.stderr}", file=sys.stderr)
            continue

        # Verification: Verify file size > 0 and exists
        if final_clip_path.exists() and final_clip_path.stat().st_size > 1024:
            size_mb = final_clip_path.stat().st_size / (1024 * 1024)
            print(f"[pipeline] Verified export: {final_clip_path.name} ({size_mb:.2f} MB)", file=sys.stderr)
            rendered_clips.append({
                "clip_id": clip_num,
                "file_path": str(final_clip_path),
                "duration": clip["duration"],
                "start": clip["start"],
                "end": clip["end"],
                "score": clip["score"],
                "size_mb": round(size_mb, 2),
                "hook": clip["hook_text"]
            })

    # 6. Ephemeral Cleanup if successful
    if cleanup and len(rendered_clips) > 0:
        print(f"\n[pipeline] Wiping ephemeral files in {temp_path}...", file=sys.stderr)
        for item in temp_path.glob("*"):
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f"[pipeline] Warning during cleanup: {e}", file=sys.stderr)

    return {
        "status": "success" if rendered_clips else "error",
        "total_clips_created": len(rendered_clips),
        "output_directory": str(out_path),
        "clips": rendered_clips
    }


def main():
    parser = argparse.ArgumentParser(description="Autonomous vertical video clipping pipeline.")
    parser.add_argument("--input", "-i", required=True, help="YouTube URL or local video file path")
    parser.add_argument("--output-dir", "-o", default="./final_clips", help="Directory for final clips")
    parser.add_argument("--temp-dir", "-t", default="./temp_work", help="Ephemeral staging directory")
    parser.add_argument("--model", "-m", default="small", choices=["tiny", "base", "small", "medium"], help="Whisper model size")
    parser.add_argument("--num-clips", "-n", type=int, default=3, help="Number of viral clips to extract (default: 3)")
    parser.add_argument("--no-cleanup", action="store_true", help="Preserve ephemeral temp files")
    args = parser.parse_args()

    try:
        res = run_pipeline(
            input_source=args.input,
            output_dir=args.output_dir,
            temp_dir=args.temp_dir,
            whisper_model=args.model,
            num_clips=args.num_clips,
            cleanup=not args.no_cleanup
        )
        print(json.dumps(res, indent=2))
        return 0 if res["status"] == "success" else 1
    except Exception as e:
        err = {"status": "error", "message": str(e)}
        print(json.dumps(err, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
