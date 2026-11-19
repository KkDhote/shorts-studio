---
name: universal-clipper
description: End-to-end autonomous pipeline to ingest YouTube videos, livestreams, or local files, detect high-retention viral hooks, apply smooth AI subject tracking, burn word-by-word karaoke captions, and export 1080x1920 Shorts.
---

# Universal Clipper Skill

An autonomous production-grade AI video pipeline that ingests long-form video (YouTube VODs, livestreams, podcasts, gaming, interviews) and outputs viral 9:16 vertical Shorts (1080x1920) with AI subject tracking and synchronized karaoke subtitles.

## Workspace Layout

```
e:\Cliping\
├── .venv\                           # Isolated Python 3.13 virtual environment
├── bin\                             # Standalone FFmpeg & FFprobe binaries
├── temp_work\                       # Ephemeral staging directory
├── final_clips\                     # Output directory for rendered Shorts
├── scripts\                         # Modular backend processing engines
│   ├── ingest.py                    # yt-dlp & local video intake
│   ├── transcribe.py                # faster-whisper word-level transcription
│   ├── smart_crop.py                # MediaPipe face tracking & pillarbox fallback
│   ├── render_captions.py           # .ass karaoke subtitles & H.264 burn
│   └── pipeline.py                  # End-to-end automated runner
└── .agent\skills\universal-clipper\
    └── SKILL.md                     # Agent skill definition
```

---

## Autonomous Execution Rules

Always execute steps via the workspace virtual environment:
- Windows: `.\.venv\Scripts\python.exe`

### Phase 1: Ingestion
Run `scripts/ingest.py` to stage video into `./temp_work/`:
```powershell
.\.venv\Scripts\python.exe scripts\ingest.py --input "<YOUTUBE_URL_OR_LOCAL_PATH>" --output-dir "./temp_work" --output-name "source"
```
- **YouTube URLs:** Employs `yt-dlp` with `--extractor-args "youtube:player_client=android,web"` and multi-layer retries to bypass 403 / throttling blocks.
- **Local Files:** Validates video stream integrity and remuxes to MP4 container if needed.

### Phase 2: Transcribe & Viral Scoring
1. **Transcribe:** Run `scripts/transcribe.py` to extract word-level timestamps with automatic CUDA acceleration (CPU int8 fallback) and Hinglish/Hindi code-switching support:
```powershell
.\.venv\Scripts\python.exe scripts\transcribe.py --input "./temp_work/source.mp4" --output "./temp_work/transcript.json" --model small
```
2. **Viral Hook Analysis:**
   Inspect `./temp_work/transcript.json` to score 3–5 high-retention windows:
   - **Target Duration:** 30–58 seconds per clip (strictly under 60 seconds).
   - **Hook Priority:** First 3 seconds must contain a strong curiosity hook, question, contrarian statement, or emotional trigger (e.g., "Why", "The truth about", "Never do this", "Kyun", "Kaise").
   - **Sentence Completeness:** The cut start and end MUST strictly land on complete sentence boundaries (matching punctuation `.`, `!`, `?`). Never cut mid-sentence.
   - **Speech Cadence:** Pacing between 2.2 and 3.8 words per second.

### Phase 3: Track, Caption & Render
For each selected timestamp interval `[START, END]`:

1. **Smart Cropping:**
```powershell
.\.venv\Scripts\python.exe scripts\smart_crop.py --input "./temp_work/source.mp4" --output "./temp_work/temp_crop_01.mp4" --start <START_SECONDS> --end <END_SECONDS> --target-width 1080 --target-height 1920
```
- Uses MediaPipe Face Detection with Exponential Moving Average (EMA) smoothing and deadband threshold to prevent camera jitter.
- If no subject is detected for >1.5 seconds, smoothly transitions to a 1080x1920 blurred-background pillarbox layout.

2. **Viral Karaoke Captions & Export:**
```powershell
.\.venv\Scripts\python.exe scripts\render_captions.py --input "./temp_work/temp_crop_01.mp4" --transcript "./temp_work/transcript.json" --output "./final_clips/clip_01_<hook-slug>.mp4" --start <START_SECONDS> --end <END_SECONDS> --font "Arial Black" --font-size 54 --highlight "#FFD700" --margin-v 280
```
- Formats 2–4 words per phrase.
- Highlights the active spoken word in `#FFD700` golden yellow with white surrounding text.
- Applies thick black outline and drop shadow.
- Enforces safe bottom margin (`MarginV=280`) to ensure captions are never hidden behind YouTube Shorts UI elements.
- Encodes with `CRF 20`, `AAC 192k` at 1080x1920.

### Phase 4: Verification & Ephemeral Cleanup
1. **Verification:** Inspect the generated `.mp4` files in `./final_clips/`. Verify:
   - File size > 0 bytes.
   - Duration matches target interval (30–58s).
   - Valid video and audio streams.
2. **Cleanup:** Delete ephemeral files in `./temp_work/` once all clips are verified:
```powershell
Remove-Item -Recurse -Force ./temp_work/*
```

---

## One-Command Autonomous Execution

To run the complete pipeline automatically in a single command:
```powershell
.\.venv\Scripts\python.exe scripts\pipeline.py --input "<YOUTUBE_URL_OR_LOCAL_PATH>" --model small --num-clips 3
```

---

## "Prompt 2" User Trigger Shortcut

Whenever the user prompts with **`Prompt 2`** followed by a YouTube link and highlights/moments:
1. Parse the video URL and highlight timestamps/descriptions.
2. Ingest, transcribe, smart-crop at 60 FPS, and burn word-by-word karaoke captions with 0.0ms audio-video sync.
3. Export the final 1080x1920 vertical Shorts into `./final_clips/`.
4. Stage the clips directly into `./final_clips/upload_queue.json` mapped to the 2-shorts-per-day Auto-Pilot schedule.
5. Wipe `./temp_work/` cleanly and output the summary table with viral titles and hashtags.
