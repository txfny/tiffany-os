"""
Review Plan — deterministic audit of exercise selection against context.

Runs AFTER exercise-selection, BEFORE Claude presents the plan.
Flags mechanical mismatches that don't require reasoning:
- location/equipment conflicts
- bracing conflicts with symptom regions
- 48-hour muscle group overlap
- volume vs readiness tier
- weight mismatches

Claude handles: interpreting free-text symptoms, session type overrides,
picking from substitution options, communicating risk to user.
"""

import os
import json
import glob as _glob
from datetime import date, timedelta
from typing import Optional

from shared.exercise_selection import EXERCISES, LOCATION_EQUIPMENT, _normalize_exercise_name


# Map user-reported symptom regions to body_regions tags on exercises.
# Claude maps free-text symptoms to these keys before calling this endpoint.
SYMPTOM_REGION_MAP = {
    "abdomen": ["core", "abdomen", "lower_back"],
    "lower_back": ["lower_back", "core"],
    "knee": ["legs"],
    "shoulder": ["shoulders"],
    "wrist": ["arms"],
    "neck": ["shoulders", "core"],
    "hip": ["legs", "glutes", "core"],
    "ankle": ["legs"],
    "chest": ["chest"],
    "upper_back": ["back"],
}


def _get_recent_muscle_groups(sessions_dir: str, target_date: date, hours: int = 48) -> dict:
    """
    Look at sessions in the last `hours` hours and return muscle groups hit
    with their dates. Returns { "quads": "2026-04-01", "glutes": "2026-04-01", ... }
    """
    cutoff = target_date - timedelta(hours=hours)
    groups = {}

    if not os.path.isdir(sessions_dir):
        return groups

    for days_back in range(0, 3):  # check up to 3 days back
        check_date = target_date - timedelta(days=days_back)
        if check_date < cutoff:
            break
        # Skip today
        if check_date == target_date:
            continue

        pattern = os.path.join(sessions_dir, f"{check_date.isoformat()}*.json")
        files = _glob.glob(pattern)
        for f in files:
            try:
                with open(f) as fh:
                    session = json.load(fh)
                exercises = session.get("actual_exercises", session.get("exercises", []))
                for ex in exercises:
                    name = _normalize_exercise_name(ex.get("name", ""))
                    pool_entry = EXERCISES.get(name)
                    if pool_entry:
                        for target in pool_entry["targets"]:
                            if target not in groups:
                                groups[target] = check_date.isoformat()
            except (json.JSONDecodeError, IOError):
                continue

    return groups


def _check_location(exercise_name: str, location: str) -> Optional[dict]:
    """Check if exercise is available at the given location. Returns flag or None."""
    pool_entry = EXERCISES.get(exercise_name)
    if not pool_entry:
        return None

    available_equipment = LOCATION_EQUIPMENT.get(location, [])
    has_equipment = any(tag in available_equipment for tag in pool_entry["equipment"])

    if not has_equipment:
        return {
            "check": "location",
            "exercise": exercise_name,
            "status": "FLAG",
            "reason": f"{exercise_name} requires {pool_entry['equipment']} — not available at {location}",
            "equipment_needed": pool_entry["equipment"],
            "location": location,
        }
    return None


def _check_bracing(exercise_name: str, symptom_regions: list) -> Optional[dict]:
    """Check if exercise requires bracing and conflicts with symptom regions."""
    pool_entry = EXERCISES.get(exercise_name)
    if not pool_entry:
        return None

    if not pool_entry.get("requires_bracing", False):
        return None

    if not symptom_regions:
        return None

    # Expand symptom regions to body_region tags
    flagged_regions = set()
    for region in symptom_regions:
        flagged_regions.update(SYMPTOM_REGION_MAP.get(region, [region]))

    # Check overlap with exercise body regions
    exercise_regions = set(pool_entry.get("body_regions", []))
    overlap = exercise_regions & flagged_regions

    if overlap:
        return {
            "check": "bracing_conflict",
            "exercise": exercise_name,
            "status": "FLAG",
            "reason": f"{exercise_name} requires bracing and loads {', '.join(overlap)} — conflicts with reported symptoms in {', '.join(symptom_regions)}",
            "requires_bracing": True,
            "conflicting_regions": list(overlap),
            "symptom_regions": symptom_regions,
        }
    return None


