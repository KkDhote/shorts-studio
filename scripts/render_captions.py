"""
Render Captions module for Universal Video Clipper.
Generates viral karaoke-style .ass subtitles and burns them into 9:16 video.
Features:
- 2–4 words per phrase (punchy viral cadence)
- Bold sans-serif typography (Arial Black / Montserrat)
- Thick black stroke and drop shadow
- Active spoken word highlighted in golden yellow (#FFD700)
- Safe margin (MarginV=280) avoiding YouTube Shorts UI overlay
- High-quality H.264 CRF 20 / AAC 192k FFmpeg export
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def get_ffmpeg_path() -> str:
    workspace_dir = Path(__file__).resolve().parent.parent
    local_bin = workspace_dir / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if local_bin.exists():
        return str(local_bin)
    venv_bin = workspace_dir / ".venv" / "Scripts" / "ffmpeg.exe" if sys.platform == "win32" else workspace_dir / ".venv" / "bin" / "ffmpeg"
    if venv_bin.exists():
        return str(venv_bin)
    return shutil.which("ffmpeg") or "ffmpeg"


def hex_to_ass_color(hex_str: str) -> str:
    """Convert #RRGGBB or RRGGBB to ASS &H00BBGGRR&."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 6:
        r = hex_clean[0:2]
        g = hex_clean[2:4]
        b = hex_clean[4:6]
        return f"&H00{b}{g}{r}&"
    return "&H0000D7FF&"


