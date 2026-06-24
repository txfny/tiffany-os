"""
Coach Pipeline — the deterministic backbone.

This is the full pipeline that runs before Claude does any reasoning.
It gathers data, computes readiness, validates gaps, and returns a
structured context object that Claude uses to build the session.

Claude's job: take this context and generate the session plan + justification.
This code's job: everything else.
"""

import json
from datetime import date, datetime, timedelta
import sys
import os

# Add parent dir to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.weekly_template import get_session_type, resolve_session_type
from shared.readiness import compute_readiness, compute_hrv_baseline
from shared.ivg import run_ivg
from shared.ovg import run_ovg
from shared.working_weights import get_working_weights
from shared.save_session import save_snapshot, save_session_log
from shared.exercise_selection import select_exercises
from shared.post_workout_analysis import analyze_post_workout
from shared.trend_brain import build_trend_digest


def _get_sessions_dir():
    """Find the data/sessions directory."""
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "..", "data", "sessions")
    if os.path.isdir(d):
        return d
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "data", "sessions")


def _load_previous_session_flags(target_date: date) -> list:
    """Load post-workout analysis flags from yesterday's session JSON."""
    import glob as _glob
    sessions_dir = _get_sessions_dir()

    # Check yesterday and day before (in case yesterday was rest with no file)
    for days_back in range(1, 4):
        check_date = target_date - timedelta(days=days_back)
        pattern = os.path.join(sessions_dir, f"{check_date.isoformat()}*.json")
        files = _glob.glob(pattern)
        if files:
            with open(files[0]) as fh:
                session = json.load(fh)
            pwa = session.get("post_workout_analysis", {})
            flags = pwa.get("flags", [])
            if flags:
                return flags
    return []


def run_pre_session(target_date: date, snapshot: dict) -> dict:
    """
    Run the full pre-session pipeline. Returns structured context for Claude.

    Steps:
    1. Session type lookup (deterministic)
    2. Readiness computation (deterministic)
    3. IVG check (deterministic)
    4. Working weights fetch (deterministic)

    Claude receives this output and builds the session plan from it.
    """
    sessions_dir = _get_sessions_dir()

    # Step 1: What type of session is today? (raw template)
    scheduled_session = get_session_type(target_date)

    # Step 1.5: Load previous session flags for readiness
    previous_flags = _load_previous_session_flags(target_date)

    # Step 1.6: Compute rolling HRV baseline from session history
    hrv_baseline = compute_hrv_baseline(sessions_dir, target_date)

    # Step 2: What's the readiness tier?
    readiness = compute_readiness(snapshot, previous_session_flags=previous_flags,
                                  hrv_baseline=hrv_baseline)

    # Step 2.5: Check for missed session rescheduling
    session_type, reschedule_info = resolve_session_type(
        target_date, sessions_dir, readiness["tier"]
    )

    # Step 3: Any gaps in this week's data?
    ivg = run_ivg(target_date)

    # Step 4: Current working weights
    weights = get_working_weights()

    # Step 5: Exercise selection (strength days only)
    exercise_plan = None
    if session_type.get("type") == "strength":
        exercise_plan = select_exercises(
            target_date=target_date,
            session_type="strength",
            focus=session_type.get("focus", ""),
            location=snapshot.get("equipment", session_type.get("location", "home_gym")),
            working_weights=weights.get("weights", {}),
        )

    # Step 6: Cross-session trend digest (Phase 2)
    trend_digest = build_trend_digest(target_date, sessions_dir=sessions_dir)

    return {
        "date": target_date.isoformat(),
        "session_type": session_type,
        "scheduled_type": scheduled_session["type"],
        "scheduled_focus": scheduled_session["focus"],
        "reschedule_info": reschedule_info,
        "readiness": readiness,
        "hrv_baseline": hrv_baseline,
        "ivg": ivg,
        "working_weights": weights,
        "exercise_plan": exercise_plan,
        "snapshot": snapshot,
        "previous_session_flags": previous_flags,
        "trend_digest": trend_digest,
        "reasoning_trace": [],
    }


def run_post_session(session_data: dict, target_date: date) -> dict:
    """
    Run the full post-session pipeline. Persists data and validates.

    Steps:
    1. Save session log to Supabase (deterministic)
    2. Post-workout analysis (deterministic)
    3. OVG validation (deterministic)
    """
    # Step 1: Save
    save_result = save_session_log(session_data)

    # Step 2: Post-workout analysis
    apple_health = session_data.get("apple_health")
    snapshot = session_data.get("snapshot", {})
    pwa = analyze_post_workout(
        session_date=target_date.isoformat(),
        apple_health=apple_health,
        session_exercises=session_data.get("actual_exercises", []),
        overall_rpe=session_data.get("overall_rpe"),
        morning_hrv=snapshot.get("hrv_ms"),
    )

    # Step 3: Validate
    weights = get_working_weights()
    ovg = run_ovg(session_data, target_date, weights.get("weights", {}))

    return {
        "save_result": save_result,
        "post_workout_analysis": pwa,
        "ovg": ovg,
    }


# --- CLI for local testing ---
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

    today = date.today()

    # Example snapshot
    test_snapshot = {
        "hrv_ms": 52,
        "rhr_bpm": 51,
        "rhr_7day_avg": 53,
        "sleep_hours": 7,
        "energy": 6,
        "symptom_load": 1,
        "cycle_day": 26,
        "soreness": {"lower": 0, "upper": 0, "core": 0},
        "equipment": "home_gym",
    }

    print("=== PRE-SESSION PIPELINE ===")
    result = run_pre_session(today, test_snapshot)
    print(json.dumps(result, indent=2, default=str))