def _check_48h_overlap(exercise_name: str, recent_groups: dict) -> Optional[dict]:
    """Check if exercise targets muscle groups hit in last 48 hours."""
    pool_entry = EXERCISES.get(exercise_name)
    if not pool_entry:
        return None

    overlaps = []
    for target in pool_entry["targets"]:
        if target in recent_groups:
            overlaps.append({"group": target, "last_hit": recent_groups[target]})

    if overlaps:
        return {
            "check": "48h_overlap",
            "exercise": exercise_name,
            "status": "FLAG",
            "reason": f"{exercise_name} targets {', '.join(o['group'] for o in overlaps)} — hit within 48h ({overlaps[0]['last_hit']})",
            "overlaps": overlaps,
        }
    return None


def _check_weight(exercise_name: str, prescribed_load: str, working_weights: dict) -> Optional[dict]:
    """Check if prescribed weight matches the working weights source of truth."""
    if not working_weights:
        return None

    canonical_weight = working_weights.get(exercise_name)
    if canonical_weight is None:
        return None

    # Normalize for comparison (strip whitespace, lowercase)
    prescribed_norm = str(prescribed_load).strip().lower()
    canonical_norm = str(canonical_weight).strip().lower()

    if prescribed_norm != canonical_norm and prescribed_norm not in ("assess", "check", "bodyweight"):
        return {
            "check": "weight_mismatch",
            "exercise": exercise_name,
            "status": "FLAG",
            "reason": f"{exercise_name}: prescribed '{prescribed_load}' but working weight is '{canonical_weight}'",
            "prescribed": prescribed_load,
            "canonical": canonical_weight,
        }
    return None


def _apply_volume_adjustment(exercises: list, readiness_tier: str) -> dict:
    """Return volume adjustment instructions based on readiness tier."""
    if readiness_tier == "LOW":
        return {
            "check": "volume",
            "status": "ADJUST",
            "tier": "LOW",
            "action": "no_strength",
            "reason": "Readiness LOW — no structured strength. Active recovery only.",
        }
    elif readiness_tier == "MODERATE":
        adjusted = []
        for ex in exercises:
            adjusted.append({
                "name": ex.get("name"),
                "original_sets": ex.get("sets", 3),
                "adjusted_sets": max(ex.get("sets", 3) - 1, 1),
                "rpe_cap": 7,
            })
        return {
            "check": "volume",
            "status": "ADJUST",
            "tier": "MODERATE",
            "action": "reduce",
            "reason": "Readiness MODERATE — sets reduced by 1, RPE cap 7, no progression.",
            "exercises": adjusted,
        }
    else:
        return {
            "check": "volume",
            "status": "PASS",
            "tier": "HIGH",
            "action": "full",
            "reason": "Readiness HIGH — full programming.",
        }


def _find_substitutions(flagged_exercise: str, location: str, already_in_plan: set) -> list:
    """Return valid substitution options for a flagged exercise at the given location."""
    pool_entry = EXERCISES.get(flagged_exercise)
    if not pool_entry:
        return []

    available_equipment = LOCATION_EQUIPMENT.get(location, [])
    options = []

    for sub_name in pool_entry.get("substitutions", []):
        sub_entry = EXERCISES.get(sub_name)
        if not sub_entry:
            continue
        if sub_name in already_in_plan:
            continue
        # Check equipment
        if any(tag in available_equipment for tag in sub_entry["equipment"]):
            options.append({
                "name": sub_name,
                "targets": sub_entry["targets"],
                "requires_bracing": sub_entry.get("requires_bracing", False),
                "body_regions": sub_entry.get("body_regions", []),
                "focus": sub_entry["focus"],
            })

    # Also look for same-target exercises at the location that aren't substitutions
    target_set = set(pool_entry["targets"])
    for name, ex in EXERCISES.items():
        if name == flagged_exercise or name in already_in_plan:
            continue
        if any({"name": name} == o or o.get("name") == name for o in options):
            continue
        if not any(tag in available_equipment for tag in ex["equipment"]):
            continue
        if set(ex["targets"]) & target_set:
            options.append({
                "name": name,
                "targets": ex["targets"],
                "requires_bracing": ex.get("requires_bracing", False),
                "body_regions": ex.get("body_regions", []),
                "focus": ex["focus"],
                "note": "same-target alternative (not a listed substitution)",
            })

    return options


