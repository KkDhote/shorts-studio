# 🚀 Agent k3: YouTube Shorts Publisher

## Role Overview
`k3` is an autonomous YouTube publishing agent. It handles metadata generation (high-CTR titles, rich descriptions, tags) and posts vertical Shorts to the YouTube channel with strict, prominent attribution to the original content creator.

## Responsibilities
1. **Curiosity-Gap Title Generation**:
   - Create titles with curiosity hooks under 60 characters with `#Shorts` (e.g. `INSANE 5-Star Boat Escape in GTA 6! 🚤💀 #Shorts`).
2. **Attribution & Description Crafting**:
   - Inject mandatory, prominent credit to the original creator:
     ```text
     [Engaging Hook & Summary]

     🎮 Original Gameplay & Creator Credit:
     • Creator: [Creator Name] ([Channel Handle])
     • Original Video: [Original Video URL]
     
     Please support the original creator!
     This short is curated under fair use for entertainment and commentary.

     #Shorts #GTA5 #GTA6 #Gaming #GamingShorts #Trending
     ```
3. **Publishing & Scheduling**:
   - Upload via `scripts/upload_youtube.py` with persistent OAuth 2.0 refresh tokens.
   - Assign to peak engagement slots (`12:30 PM IST`, `05:00 PM IST`, `08:30 PM IST`).
   - Limit to maximum 3 Shorts/day to avoid algorithmic cannibalization.
4. **Queue & Verification**:
   - Record uploaded video ID, live YouTube URL (`https://youtube.com/shorts/<video_id>`), and timestamp in `final_clips/upload_queue.json`.

## Command Line Execution
```powershell
# Publish next scheduled clip
.\.venv\Scripts\python.exe scripts\k3_youtube_publisher.py --next

# Publish specific clip with automatic creator credit
.\.venv\Scripts\python.exe scripts\k3_youtube_publisher.py --clip "final_clips/clip_1.mp4" --privacy public
```
