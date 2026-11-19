#!/usr/bin/env python3
"""
Dynamic 2-Shorts-Per-Day Auto-Scheduler.
Inspects existing queue and automatically allocates next open peak retention slots
(12:30 PM IST & 07:30 PM IST) for any new clips.
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

SLOTS = ["12:30 PM IST", "05:00 PM IST", "08:30 PM IST"]
IST = timezone(timedelta(hours=5, minutes=30))

def allocate_slots_for_new_clips(new_clip_files, queue_file=None):
    """
    Takes a list of new clip relative paths (or objects) and assigns them
    to the next available open slots in upload_queue.json.
    """
    base_dir = Path(__file__).resolve().parent.parent
    if queue_file is None:
        queue_file = base_dir / "final_clips" / "upload_queue.json"
    else:
        queue_file = Path(queue_file)

    queue = []
    if queue_file.exists():
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []

    # Map existing booked dates & slots
    booked = {}
    for item in queue:
        d = item.get("scheduled_date")
        s = item.get("schedule")
        if d and s:
            booked.setdefault(d, set()).add(s)

    now_ist = datetime.now(IST)
    current_date = now_ist.date()

    allocated = []
    for clip in new_clip_files:
        file_path = clip if isinstance(clip, str) else clip.get("file")
        
        # Find next open date & slot
        assigned_date = None
        assigned_slot = None

        search_date = current_date
        while not assigned_date:
            date_str = search_date.strftime("%Y-%m-%d")
            day_booked = booked.get(date_str, set())

            for slot in SLOTS:
                # If checking today, verify time hasn't passed
                if search_date == current_date:
                    slot_hour_min = slot.replace(" IST", "")
                    slot_dt = datetime.strptime(f"{date_str} {slot_hour_min}", "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
                    if now_ist >= slot_dt:
                        continue # slot in past today

                if slot not in day_booked:
                    assigned_date = date_str
                    assigned_slot = slot
                    booked.setdefault(date_str, set()).add(slot)
                    break

            if not assigned_date:
                search_date += timedelta(days=1)

        slot_label = f"{datetime.strptime(assigned_date, '%Y-%m-%d').strftime('%b %d')} ({assigned_slot})"
        
        if isinstance(clip, dict):
            clip["scheduled_date"] = assigned_date
            clip["schedule"] = assigned_slot
            clip["slot_label"] = slot_label
            allocated.append(clip)
        else:
            allocated.append({
                "file": file_path,
                "scheduled_date": assigned_date,
                "schedule": assigned_slot,
                "slot_label": slot_label
            })

    return allocated

def sync_unassigned_clips(queue_file=None):
    """
    Scans queue and assigns any unassigned or newly added clip to the next open slots.
    """
    base_dir = Path(__file__).resolve().parent.parent
    if queue_file is None:
        queue_file = base_dir / "final_clips" / "upload_queue.json"
    else:
        queue_file = Path(queue_file)

    if not queue_file.exists():
        return []

    with open(queue_file, "r", encoding="utf-8") as f:
        queue = json.load(f)

    changed = False
    unassigned = [item for item in queue if not item.get("uploaded", False) and not item.get("scheduled_date")]

    if unassigned:
        allocate_slots_for_new_clips(unassigned, queue_file)
        changed = True

    if changed:
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

    return queue

if __name__ == "__main__":
    q = sync_unassigned_clips()
    print(f"Synced {len(q)} items in upload_queue.json.")
