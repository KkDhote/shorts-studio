# 🎯 Agent k1: Gaming Video Researcher

## Role Overview
`k1` is an autonomous gaming content researcher specializing in YouTube gaming videos, with a primary focus on **GTA 5, GTA 6**, and viral gaming moments (e.g., crazy stunts, hilarious fails, mods, leaks, and pro gameplay from top creators like CarryMinati, Mythpat, Techno Gamerz, theRadBrad, Total Gaming, DarkViperAU, TGG).

## Responsibilities
1. **Search & Discovery**:
   - Continuously or on-demand search YouTube for trending, high-velocity gaming videos.
   - Target keywords: `GTA 6 gameplay`, `GTA 5 funny moments`, `GTA 6 leaks`, `GTA V insane stunts`, `Techno Gamerz GTA`, `theRadBrad GTA 6`, `CarryMinati GTA 6`.
2. **Quality & Suitability Filtering**:
   - Video duration between 3 and 60 minutes (optimal for long-form highlight extraction).
   - Minimum view threshold / high engagement velocity.
   - Verify presence of active commentary or clear gameplay audio.
3. **Creator Attribution Extraction**:
   - Extract `creator_name`, `channel_handle`, `channel_url`, `subscribers`, `video_title`, `video_url`, `video_id`, `duration`, and `thumbnail`.
4. **Queue Registration**:
   - Register the candidate into `final_clips/sources_registry.json`.
   - Add task ticket to `final_clips/research_queue.json` for Agent `k2` to process.

## Command Line Execution
```powershell
# Search and queue top GTA 5 / GTA 6 videos
.\.venv\Scripts\python.exe scripts\k1_researcher.py --query "GTA 6 gameplay" --max-results 5

# Research specific creator
.\.venv\Scripts\python.exe scripts\k1_researcher.py --creator "theRadBrad" --query "GTA 5"

# Register direct YouTube URL with attribution
.\.venv\Scripts\python.exe scripts\k1_researcher.py --url "https://www.youtube.com/watch?v=EXAMPLE_ID"
```
