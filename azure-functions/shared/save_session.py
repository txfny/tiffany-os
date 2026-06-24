"""
Save session — writes session data to Supabase.
Deterministic persistence. No relying on Claude to remember.
"""

from datetime import date
from .supabase_client import get_client


def save_snapshot(snapshot: dict) -> dict:
    """Save a daily snapshot to Supabase."""
    client = get_client()
    result = client.table("snapshots").upsert({
        "date": snapshot["date"],
        "hrv_ms": snapshot.get("hrv_ms"),
        "rhr_bpm": snapshot.get("rhr_bpm"),
        "sleep_hours": snapshot.get("sleep_hours"),
        "energy": snapshot.get("energy"),
        "mood": snapshot.get("mood"),
        "cycle_day": snapshot.get("cycle_day"),
        "symptom_load": snapshot.get("symptom_load"),
        "soreness_lower": snapshot.get("soreness", {}).get("lower", 0),
        "soreness_upper": snapshot.get("soreness", {}).get("upper", 0),
        "soreness_core": snapshot.get("soreness", {}).get("core", 0),
        "breath_location": snapshot.get("breath_location"),
        "equipment": snapshot.get("equipment"),
        "notes": snapshot.get("notes"),
    }, on_conflict="date").execute()

    return {"saved": True, "table": "snapshots", "date": snapshot["date"]}


def save_session_log(session: dict) -> dict:
    """Save a completed session log to Supabase."""
    client = get_client()

    # Insert into logs table
    log_result = client.table("logs").insert({
        "session_type": session.get("session_type"),
        "overall_rpe": session.get("overall_rpe"),
        "energy_after": session.get("energy_after"),
        "prediction_accuracy": session.get("prediction_accuracy"),
        "notes": session.get("notes"),
        "readiness_tier": session.get("readiness_tier"),
    }).execute()

    log_id = log_result.data[0]["id"] if log_result.data else None

    # Insert exercise history
    exercises_saved = 0
    for ex in session.get("exercises", []):
        client.table("exercise_history").insert({
            "log_id": log_id,
            "date": session["date"],
            "exercise_name": ex["name"],
            "target_area": ex.get("target_area"),
            "prescribed_sets": ex.get("prescribed_sets"),
            "prescribed_reps": ex.get("prescribed_reps"),
            "prescribed_load": ex.get("prescribed_load"),
            "sets_completed": ex.get("sets_completed"),
            "reps_completed": ex.get("reps_completed"),
            "load_used": ex.get("load_used"),
            "actual_rpe": ex.get("actual_rpe"),
            "skipped": ex.get("skipped", False),
            "notes": ex.get("notes"),
        }).execute()
        exercises_saved += 1

    return {
        "saved": True,
        "log_id": log_id,
        "exercises_saved": exercises_saved,
        "date": session["date"],
    }
