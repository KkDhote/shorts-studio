---
description: Automatically triggers universal-clipper whenever the user inputs 'Prompt 2' with a YouTube link and highlights.
---

# Prompt 2 Trigger Rule

Whenever the USER starts a message with `Prompt 2` (or provides a YouTube link and highlights/moments), follow this exact behavior:

1. **Extract Inputs:**
   - **Video URL:** The provided YouTube / stream / video link.
   - **Highlights & Moments:** The provided timestamps, descriptions, or number of clips (default to the highlighted moments, or 3–5 clips if unspecified, 25 to 65 seconds each).
   - **Framing Mode:** Auto-Detect (`streamer-split` for corner facecam streamers, `fullscreen-crop` for gameplay/vlogs/cinematics).
   - **Captions:** Word-by-word karaoke typography (`#FFD700` yellow highlight, safe bottom margin `MarginV=280`).

2. **Execute Full Universal Clipper Pipeline Autonomously:**
   - Ingest source slices into `temp_work/` using `yt-dlp`.
   - Transcribe with word timestamps (`scripts/transcribe.py`).
   - Run AI subject tracking & framing at 60 FPS (`scripts/smart_crop.py`).
   - Burn karaoke subtitles with verified 0.0ms audio-video sync (`scripts/render_captions.py`).
   - Output rendered 1080x1920 60 FPS vertical Shorts into `final_clips/`.
   - Wipe `temp_work/` cleanly upon completion.

3. **Stage into Studio & Auto-Pilot:**
   - Append the new clips into `final_clips/upload_queue.json` with viral titles, hashtags, and assigned 2-shorts-per-day peak slots (`12:30 PM IST` and `07:30 PM IST`).
   - The live web dashboard (`http://localhost:5050` and mobile tunnel) will automatically show the new clips ready for approval or auto-posting!

4. **Deliver Concise Summary:**
   - Print summary table with filenames, exact timestamps, opening hook lines, detected layouts, viral titles, and 5 niche hashtags.
