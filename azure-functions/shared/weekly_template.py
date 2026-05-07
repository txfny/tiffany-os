"""
Weekly template — the ONLY source of truth for session types.
Deterministic. No interpretation. No Claude override.
"""

import os
import json
import glob
from datetime import date, timedelta

WEEKLY_TEMPLATE = {
    0: {  # Monday
        "type": "strength",
        "focus": "Upper body circuit + core",
        "location": "home_gym",
        "with_bf": False,
        "morning": "treadmill_warmup",
        "training_style": "circuit",
        "priority_note": "Dedicated upper day: OHP, lat pulldown, dumbbell row, chest press, tricep work as circuit rounds (3 rounds), 60-90s rest between rounds. Core circuit after. ~45 min total. Fresh from weekend rest — best day for upper progression.",
    },
    1: {  # Tuesday
        "type": "strength",
        "focus": "Lower body + core",
        "location": "home_gym",  # keep home as default
        "with_bf": False,
        "morning": "treadmill_warmup",
        "training_style": "circuit",
        "priority_note": "Tuesday = lower body + dedicated core circuit. This avoids 48h upper-body overlap with Monday and keeps Tuesday available for lower-focused work.",
    },
    2: {  # Wednesday
        "type": "active_recovery",
        "focus": "Zone 2 treadmill walk (45-60 min) + YouTube",
        "location": "home_gym",
        "with_bf": True,
        "morning": "run_or_elliptical_optional",
    },
    3: {  # Thursday
        "type": "strength",
        "focus": "Full body circuit + core",
        "location": "home_gym",
        "with_bf": True,
        "morning": "treadmill_warmup",
        "training_style": "circuit",
        "priority_note": "Circuit format: all exercises back-to-back as rounds (3 rounds), 60-90s rest between rounds. Core circuit after. Different exercise selection from Monday (rotation logic).",
    },
    4: {  # Friday
        "type": "cardio",
        "focus": "Zone 2 treadmill or HIIT intervals — mood-based",
        "location": "home_gym",
        "with_bf": True,
        "morning": "treadmill",
        "priority_note": "Feeling good → 20-25 min treadmill intervals (walk 2 min / jog 1 min). Feeling meh → 45-60 min treadmill walk + YouTube.",
    },
    5: {  # Saturday
        "type": "rest_or_light_cardio",
        "focus": "Run, elliptical, walk, or full rest — your call",
        "location": "home_gym",
        "with_bf": False,
    },
    6: {  # Sunday
        "type": "rest",
        "focus": "Full rest or walk",
        "location": None,
        "with_bf": False,
    },
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_session_type(target_date) -> dict:
    """Return the session type for a given date. Deterministic."""
    weekday = target_date.weekday()  # 0=Mon, 6=Sun
    template = WEEKLY_TEMPLATE[weekday].copy()
    template["day_name"] = DAY_NAMES[weekday]
    template["date"] = target_date.isoformat()
    return template


def resolve_session_type(target_date, sessions_dir, readiness_tier):
    """
    Post-process session type: if a strength focus was missed earlier this week,
    and today can absorb it, modify the session type.

    Rules:
    - Only Wed/Thu can absorb missed strength sessions
    - Readiness must be MODERATE or HIGH
    - Most recent miss wins (one pending at a time)
    - Debt expires at week boundary

    Returns: (session_type_dict, reschedule_info_or_None)
    """
    template = get_session_type(target_date)
    weekday = target_date.weekday()

    # Only Wed (2) and Thu (3) can absorb
    if weekday not in (2, 3):
        return template, None

    # Don't reschedule if still recovering
    if readiness_tier == "LOW":
        return template, None

    # Find this week's Monday
    monday = target_date - timedelta(days=weekday)

    # Scan session JSONs from Monday through yesterday
    missed_focus = None
    missed_date = None

    for days_offset in range(weekday - 1, -1, -1):  # yesterday back to Monday
        check_date = monday + timedelta(days=days_offset)
        pattern = os.path.join(sessions_dir, f"{check_date.isoformat()}*.json")
        files = glob.glob(pattern)
        if not files:
            continue
        with open(files[0]) as fh:
            session = json.load(fh)

        scheduled = session.get("scheduled_type")
        actual = session.get("session_type", "")

        # Detect miss: was scheduled as strength but didn't do strength
        if scheduled == "strength" and "strength" not in actual.lower():
            missed_focus = session.get("scheduled_focus")
            missed_date = check_date.isoformat()
            break  # most recent miss wins

    if not missed_focus:
        return template, None

    # Build rescheduled session type
    rescheduled = template.copy()
    rescheduled["type"] = "strength"
    rescheduled["focus"] = missed_focus
    rescheduled["rescheduled_from"] = missed_date

    if weekday == 2:  # Wednesday: normally recovery, so flag reduced volume
        rescheduled["volume_note"] = "Rescheduled session — reduced volume recommended"

    reschedule_info = {
        "missed_focus": missed_focus,
        "missed_date": missed_date,
        "rescheduled_to": target_date.isoformat(),
        "original_day_type": template["type"],
    }

    return rescheduled, reschedule_info
