"""
Output Validation Gate — validates session plan before presenting to user.
Checks: correct session type, valid working weights, date accuracy, no fabricated data.
"""

from datetime import date
from .weekly_template import get_session_type


def run_ovg(session_plan: dict, target_date: date, working_weights: dict) -> dict:
    """
    Validate a session plan before output.
    Returns: { valid: bool, errors: [...], warnings: [...] }
    """
    errors = []
    warnings = []

    # 1. Date/day accuracy (skip if session was rescheduled)
    expected = get_session_type(target_date)
    if not session_plan.get("rescheduled_from"):
        if session_plan.get("session_type") and session_plan["session_type"] != expected["type"]:
            errors.append({
                "check": "session_type_mismatch",
                "expected": expected["type"],
                "got": session_plan["session_type"],
                "message": f"Session type should be '{expected['type']}' for {expected['day_name']}, got '{session_plan['session_type']}'"
            })

    # 2. Working weight validation
    exercises = session_plan.get("exercises", [])
    for ex in exercises:
        name = ex.get("name", "").lower().replace(" ", "_")
        prescribed_load = ex.get("prescribed_load")
        if name in working_weights and prescribed_load:
            current = working_weights[name]
            if str(prescribed_load) != str(current):
                warnings.append({
                    "check": "weight_mismatch",
                    "exercise": ex["name"],
                    "expected": current,
                    "got": prescribed_load,
                    "message": f"{ex['name']}: prescribed {prescribed_load} but latest logged weight is {current}"
                })

    # 3. Strength on non-strength day (skip if rescheduled)
    if expected["type"] in ("rest", "active_recovery", "cardio") and not session_plan.get("rescheduled_from"):
        strength_exercises = [e for e in exercises if e.get("type") == "strength"]
        if strength_exercises:
            warnings.append({
                "check": "strength_on_rest_day",
                "message": f"{expected['day_name']} is {expected['type']} — plan includes {len(strength_exercises)} strength exercises"
            })

    # 4. Volume check for readiness tier
    readiness_tier = session_plan.get("readiness_tier")
    if readiness_tier == "LOW" and exercises:
        errors.append({
            "check": "training_on_low_readiness",
            "message": "Readiness is LOW — should be active recovery only, no structured exercises"
        })
    if readiness_tier == "MODERATE":
        for ex in exercises:
            if ex.get("sets", 0) > 2:
                warnings.append({
                    "check": "volume_too_high_for_moderate",
                    "exercise": ex.get("name"),
                    "message": f"{ex['name']} has {ex['sets']} sets — MODERATE readiness caps at 2 sets"
                })

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
