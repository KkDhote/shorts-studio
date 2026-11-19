---
name: gaming-agent-swarm
description: 4-Agent automated gaming pipeline (k1, k2, k3, k4) to discover GTA 5, GTA 6 & gaming videos, extract viral meme shorts, and auto-publish to YouTube Shorts and Instagram Reels with mandatory original creator credits.
---

# 🎮 4-Agent Autonomous Gaming Pipeline (k1, k2, k3, k4)

This skill coordinates four specialized autonomous agents designed to discover viral gaming gameplay, convert long videos into meme-enhanced vertical shorts, and publish them to YouTube Shorts and Instagram Reels with proper creator attribution.

---

## 🤖 The 4 Agents

### 1. `k1` — Gaming Video Researcher (`scripts/k1_researcher.py`)
- **Mission**: Scans YouTube for trending, high-velocity GTA 5, GTA 6, and gaming content (funny fails, crazy stunts, leaks, walkthroughs, mods).
- **Attribution Guard**: Extracts and registers creator names, channel handles, URLs, and video source links into `final_clips/sources_registry.json`.
- **Handoff**: Pushes analyzed video tickets to `final_clips/research_queue.json` for Agent `k2`.

### 2. `k2` — Shorts & Meme Creator (`scripts/k2_shorts_creator.py` + `scripts/meme_enhancer.py`)
- **Mission**: Analyzes candidate videos, transcribes speech with word-level timestamps (faster-whisper), and extracts 30–58s viral windows with strong opening hooks (<3s).
- **Crop & Tracking**: 9:16 vertical crop with MediaPipe face detection and dynamic gameplay action centering.
- **Meme Enhancements**: Adds viral hook banners (`BRO WAS NOT READY FOR THIS 💀`, `GTA 6 PHYSICS GONE WRONG 😂`), meme sound effects, and GTA "WASTED" dramatic punchlines.
- **Captions**: Burns word-by-word synchronized karaoke subtitles (`#FFD700` golden highlight, black border, safe UI bottom margin).
- **Handoff**: Automatically schedules the clip into peak IST slots in `final_clips/upload_queue.json` and syncs with `final_clips/instagram_queue.json`.

### 3. `k3` — YouTube Shorts Publisher (`scripts/k3_youtube_publisher.py`)
- **Mission**: Publishes ready vertical clips to the YouTube channel.
- **Metadata**: Generates curiosity-driven titles with `#shorts` and emojis.
- **Mandatory Creator Credit**:
  ```text
  🎮 ORIGINAL GAMEPLAY & CREATOR CREDIT:
  • Creator: [Creator Name] ([Channel Handle])
  • Original Video: [Video URL]
  • Channel: [Channel URL]

  Support the original creator! Transformation curated for gaming entertainment.
  #Shorts #GTA5 #GTA6 #Gaming #ShortsFeed
  ```
- **Execution**: Official YouTube Data API v3 (`scripts/upload_youtube.py`) with persistent OAuth refresh tokens.

### 4. `k4` — Instagram Reels Publisher (`scripts/k4_instagram_publisher.py`)
- **Mission**: Publishes gaming reels to the connected Instagram account.
- **Instagram Captions**: Generates punchy 1-line hook, comment engagement question, and viral hashtags (`#reels #gamingreels #gta5 #gta6 #gtav #explorepage`).
- **Mandatory Creator Credit**:
  ```text
  ✨ CREDITS TO ORIGINAL CREATOR:
  • Creator: @[channel_handle] / [Creator Name]
  • Source: [Original Video Link]
  (DM or tag for credits or removal. All rights belong to respective owners.)
  ```
- **Execution**: Meta Graph API Reels integration (`POST /{ig-user-id}/media?media_type=REELS` & `media_publish`) with staging queue at `final_clips/instagram_queue.json`.

---

## ⚡ Quick Run Commands

```powershell
# 1. Check status of all 4 agents
.\.venv\Scripts\python.exe scripts\orchestrate_k_agents.py --status

# 2. Run Agent k1 (Search gaming videos)
.\.venv\Scripts\python.exe scripts\k1_researcher.py --query "GTA 6 gameplay" --max-results 3

# 3. Run Agent k2 (Process next video & create meme shorts)
.\.venv\Scripts\python.exe scripts\k2_shorts_creator.py --auto-queue

# 4. Run Agent k3 (Post next short to YouTube with creator credit)
.\.venv\Scripts\python.exe scripts\k3_youtube_publisher.py --publish-next

# 5. Run Agent k4 (Post next reel to Instagram with creator credit)
.\.venv\Scripts\python.exe scripts\k4_instagram_publisher.py --publish-next
```
