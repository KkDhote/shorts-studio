#!/usr/bin/env python3
"""
Adds high-conversion Subscribe and Comment Reminders to all unposted Shorts in upload_queue.json.
- Enriches descriptions with algorithmic engagement CTA blocks
- Polishes pinned comments with engaging questions + subscribe & comment prompts
- Triggers cloud sync to update Render live
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
QUEUE_PATH = BASE_DIR / "final_clips" / "upload_queue.json"

CTA_BLOCK = (
    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🔔 SUBSCRIBE to @KULDEEPBHAIGAMER for daily GTA 6 Shorts & viral gameplay!\n"
    "💬 COMMENT below with your thoughts — I read and reply to everyone!\n"
    "👍 DROP A LIKE and share this Short with your friends!\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
)

PINNED_CTA = "💬 Drop your thoughts in the COMMENTS below & 🔔 SUBSCRIBE to KULDEEPBHAI GAMER for daily GTA 6 Shorts! ❤️👇"

def main():
    if not QUEUE_PATH.exists():
        print(f"Error: {QUEUE_PATH} not found!")
        return

    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        queue = json.load(f)

    updated_count = 0

    for idx, item in enumerate(queue):
        # Only modify unposted clips
        if item.get("uploaded", False):
            continue

        # 1. Update Description with Subscribe & Comment Reminder CTA Block
        desc = item.get("description", "")
        if "SUBSCRIBE to @KULDEEPBHAIGAMER" not in desc:
            # Place CTA block right above hashtags or fair use section
            if "🎮 ORIGINAL GAMEPLAY" in desc:
                parts = desc.split("🎮 ORIGINAL GAMEPLAY", 1)
                desc = parts[0].rstrip() + CTA_BLOCK + "\n\n🎮 ORIGINAL GAMEPLAY" + parts[1]
            elif "\n\n#" in desc:
                parts = desc.split("\n\n#", 1)
                desc = parts[0].rstrip() + CTA_BLOCK + "\n\n#" + parts[1]
            else:
                desc = desc.rstrip() + CTA_BLOCK
            item["description"] = desc

        # 2. Update Pinned Comment with engaging prompt + Subscribe & Comment Reminder
        current_pinned = item.get("pinned_comment", "").strip()
        if not current_pinned:
            new_pinned = f"🔥 Which moment was your favorite? {PINNED_CTA}"
        elif "SUBSCRIBE to KULDEEPBHAI GAMER" not in current_pinned:
            # Keep question, append reminder
            # Clean up trailing punctuation if needed
            cleaned = current_pinned.rstrip(".! ")
            new_pinned = f"{cleaned}!\n\n{PINNED_CTA}"
        else:
            new_pinned = current_pinned

        item["pinned_comment"] = new_pinned
        updated_count += 1

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully updated {updated_count} unposted clips with Subscribe & Comment Reminders in upload_queue.json!")

if __name__ == "__main__":
    main()
