"""
Working weights — fetches latest weights from Supabase exercise_history.
Single source of truth. No guessing.
"""

from .supabase_client import get_client


# Fallback weights if no history exists yet
DEFAULT_WEIGHTS = {
    "goblet_squat": "35 lb",
    "sumo_squat": "35 lb",
    "romanian_deadlift": "25 lb each",
    "hip_thrust": "50 lb",
    "overhead_press": "20 lb barbell",
    "shoulder_press": "DB press 15 lb each (no asymmetry detected Apr 7, ready to bump)",
    "lat_pulldown": "65 lb (locked Apr 30, consolidated May 7 — retest 70 next HIGH day)",
    "seated_row": "60 lb (failed at 65 on Apr 2)",
    "chest_press": "50 lb",
    "tricep_dip": "20 lb",
    "tricep_extension": "15 lb cable",
    "dumbbell_row": "20 lb each",
    "leg_press": "220 lb",
}


def get_working_weights() -> dict:
    """
    Fetch the latest working weight for each exercise from exercise_history.
    Falls back to defaults if no history exists.
    """
    client = get_client()

    try:
        # Get the most recent entry for each exercise
        result = client.table("exercise_history").select(
            "exercise_name, load_used, date, notes"
        ).order("date", desc=True).limit(100).execute()

        if not result.data:
            return {"source": "defaults", "weights": DEFAULT_WEIGHTS}

        # Group by exercise, take the most recent
        latest = {}
        for row in result.data:
            name = row["exercise_name"].lower().replace(" ", "_")
            if name not in latest:
                latest[name] = {
                    "load": row["load_used"],
                    "date": row["date"],
                    "notes": row.get("notes", ""),
                }

        # Merge with defaults for any missing exercises
        weights = {}
        for exercise, default_load in DEFAULT_WEIGHTS.items():
            if exercise in latest:
                weights[exercise] = latest[exercise]["load"]
            else:
                weights[exercise] = default_load

        return {"source": "exercise_history", "weights": weights, "raw": latest}

    except Exception as e:
        return {"source": "defaults", "weights": DEFAULT_WEIGHTS, "error": str(e)}