def review_plan(
    exercise_plan: dict,
    readiness_tier: str,
    location: str,
    symptom_regions: list = None,
    working_weights: dict = None,
    target_date: date = None,
    sessions_dir: str = None,
) -> dict:
    """
    Deterministic audit of an exercise plan against context.

    Args:
        exercise_plan: output from /exercise-selection
        readiness_tier: "LOW", "MODERATE", or "HIGH"
        location: "home_gym" or "planet_fitness"
        symptom_regions: list of standardized body region keys (e.g., ["abdomen", "lower_back"])
        working_weights: dict from /working-weights
        target_date: today's date for 48h lookback
        sessions_dir: path to session JSON files

    Returns:
        Structured audit with flags, volume adjustments, and substitution options.
    """
    if target_date is None:
        target_date = date.today()

    if sessions_dir is None:
        sessions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "..", "data", "sessions")
        if not os.path.isdir(sessions_dir):
            sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "..", "data", "sessions")

    symptom_regions = symptom_regions or []

    # Get recent muscle group history for 48h check
    recent_groups = _get_recent_muscle_groups(sessions_dir, target_date)

    # Audit each exercise
    exercises = exercise_plan.get("exercises", [])
    core = exercise_plan.get("core", [])
    all_exercises = exercises + core

    exercise_flags = []
    plan_names = {ex.get("name") for ex in all_exercises}

    for ex in all_exercises:
        name = ex.get("name", "")
        ex_flags = []

        # Location check
        loc_flag = _check_location(name, location)
        if loc_flag:
            ex_flags.append(loc_flag)

        # Bracing check
        brace_flag = _check_bracing(name, symptom_regions)
        if brace_flag:
            ex_flags.append(brace_flag)

        # 48h overlap check
        overlap_flag = _check_48h_overlap(name, recent_groups)
        if overlap_flag:
            ex_flags.append(overlap_flag)

        # Weight check
        weight_flag = _check_weight(name, ex.get("load", ""), working_weights or {})
        if weight_flag:
            ex_flags.append(weight_flag)

        if ex_flags:
            # Find substitutions for flagged exercises
            subs = _find_substitutions(name, location, plan_names)
            exercise_flags.append({
                "exercise": name,
                "flags": ex_flags,
                "substitution_options": subs,
            })

    # Volume adjustment
    volume = _apply_volume_adjustment(all_exercises, readiness_tier)

    # Summary
    total_flags = sum(len(ef["flags"]) for ef in exercise_flags)
    flagged_exercises = [ef["exercise"] for ef in exercise_flags]
    bracing_conflicts = [ef["exercise"] for ef in exercise_flags
                         if any(f["check"] == "bracing_conflict" for f in ef["flags"])]
    location_conflicts = [ef["exercise"] for ef in exercise_flags
                          if any(f["check"] == "location" for f in ef["flags"])]

    # Build available alternatives: all exercises at this location that
    # are NOT in the original plan AND pass the same symptom/bracing checks.
    # This gives Claude the full pool to pick from when many exercises are removed.
    available_equipment = LOCATION_EQUIPMENT.get(location, [])
    available_alternatives = []
    for name, ex in EXERCISES.items():
        if name in plan_names:
            continue
        if not any(tag in available_equipment for tag in ex["equipment"]):
            continue
        # Run the same checks
        alt_flags = []
        brace_flag = _check_bracing(name, symptom_regions)
        if brace_flag:
            alt_flags.append("bracing_conflict")
        overlap_flag = _check_48h_overlap(name, recent_groups)
        if overlap_flag:
            alt_flags.append("48h_overlap")
        available_alternatives.append({
            "name": name,
            "targets": ex["targets"],
            "focus": ex["focus"],
            "category": ex["category"],
            "requires_bracing": ex.get("requires_bracing", False),
            "body_regions": ex.get("body_regions", []),
            "sets": ex["sets"],
            "reps": ex["reps"],
            "flags": alt_flags,
            "clear": len(alt_flags) == 0,
        })

    # Confidence
    if total_flags == 0:
        confidence = "HIGH"
        confidence_reason = "All exercises pass — tools and context align."
    elif total_flags <= 2:
        confidence = "MODERATE"
        confidence_reason = f"{total_flags} flag(s) found — minor adjustments needed."
    else:
        confidence = "LOW"
        confidence_reason = f"{total_flags} flags found — significant mismatches, consider session type change."

    return {
        "date": target_date.isoformat(),
        "readiness_tier": readiness_tier,
        "location": location,
        "symptom_regions": symptom_regions,
        "exercise_flags": exercise_flags,
        "available_alternatives": available_alternatives,
        "volume_adjustment": volume,
        "summary": {
            "total_flags": total_flags,
            "flagged_exercises": flagged_exercises,
            "bracing_conflicts": bracing_conflicts,
            "location_conflicts": location_conflicts,
            "exercises_clear": len(all_exercises) - len(flagged_exercises),
            "confidence": confidence,
            "confidence_reason": confidence_reason,
        },
        "recent_muscle_groups_48h": recent_groups,
    }
