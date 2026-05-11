"""
Exercise selection — deterministic rotation logic.
Picks exercises for today's session based on recent history.
Rotates accessories to prevent staleness. Keeps compound staples sticky.
"""

import os
import json
import glob
from datetime import date, timedelta


# ─── EXERCISE POOL ──────────────────────────────────────────────────────────
# Structured from rules/progression.yaml. Each exercise has:
# - targets: muscle groups
# - category: compound or accessory
# - focus: lower, upper, core
# - equipment: list of equipment tags
# - substitutions: list of exercise keys that can replace it
# - sequence_priority: lower = earlier in session

EXERCISES = {
    # Lower body
    "goblet_squat": {
        "targets": ["quads", "glutes", "core"],
        "category": "compound",
        "focus": "lower",
        "equipment": ["home_dumbbells", "planet_fitness_dumbbells"],
        "sets": 3, "reps": "10-12",
        "sequence_priority": 1,
        "substitutions": ["barbell_back_squat", "smith_machine_squat", "bodyweight_squat"],
        "requires_bracing": True,
        "body_regions": ["legs", "core", "lower_back"],
    },
    "sumo_squat": {
        "targets": ["adductors", "glutes", "quads"],
        "category": "compound",
        "focus": "lower",
        "equipment": ["home_dumbbells", "planet_fitness_dumbbells"],
        "sets": 3, "reps": "10-12",
        "sequence_priority": 2,
        "substitutions": ["wide_stance_goblet_squat", "cable_sumo_squat"],
        "requires_bracing": True,
        "body_regions": ["legs", "core"],
    },
    "romanian_deadlift": {
        "targets": ["hamstrings", "glutes", "lower_back"],
        "category": "compound",
        "focus": "lower",
        "equipment": ["home_dumbbells", "planet_fitness_dumbbells"],
        "sets": 3, "reps": "8-12",
        "sequence_priority": 2,
        "substitutions": ["single_leg_rdl", "good_mornings"],
        "requires_bracing": True,
        "body_regions": ["legs", "lower_back", "core"],
    },
    "hip_thrust": {
        "targets": ["glutes"],
        "category": "accessory",
        "focus": "lower",
        "equipment": ["home_dumbbells"],
        "sets": 3, "reps": "10-15",
        "sequence_priority": 3,
        "substitutions": ["glute_bridge", "bulgarian_split_squat", "cable_pull_through"],
        "requires_bracing": False,
        "body_regions": ["legs", "glutes"],
    },
    "leg_curl": {
        "targets": ["hamstrings"],
        "category": "accessory",
        "focus": "lower",
        "equipment": ["planet_fitness_machine"],
        "sets": 3, "reps": "10-15",
        "sequence_priority": 4,
        "substitutions": ["nordic_hamstring_curl", "slider_leg_curl"],
        "requires_bracing": False,
        "body_regions": ["legs"],
    },

    # Upper body
    "overhead_press": {
        "targets": ["shoulders", "triceps"],
        "category": "compound",
        "focus": "upper",
        "equipment": ["home_barbell"],
        "sets": 3, "reps": "8-10",
        "sequence_priority": 1,
        "substitutions": ["dumbbell_shoulder_press", "machine_shoulder_press"],
        "requires_bracing": True,
        "body_regions": ["shoulders", "arms", "core"],
    },
    "dumbbell_row": {
        "targets": ["back", "biceps"],
        "category": "compound",
        "focus": "upper",
        "equipment": ["home_dumbbells", "planet_fitness_dumbbells"],
        "sets": 3, "reps": "10-12",
        "sequence_priority": 2,
        "substitutions": ["cable_row", "inverted_row"],
        "requires_bracing": False,
        "body_regions": ["back", "arms"],
    },
    "lat_pulldown": {
        "targets": ["lats", "biceps"],
        "category": "compound",
        "focus": "upper",
        "equipment": ["home_machine", "planet_fitness_cable"],
        "sets": 3, "reps": "10-12",
        "sequence_priority": 1,
        "substitutions": ["pullup_negatives", "band_lat_pulldown"],
        "requires_bracing": False,
        "body_regions": ["back", "arms"],
    },
    "chest_press": {
        "targets": ["chest", "triceps"],
        "category": "compound",
        "focus": "upper",
        "equipment": ["home_machine", "home_dumbbells", "planet_fitness_machine"],
        "sets": 3, "reps": "8-12",
        "sequence_priority": 2,
        "substitutions": ["pushups", "dumbbell_bench_press"],
        "requires_bracing": False,
        "body_regions": ["chest", "arms"],
    },
    "seated_row": {
        "targets": ["back", "biceps"],
        "category": "compound",
        "focus": "upper",
        "equipment": ["home_machine", "home_dumbbells", "planet_fitness_machine"],
        "sets": 3, "reps": "10-12",
        "sequence_priority": 2,
        "substitutions": ["cable_row", "dumbbell_row"],
        "requires_bracing": False,
        "body_regions": ["back", "arms"],
    },
    "tricep_dip": {
        "targets": ["triceps"],
        "category": "accessory",
        "focus": "upper",
        "equipment": ["home_dumbbells", "planet_fitness_dip_station"],
        "sets": 3, "reps": "8-12",
        "sequence_priority": 3,
        "substitutions": ["bench_dip", "overhead_tricep_extension"],
        "requires_bracing": False,
        "body_regions": ["arms"],
    },
    "overhead_tricep_extension": {
        "targets": ["triceps"],
        "category": "accessory",
        "focus": "upper",
        "equipment": ["home_dumbbells"],
        "sets": 3, "reps": "10-15",
        "sequence_priority": 4,
        "substitutions": ["cable_pushdown", "tricep_dip"],
        "requires_bracing": False,
        "body_regions": ["arms"],
    },
    "cable_pushdown": {
        "targets": ["triceps"],
        "category": "accessory",
        "focus": "upper",
        "equipment": ["planet_fitness_cable"],
        "sets": 3, "reps": "12-15",
        "sequence_priority": 3,
        "substitutions": ["band_pushdown", "tricep_dip"],
        "requires_bracing": False,
        "body_regions": ["arms"],
    },

    # Core — tagged by slot for 11-line abs programming
    # Slots: "rectus" (groove depth), "oblique" (frame without widening), "tva" (flat/tight)
    "hanging_leg_raise": {
        "targets": ["lower_abs", "hip_flexors"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "rectus",
        "equipment": ["home_pull_up_bar"],
        "sets": 3, "reps": "10-12",
        "sequence_priority": 1,
        "substitutions": ["captains_chair_leg_raise", "lying_leg_raise"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
    "knee_raise": {
        "targets": ["lower_abs"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "rectus",
        "equipment": ["home_pull_up_bar"],
        "sets": 3, "reps": "5-10",
        "sequence_priority": 2,
        "substitutions": ["reverse_crunch"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
    "bicycle_crunch": {
        "targets": ["upper_abs", "lower_abs", "obliques"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "rectus",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "30-45 sec",
        "sequence_priority": 1,
        "substitutions": ["long_arm_crunch", "heel_touches"],
        "requires_bracing": False,
        "body_regions": ["core", "abdomen"],
    },
    "reverse_crunch": {
        "targets": ["lower_abs"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "rectus",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "10-15",
        "sequence_priority": 2,
        "substitutions": ["knee_raise", "lying_leg_raise"],
        "requires_bracing": False,
        "body_regions": ["core", "abdomen"],
    },
    "flutter_kicks": {
        "targets": ["lower_abs", "hip_flexors"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "rectus",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "30-45 sec",
        "sequence_priority": 3,
        "substitutions": ["scissor_kicks"],
        "requires_bracing": False,
        "body_regions": ["core", "abdomen"],
    },
    "dead_bug": {
        "targets": ["deep_core", "transverse_abdominis"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "tva",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "10 each side",
        "sequence_priority": 3,
        "substitutions": ["bird_dog"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
    "plank_hip_dip": {
        "targets": ["obliques"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "oblique",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "20 (10 each side)",
        "sequence_priority": 4,
        "substitutions": ["side_plank", "russian_twist"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
    "stomach_vacuum": {
        "targets": ["transverse_abdominis"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "tva",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "15 sec hold",
        "sequence_priority": 5,
        "substitutions": [],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
        "progression": "hold_time: 10s → 15s → 20s → 30s. Advance when 3x current hold feels easy.",
    },
    "cable_crunch": {
        "targets": ["upper_abs"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "rectus",
        "equipment": ["planet_fitness_cable"],
        "sets": 3, "reps": "12-15",
        "sequence_priority": 2,
        "substitutions": ["weighted_crunch"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
    # pallof_press: removed from oblique pool per Tiffany preference
    # (feedback_core_preference.md). Plank variations preferred over anti-rotation
    # work. Keeping the definition here for reference but `core_slot` set to None
    # so the selection logic won't pick it.
    "pallof_press": {
        "targets": ["obliques", "deep_core"],
        "category": "accessory",
        "focus": "core",
        "core_slot": None,
        "equipment": ["planet_fitness_cable", "home_pull_up_bar"],
        "sets": 3, "reps": "10 each side",
        "sequence_priority": 3,
        "substitutions": ["band_pallof_press"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
    "side_plank_hip_dip": {
        "targets": ["obliques"],
        "category": "accessory",
        "focus": "core",
        "core_slot": "oblique",
        "equipment": ["bodyweight"],
        "sets": 3, "reps": "10 each side",
        "sequence_priority": 4,
        "substitutions": ["plank_hip_dip"],
        "requires_bracing": True,
        "body_regions": ["core", "abdomen"],
    },
}

# Equipment available at each location
LOCATION_EQUIPMENT = {
    "home_gym": [
        "home_dumbbells", "home_barbell", "home_pull_up_bar",
        "home_bench_or_chair", "home_machine", "bodyweight",
    ],
    "planet_fitness": [
        "planet_fitness_dumbbells", "planet_fitness_cable",
        "planet_fitness_machine", "planet_fitness_dip_station",
        "bodyweight",
    ],
}

# How many consecutive same-focus sessions before rotation kicks in
ACCESSORY_ROTATION_THRESHOLD = 3
COMPOUND_ROTATION_THRESHOLD = 5  # compounds are stickier

# Name normalization: map session file exercise names to pool keys
NAME_MAP = {
    "goblet squat": "goblet_squat",
    "sumo squat": "sumo_squat",
    "romanian deadlift": "romanian_deadlift",
    "hip thrust": "hip_thrust",
    "overhead press": "overhead_press",
    "dumbbell row": "dumbbell_row",
    "lat pulldown": "lat_pulldown",
    "chest press": "chest_press",
    "seated row": "seated_row",
    "tricep dip": "tricep_dip",
    "overhead tricep extension": "overhead_tricep_extension",
    "overhead tricep extension (cable)": "overhead_tricep_extension",
    "cable pushdown": "cable_pushdown",
    "hanging leg raise": "hanging_leg_raise",
    "knee raise": "knee_raise",
    "dead bug": "dead_bug",
    "plank hip dip": "plank_hip_dip",
    "stomach vacuum": "stomach_vacuum",
    "cable crunch": "cable_crunch",
    "pallof press": "pallof_press",
    "leg curl": "leg_curl",
    "shoulder press (machine)": "overhead_press",
    "shoulder press": "overhead_press",
}


def _normalize_exercise_name(name: str) -> str:
    """Map a session file exercise name to a pool key."""
    return NAME_MAP.get(name.lower().strip(), name.lower().replace(" ", "_"))


def _normalize_focus(focus_str: str) -> str:
    """Map session focus strings to simplified tags."""
    f = focus_str.lower()
    if "lower" in f:
        return "lower"
    if "upper" in f:
        return "upper"
    if "full" in f:
        return "full_body"
    return "other"


def _get_recent_sessions(focus: str, sessions_dir: str, lookback: int = 6) -> list:
    """
    Read local session JSON files and return recent strength sessions
    matching the given focus type.
    """
    pattern = os.path.join(sessions_dir, "*.json")
    files = sorted(glob.glob(pattern), reverse=True)

    matching = []
    for f in files:
        with open(f) as fh:
            session = json.load(fh)

        session_type = session.get("session_type", "")
        if "strength" not in session_type.lower() and "strength" != session.get("session_type"):
            continue

        # Check focus match
        session_focus = session.get("focus", session_type)
        normalized = _normalize_focus(session_focus)

        # full_body sessions count for both lower and upper history
        if focus == "full_body" or normalized == focus or normalized == "full_body":
            exercises = []
            for ex in session.get("actual_exercises", session.get("exercises", [])):
                name = _normalize_exercise_name(ex.get("name", ""))
                if name in EXERCISES:
                    exercises.append(name)
            if exercises:
                matching.append({
                    "date": session.get("date"),
                    "focus": normalized,
                    "exercises": exercises,
                })

        if len(matching) >= lookback:
            break

    return matching


def _exercises_available_at(location: str) -> set:
    """Return exercise keys available at the given location."""
    available_equipment = LOCATION_EQUIPMENT.get(location, LOCATION_EQUIPMENT["home_gym"])
    result = set()
    for name, ex in EXERCISES.items():
        if any(tag in available_equipment for tag in ex["equipment"]):
            result.add(name)
    return result


def _exercises_for_focus(focus: str, available: set) -> dict:
    """Return exercises matching the focus type and available at location."""
    result = {}
    if focus == "lower":
        for name, ex in EXERCISES.items():
            if ex["focus"] == "lower" and name in available:
                result[name] = ex
    elif focus == "upper":
        for name, ex in EXERCISES.items():
            if ex["focus"] == "upper" and name in available:
                result[name] = ex
    elif focus == "full_body":
        # Pick a mix: 2-3 lower compounds + 1-2 upper compounds + accessories
        for name, ex in EXERCISES.items():
            if ex["focus"] in ("lower", "upper") and name in available:
                result[name] = ex
    return result


def _compute_staleness(exercise_name: str, recent_sessions: list) -> int:
    """Count consecutive recent sessions where this exercise appeared."""
    streak = 0
    for session in recent_sessions:
        if exercise_name in session["exercises"]:
            streak += 1
        else:
            break
    return streak


def _find_substitution(exercise_name: str, available: set, already_selected: set):
    """Find a valid substitution for an exercise at the current location."""
    ex = EXERCISES.get(exercise_name)
    if not ex:
        return None
    for sub in ex["substitutions"]:
        if sub in EXERCISES and sub in available and sub not in already_selected:
            return sub
    return None


def select_exercises(target_date: date, session_type: str, focus: str,
                     location: str, working_weights: dict = None) -> dict:
    """
    Deterministic exercise selection with rotation logic.

    Args:
        target_date: today's date
        session_type: "strength" (only type that gets exercise selection)
        focus: "lower", "upper", or "full_body"
        location: "home_gym" or "planet_fitness"
        working_weights: current weights dict from /working-weights

    Returns:
        Exercise list with rotation status, sequenced and ready for Claude.
    """
    if session_type != "strength":
        return {"exercises": [], "note": "Exercise selection only applies to strength sessions."}

    # Normalize focus
    focus = _normalize_focus(focus) if focus not in ("lower", "upper", "full_body") else focus

    # What's available at this location?
    available = _exercises_available_at(location)

    # Get candidate exercises for this focus
    candidates = _exercises_for_focus(focus, available)

    # Get recent session history
    sessions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "..", "data", "sessions")
    # Also check standard project root location
    if not os.path.isdir(sessions_dir):
        sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "data", "sessions")

    recent = _get_recent_sessions(focus, sessions_dir)

    # Build exercise list with rotation logic
    selected = []
    rotation_log = []
    selected_names = set()
    weights = working_weights or {}

    for name, ex in sorted(candidates.items(), key=lambda x: x[1]["sequence_priority"]):
        staleness = _compute_staleness(name, recent)
        threshold = COMPOUND_ROTATION_THRESHOLD if ex["category"] == "compound" else ACCESSORY_ROTATION_THRESHOLD

        if staleness >= threshold:
            # Try to rotate
            sub = _find_substitution(name, available, selected_names)
            if sub:
                rotation_log.append({
                    "original": name,
                    "replaced_with": sub,
                    "reason": f"appeared in {staleness} consecutive {focus} sessions",
                })
                sub_ex = EXERCISES[sub]
                selected_names.add(sub)
                selected.append({
                    "name": sub,
                    "targets": sub_ex["targets"],
                    "sets": sub_ex["sets"],
                    "reps": sub_ex["reps"],
                    "load": weights.get(sub, "assess"),
                    "sequence_priority": sub_ex["sequence_priority"],
                    "category": sub_ex["category"],
                    "rotation_status": "substituted",
                    "substituted_for": name,
                })
                continue

        # Keep the exercise
        selected_names.add(name)
        selected.append({
            "name": name,
            "targets": ex["targets"],
            "sets": ex["sets"],
            "reps": ex["reps"],
            "load": weights.get(name, "check"),
            "sequence_priority": ex["sequence_priority"],
            "category": ex["category"],
            "rotation_status": "keep",
            "substituted_for": None,
        })

    # For full_body, trim to 4 exercises (2 lower + 2 upper) — leaves room for core circuit
    if focus == "full_body":
        lower = [e for e in selected if EXERCISES.get(e["name"], {}).get("focus") == "lower"
                 or EXERCISES.get(e.get("substituted_for", ""), {}).get("focus") == "lower"]
        upper = [e for e in selected if EXERCISES.get(e["name"], {}).get("focus") == "upper"
                 or EXERCISES.get(e.get("substituted_for", ""), {}).get("focus") == "upper"]
        selected = lower[:2] + upper[:2]

    # Sort by sequence priority
    selected.sort(key=lambda x: x["sequence_priority"])

    # Core selection: pick 1 from each slot (rectus, oblique, tva)
    # Rotate within each slot using date-based index
    core_exercises = []
    core_available = {name: ex for name, ex in EXERCISES.items()
                      if ex["focus"] == "core" and name in available}

    # Group by slot
    slots = {"rectus": [], "oblique": [], "tva": []}
    for name, ex in sorted(core_available.items(), key=lambda x: x[1]["sequence_priority"]):
        slot = ex.get("core_slot")
        if slot in slots:
            slots[slot].append((name, ex))

    # User preference: side_plank_hip_dip for oblique slot when available
    oblique_preference = "side_plank_hip_dip"

    day_of_year = target_date.timetuple().tm_yday
    for slot, exercises in slots.items():
        if not exercises:
            continue
        if slot == "oblique" and any(n == oblique_preference for n, _ in exercises):
            pick_name, pick_ex = next((n, e) for n, e in exercises if n == oblique_preference)
        else:
            idx = day_of_year % len(exercises)
            pick_name, pick_ex = exercises[idx]
        core_exercises.append({
            "name": pick_name,
            "targets": pick_ex["targets"],
            "sets": pick_ex["sets"],
            "reps": pick_ex["reps"],
            "sequence_priority": pick_ex["sequence_priority"],
            "category": "core",
            "core_slot": slot,
            "rotation_status": "keep",
        })

    return {
        "date": target_date.isoformat(),
        "focus": focus,
        "location": location,
        "exercises": selected,
        "core": core_exercises,
        "rotation_log": rotation_log,
    }
