---
description: Rule that automatically schedules every newly rendered or ingested clip into the next available 3-shorts-per-day slot.
---

# Dynamic Auto-Scheduling Rule (3 Shorts Per Day)

Whenever new clips are processed, rendered, or added to `final_clips/`:

1. **Automatic Slot Allocation (3 Shorts / Day):**
   - Call `scripts.auto_scheduler.allocate_slots_for_new_clips()` or `sync_unassigned_clips()`.
   - Never leave a new clip unassigned.
   - Inspect the existing calendar in `final_clips/upload_queue.json` and find the earliest open slot among the 3 daily peak windows:
     - **Slot 1 (Afternoon Rush):** `12:30 PM IST` (+28% retention boost)
     - **Slot 2 (Evening Peak):** `05:00 PM IST` (+35% viral spread)
     - **Slot 3 (Prime Night Binge):** `08:30 PM IST` (+45% peak retention)
   - Assign `scheduled_date` (`YYYY-MM-DD`) and `schedule` (`12:30 PM IST`, `05:00 PM IST`, or `08:30 PM IST`).

2. **Autonomous Auto-Pilot Enforcement:**
   - If the creator reviews the clip in the studio and taps `Review & Post`, they can drop it immediately.
   - If the creator forgets or is away from their device when the scheduled time arrives, the background Auto-Pilot automatically posts it to **KULDEEPBHAI GAMER** with zero manual intervention required.
   - Enforce a maximum daily limit of 3 Shorts to prevent algorithmic cannibalization.
