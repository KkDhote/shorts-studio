# ✂️ Agent k2: Shorts & Meme Content Creator

## Role Overview
`k2` is an autonomous video editing and meme engineering agent. It takes long-form gaming videos (from `k1`'s queue or user links), discovers high-retention viral segments, crops them to 9:16 vertical, layers punchy meme content and sound effects, and burns synchronized word-by-word karaoke captions.

## Responsibilities
1. **Ingest & Audio Analysis**:
   - Ingest source video via `scripts/ingest.py`.
   - Transcribe audio with `scripts/transcribe.py` (faster-whisper) with word-level timestamps.
2. **Hook Detection & Segment Scoring**:
   - Identify 30–58 second segments.
   - Strictly score the first 3 seconds for curiosity triggers, emotional peaks, screaming, laughter, or shocking gameplay.
   - Ensure clean cut boundaries on sentence or action breaks (never cut mid-sentence).
3. **Smart 9:16 Cropping**:
   - Track faces (MediaPipe face detector with EMA smoothing) or dynamic center-of-action gameplay (`scripts/smart_crop.py`).
4. **Meme Enhancement Engine**:
   - Add sound effects (e.g. vine boom, bruh, punch impact, dramatic bass drop, meme laughs) at highlight peaks.
   - Optional meme overlays: GTA "WASTED" freeze/grayscale on player deaths, funny reaction punchline clips, or top meme banner text (`BRO WAS NOT READY FOR THIS 💀`).
5. **Karaoke Subtitles & Export**:
   - Burn synchronized word-by-word captions with `#FFD700` golden active word highlighting and thick black outline.
   - Enforce safe UI bottom margin (`MarginV=280`).
   - Export to `final_clips/clip_<ID>_<slug>.mp4` and attach creator attribution metadata.

## Command Line Execution
```powershell
# Process next candidate from research queue
.\.venv\Scripts\python.exe scripts\k2_shorts_creator.py --auto-queue

# Process specific video file or URL with meme enhancement
.\.venv\Scripts\python.exe scripts\k2_shorts_creator.py --input "./temp_work/source.mp4" --source-id "source_1" --add-memes --num-clips 3
```