def format_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format: H:MM:SS.cs (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def extract_clip_words(transcript_data: dict, clip_start: float, clip_end: float) -> list[dict]:
    """Extract and re-index words falling within [clip_start, clip_end]."""
    words = []
    segments = transcript_data.get("segments", [])

    for seg in segments:
        seg_words = seg.get("words", [])
        if seg_words:
            for w in seg_words:
                w_start = w["start"]
                w_end = w["end"]
                # Include word if it overlaps with clip interval
                if w_end > clip_start and w_start < clip_end:
                    # Offset timestamps relative to clip start
                    rel_start = max(0.0, w_start - clip_start)
                    rel_end = max(rel_start + 0.05, w_end - clip_start)
                    words.append({
                        "word": w["word"].strip(),
                        "start": round(rel_start, 3),
                        "end": round(rel_end, 3)
                    })
        else:
            # Fallback if segment has no word-level timestamps: approximate
            seg_s = seg["start"]
            seg_e = seg["end"]
            if seg_e > clip_start and seg_s < clip_end:
                text_words = seg.get("text", "").strip().split()
                if text_words:
                    dur_per_word = (seg_e - seg_s) / len(text_words)
                    for i, tw in enumerate(text_words):
                        tw_s = seg_s + (i * dur_per_word)
                        tw_e = tw_s + dur_per_word
                        if tw_e > clip_start and tw_s < clip_end:
                            words.append({
                                "word": tw,
                                "start": round(max(0.0, tw_s - clip_start), 3),
                                "end": round(max(0.05, tw_e - clip_start), 3)
                            })

    return sorted(words, key=lambda x: x["start"])


def chunk_words_into_phrases(words: list[dict], min_words: int = 2, max_words: int = 4, max_gap: float = 0.4) -> list[list[dict]]:
    """Group words into short, rhythmic 2–4 word phrases."""
    phrases = []
    current_phrase = []

    for w in words:
        if not current_phrase:
            current_phrase.append(w)
            continue

        prev_w = current_phrase[-1]
        gap = w["start"] - prev_w["end"]
        has_punctuation = any(prev_w["word"].endswith(p) for p in [".", "?", "!", ",", ";"])

        if len(current_phrase) >= max_words or gap > max_gap or (has_punctuation and len(current_phrase) >= min_words):
            phrases.append(current_phrase)
            current_phrase = [w]
        else:
            current_phrase.append(w)

    if current_phrase:
        phrases.append(current_phrase)

    return phrases


def generate_karaoke_ass(
    words: list[dict],
    output_ass_path: Path,
    font_name: str = "Arial Black",
    font_size: int = 54,
    highlight_hex: str = "#FFD700",
    margin_v: int = 280,
    words_per_phrase: int = 3
) -> None:
    """Generate .ass subtitle content with word-by-word karaoke highlighting."""
    highlight_ass = hex_to_ass_color(highlight_hex)
    white_ass = "&H00FFFFFF&"
    stroke_ass = "&H00000000&"
    shadow_ass = "&H80000000&"

    header = f"""[Script Info]
Title: Viral Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{white_ass},{highlight_ass},{stroke_ass},{shadow_ass},-1,0,0,0,100,100,2,0,1,5,3,2,60,60,{margin_v},1
Style: TopPill,Arial Black,34,{white_ass},{highlight_ass},{stroke_ass},{shadow_ass},-1,0,0,0,100,100,1,0,1,4,2,8,40,40,160,1
Style: OutroCTA,Arial Black,52,{highlight_ass},{white_ass},{stroke_ass},{shadow_ass},-1,0,0,0,108,108,2,0,1,6,4,2,50,50,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    phrases = chunk_words_into_phrases(words, min_words=2, max_words=words_per_phrase)
    dialogue_lines = []

    for phrase in phrases:
        if not phrase:
            continue

        phrase_start = phrase[0]["start"]
        phrase_end = phrase[-1]["end"]

        # Ensure active word transitions are contiguous
        for idx, active_word in enumerate(phrase):
            w_start = active_word["start"]
            # Active word end extends until next word starts, or until phrase end
            if idx + 1 < len(phrase):
                w_end = phrase[idx + 1]["start"]
            else:
                w_end = phrase_end

            if w_end <= w_start:
                w_end = w_start + 0.1

            start_ass = format_ass_time(w_start)
            end_ass = format_ass_time(w_end)

            # Build line text: uppercase words with active word colored in highlight_ass
            rendered_words = []
            for j, w in enumerate(phrase):
                text_clean = w["word"].upper()
                if j == idx:
                    # Highlight active word
                    rendered_words.append(f"{{\\c{highlight_ass}\\fscx106\\fscy106}}{text_clean}{{\\c{white_ass}\\fscx100\\fscy100}}")
                else:
                    rendered_words.append(f"{{\\c{white_ass}}}{text_clean}")

            line_text = " ".join(rendered_words)
            dialogue_lines.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{line_text}")

    # Add Subscribe & Comment reminder badge throughout the clip
    clip_duration = words[-1]["end"] if words else 35.0
    cta_start = format_ass_time(0.5)
    cta_end = format_ass_time(clip_duration)
    dialogue_lines.append(
        f"Dialogue: 1,{cta_start},{cta_end},TopPill,,0,0,0,,{{\\bord4\\shad2\\c{highlight_ass}}}🔔 SUBSCRIBE {{\\c{white_ass}}}& {{\\c{highlight_ass}}}COMMENT 👇"
    )

    # In final 4.5 seconds of the short, add prominent outro CTA
    if clip_duration > 6.0:
        outro_start = format_ass_time(max(0.0, clip_duration - 4.5))
        dialogue_lines.append(
            f"Dialogue: 2,{outro_start},{cta_end},OutroCTA,,0,0,0,,{{\\an2\\pos(540,1400)\\bord5\\shad3\\c{highlight_ass}}}🔔 SUBSCRIBE FOR DAILY GTA 6!\\N{{\\fs40\\c{white_ass}}}💬 DROP A COMMENT BELOW 👇"
        )

    full_ass_content = header + "\n".join(dialogue_lines) + "\n"

    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(full_ass_content)


def burn_captions(
    input_video: str,
    ass_path: Path,
    output_video: str,
    fps: int = 30
) -> dict:
    ffmpeg_bin = get_ffmpeg_path()
    out_path = Path(output_video)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # To avoid Windows colon and backslash escaping issues in FFmpeg -vf,
    # run ffmpeg with working directory set to ass_path.parent
    ass_dir = ass_path.parent.resolve()
    ass_filename = ass_path.name
    abs_input = Path(input_video).resolve()
    abs_output = out_path.resolve()

    cmd = [
        ffmpeg_bin, "-y",
        "-i", str(abs_input),
        "-vf", f"ass={ass_filename}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(abs_output)
    ]

    print(f"[render_captions] Burning karaoke subtitles via FFmpeg...", file=sys.stderr)
    res = subprocess.run(cmd, cwd=str(ass_dir), capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg caption burn failed:\n{res.stderr}")

    return {
        "status": "success",
        "output_file": str(abs_output),
        "ass_file": str(ass_path.resolve())
    }


def main():
    parser = argparse.ArgumentParser(description="Generate and burn viral karaoke subtitles into 9:16 video.")
    parser.add_argument("--input", "-i", required=True, help="Cropped 9:16 input video path")
    parser.add_argument("--transcript", "-t", required=True, help="Transcript JSON file path (from transcribe.py)")
    parser.add_argument("--output", "-o", required=True, help="Output video path with burned captions")
    parser.add_argument("--start", "-s", type=float, default=0.0, help="Start time offset in original video (seconds)")
    parser.add_argument("--end", "-e", type=float, default=None, help="End time offset in original video (seconds)")
    parser.add_argument("--font", default="Arial Black", help="Subtitle font family (default: Arial Black)")
    parser.add_argument("--font-size", type=int, default=54, help="Font size (default: 54)")
    parser.add_argument("--highlight", default="#FFD700", help="Active word highlight hex color (default: #FFD700)")
    parser.add_argument("--margin-v", type=int, default=280, help="Bottom margin (default: 280)")
    parser.add_argument("--words-per-phrase", type=int, default=3, help="Max words per subtitle phrase (default: 3)")
    parser.add_argument("--fps", type=int, default=60, help="Output video framerate (default: 60)")
    args = parser.parse_args()

    try:
        with open(args.transcript, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        clip_end = args.end if args.end is not None else transcript_data.get("duration", 999999.0)
        words = extract_clip_words(transcript_data, args.start, clip_end)

        temp_dir = Path(tempfile.mkdtemp(prefix="karaoke_ass_"))
        ass_path = temp_dir / "subtitles.ass"

        generate_karaoke_ass(
            words=words,
            output_ass_path=ass_path,
            font_name=args.font,
            font_size=args.font_size,
            highlight_hex=args.highlight,
            margin_v=args.margin_v,
            words_per_phrase=args.words_per_phrase
        )

        result = burn_captions(
            input_video=args.input,
            ass_path=ass_path,
            output_video=args.output,
            fps=args.fps
        )

        shutil.rmtree(temp_dir, ignore_errors=True)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        err = {"status": "error", "message": str(e)}
        print(json.dumps(err, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
