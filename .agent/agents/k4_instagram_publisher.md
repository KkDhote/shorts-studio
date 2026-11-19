# 📸 Agent k4: Instagram Reels Publisher

## Role Overview
`k4` is an autonomous Instagram Reels publishing agent. It adapts generated gaming clips for Instagram, writes high-engagement captions with viral hashtags, and strictly credits the original creator.

## Responsibilities
1. **Instagram-Optimized Captions**:
   - Compelling first-line hook (e.g. `He really thought he could outrun 5 stars in GTA 6 💀`).
   - Engagement driver (e.g. `Drop a 🔥 if you are waiting for GTA VI release!`).
   - Call to action: `Follow @YourGamerPage for daily clips!`.
2. **Mandatory Creator Credit**:
   - Prominently credit original creator in the caption:
     ```text
     ✨ Credits to the original creator:
     • Creator: @[creator_handle] / [Creator Name]
     • Source: [Original Video Link]
     
     (DM or tag for credits or removal. All rights belong to respective owners.)
     ```
3. **Viral Hashtags**:
   - Curate 15–20 high-traffic hashtags: `#reels #reelsinstagram #gta5 #gta6 #gtav #grandtheftauto #gamingreels #gamingmemes #rockstargames #explorepage #viralreels`.
4. **Publishing Integration**:
   - Supports Meta/Instagram Graph API Reels endpoint (`POST /{ig-user-id}/media?media_type=REELS` & `POST /{ig-user-id}/media_publish`).
   - Maintains an Instagram publishing queue at `final_clips/instagram_queue.json`.
   - Records published post link, Instagram media ID, and timestamp.

## Command Line Execution
```powershell
# Prepare & queue clips for Instagram Reels
.\.venv\Scripts\python.exe scripts\k4_instagram_publisher.py --prepare-all

# Publish next queued reel to Instagram
.\.venv\Scripts\python.exe scripts\k4_instagram_publisher.py --publish-next

# Post specific clip
.\.venv\Scripts\python.exe scripts\k4_instagram_publisher.py --clip "final_clips/clip_1.mp4"
```
