#!/usr/bin/env python3
"""
coach.py — LOCAL coach pipeline. Runs the whole deterministic pipeline against
local files. No cloud, no Supabase, no false cold-start baselines.

Replaces the Azure Functions pipeline. The reasoning logic still lives in
azure-functions/shared/*.py (pure functions); this wires it to local data and
reimplements the three Supabase-bound steps (working-weights, ivg, save-session)
as plain file operations.

Why this exists: the deployed Azure endpoints can't see the session history, so
readiness fell back to a cold_start HRV baseline (57) and threw false LOWs, and
save-session/ivg/working-weights 500'd on a schema mismatch. Local files are the
source of truth — so the pipeline runs where the data is.

Usage:
  python3 tools/coach.py session-type --date 2026-06-24
  python3 tools/coach.py readiness --hrv 34 --rhr 63 --rhr7 56 --sleep 7.5 --energy 4 --symptoms 1
  python3 tools/coach.py ivg --date 2026-06-24
  python3 tools/coach.py working-weights
  python3 tools/coach.py exercise-selection --date 2026-06-24 --focus "Lower body + core" --location home_gym
  python3 tools/coach.py review-plan --plan-file plan.json --tier MODERATE --location home_gym [--symptoms abdomen,knee]
  python3 tools/coach.py ovg --plan-file plan.json --date 2026-06-24
  python3 tools/coach.py pre-session --date 2026-06-24 --snapshot-file snap.json
  python3 tools/coach.py save-session --file data/sessions/2026-06-24-session.json
  python3 tools/coach.py post-workout --session-file data/sessions/2026-06-24-session.json

Every subcommand prints JSON to stdout.
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(REPO_ROOT, "data", "sessions")
WORKING_WEIGHTS_FILE = os.path.join(REPO_ROOT, "data", "working-weights.json")
SHARED_PARENT = os.path.join(REPO_ROOT, "azure-functions")

# Make `shared` importable as a package (review_plan does `from shared...`).
# We only ever import the PURE-logic modules; the Supabase-bound ones
# (ivg / working_weights / save_session) are reimplemented below, so the
# `supabase` package never needs to be installed.
if SHARED_PARENT not in sys.path:
    sys.path.insert(0, SHARED_PARENT)

from shared import readiness as _readiness          # noqa: E402
from shared import weekly_template as _template      # noqa: E402
from shared import exercise_selection as _selection   # noqa: E402
from shared import review_plan as _review             # noqa: E402
from shared import ovg as _ovg                         # noqa: E402
from shared import post_workout_analysis as _pwa       # noqa: E402


# ---------------------------------------------------------------------------
# Local reimplementations of the three Supabase-bound steps
# ---------------------------------------------------------------------------

def load_working_weights() -> dict:
    """Read data/working-weights.json (built by my_room/build_room.py).
    Returns BOTH the rich nested dict and a flat {name: 'load'} map the
    selection/review functions expect."""
    with open(WORKING_WEIGHTS_FILE) as fh:
        data = json.load(fh)
    nested = data.get("weights", {})
    flat = {name: rec.get("load") if isinstance(rec, dict) else rec
            for name, rec in nested.items()}
    return {"source": "data/working-weights.json",
            "generated_at": data.get("generated_at"),
            "weights": nested, "flat": flat}


def run_ivg_local(target_date: datetime.date) -> dict:
    """Gap check: every day Monday..yesterday should have a session file."""
    week_start = target_date - datetime.timedelta(days=target_date.weekday())
    week_end = target_date - datetime.timedelta(days=1)
    if week_end < week_start:
        return {"status": "clear", "gaps": [], "source": "local_files",
                "summary": "First day of the week — no prior days to check."}
    gaps = []
    current = week_start
    while current <= week_end:
        day_str = current.isoformat()
        if not glob.glob(os.path.join(SESSIONS_DIR, f"{day_str}*.json")):
            gaps.append({"date": day_str,
                         "day": _template.DAY_NAMES[current.weekday()],
                         "issue": "no_session_logged"})
        current += datetime.timedelta(days=1)
    if gaps:
        gap_days = ", ".join(f"{g['day']} {g['date']}" for g in gaps)
        return {"status": "gaps_found", "gaps": gaps, "source": "local_files",
                "summary": f"Missing session data for: {gap_days}. Resolve before proceeding."}
    return {"status": "clear", "gaps": [], "source": "local_files",
            "summary": "All prior days this week have logged sessions."}


def save_session_local(session_file: str) -> dict:
    """Validate the session JSON is parseable, then regenerate the room +
    working-weights. The local JSON file IS the persistence layer."""
    with open(session_file) as fh:
        session = json.load(fh)  # raises if malformed
    date_str = session.get("date", "?")
    build = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, "my_room", "build_room.py")],
        capture_output=True, text=True)
    return {
        "saved": True,
        "file": os.path.relpath(session_file, REPO_ROOT),
        "date": date_str,
        "session_type": session.get("session_type"),
        "build_room_ok": build.returncode == 0,
        "build_room_tail": build.stdout.strip().splitlines()[-3:] if build.stdout else [],
        "build_room_err": build.stderr.strip() or None,
    }


# ---------------------------------------------------------------------------
# Pure-logic wrappers
# ---------------------------------------------------------------------------

def load_previous_session_flags(target_date: datetime.date) -> list:
    """Post-workout flags from the most recent logged session in the last 3 days.
    Feeds readiness (can nudge toward MODERATE, never to LOW)."""
    for days_back in range(1, 4):
        check = target_date - datetime.timedelta(days=days_back)
        files = glob.glob(os.path.join(SESSIONS_DIR, f"{check.isoformat()}*.json"))
        if files:
            with open(files[0]) as fh:
                session = json.load(fh)
            flags = (session.get("post_workout_analysis") or {}).get("flags", [])
            if flags:
                return flags
    return []


def compute_readiness(snapshot: dict, target_date: datetime.date) -> dict:
    baseline = _readiness.compute_hrv_baseline(SESSIONS_DIR, target_date)
    prev_flags = load_previous_session_flags(target_date)
    result = _readiness.compute_readiness(
        snapshot, previous_session_flags=prev_flags, hrv_baseline=baseline)
    result["hrv_baseline"] = baseline
    return result


def select_exercises(target_date, session_type, focus, location):
    ww = load_working_weights()
    return _selection.select_exercises(
        target_date, session_type, focus, location, working_weights=ww["flat"])


def review_plan(plan, tier, location, symptom_regions, target_date):
    ww = load_working_weights()
    return _review.review_plan(
        plan, tier, location,
        symptom_regions=symptom_regions, working_weights=ww["flat"],
        target_date=target_date, sessions_dir=SESSIONS_DIR)


def run_ovg(plan, target_date):
    ww = load_working_weights()
    return _ovg.run_ovg(plan, target_date, ww["flat"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_date(s):
    return datetime.date.fromisoformat(s) if s else datetime.date.today()


def _emit(obj):
    print(json.dumps(obj, indent=2, default=str))


def _snapshot_from_args(args):
    return {
        "hrv_ms": args.hrv, "rhr_bpm": args.rhr,
        "rhr_7day_avg": args.rhr7 if args.rhr7 is not None else args.rhr,
        "sleep_hours": args.sleep, "energy": args.energy,
        "symptom_load": args.symptoms,
        "dietary_context": args.dietary,
    }


def main():
    p = argparse.ArgumentParser(description="Local coach pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("session-type"); s.add_argument("--date")

    s = sub.add_parser("readiness")
    s.add_argument("--date")
    s.add_argument("--hrv", type=float, required=True)
    s.add_argument("--rhr", type=int, required=True)
    s.add_argument("--rhr7", type=int, default=None)
    s.add_argument("--sleep", type=float, required=True)
    s.add_argument("--energy", type=int, default=None)
    s.add_argument("--symptoms", type=int, default=0)
    s.add_argument("--dietary", default=None)

    s = sub.add_parser("ivg"); s.add_argument("--date")
    sub.add_parser("working-weights")

    s = sub.add_parser("exercise-selection")
    s.add_argument("--date")
    s.add_argument("--session-type", default="strength")
    s.add_argument("--focus", required=True)
    s.add_argument("--location", default="home_gym")

    s = sub.add_parser("review-plan")
    s.add_argument("--plan-file", required=True)
    s.add_argument("--tier", required=True)
    s.add_argument("--location", default="home_gym")
    s.add_argument("--symptoms", default="")
    s.add_argument("--date")

    s = sub.add_parser("ovg")
    s.add_argument("--plan-file", required=True)
    s.add_argument("--date")

    s = sub.add_parser("pre-session")
    s.add_argument("--date")
    s.add_argument("--snapshot-file", required=True)

    s = sub.add_parser("save-session"); s.add_argument("--file", required=True)

    s = sub.add_parser("post-workout")
    s.add_argument("--session-file", required=True)

    args = p.parse_args()

    if args.cmd == "session-type":
        _emit(_template.get_session_type(_parse_date(args.date)))

    elif args.cmd == "readiness":
        td = _parse_date(args.date)
        _emit(compute_readiness(_snapshot_from_args(args), td))

    elif args.cmd == "ivg":
        _emit(run_ivg_local(_parse_date(args.date)))

    elif args.cmd == "working-weights":
        _emit(load_working_weights())

    elif args.cmd == "exercise-selection":
        _emit(select_exercises(_parse_date(args.date), args.session_type,
                               args.focus, args.location))

    elif args.cmd == "review-plan":
        with open(args.plan_file) as fh:
            plan = json.load(fh)
        regions = [x.strip() for x in args.symptoms.split(",") if x.strip()]
        _emit(review_plan(plan, args.tier, args.location, regions, _parse_date(args.date)))

    elif args.cmd == "ovg":
        with open(args.plan_file) as fh:
            plan = json.load(fh)
        _emit(run_ovg(plan, _parse_date(args.date)))

    elif args.cmd == "pre-session":
        td = _parse_date(args.date)
        with open(args.snapshot_file) as fh:
            snap = json.load(fh)
        scheduled = _template.get_session_type(td)
        readiness = compute_readiness(snap, td)
        # Missed-strength rescheduling needs the tier first (Wed/Thu can absorb).
        session_type, reschedule_info = _template.resolve_session_type(
            td, SESSIONS_DIR, readiness["tier"])
        out = {"date": td.isoformat(),
               "session_type": session_type,
               "scheduled_type": scheduled["type"],
               "scheduled_focus": scheduled["focus"],
               "reschedule_info": reschedule_info,
               "readiness": readiness,
               "ivg": run_ivg_local(td),
               "working_weights": load_working_weights()}
        if session_type.get("type") == "strength":
            loc = snap.get("equipment", session_type.get("location", "home_gym"))
            sel = select_exercises(td, "strength", session_type.get("focus", ""), loc)
            out["exercise_selection"] = sel
            out["review_plan"] = review_plan(
                sel, readiness["tier"], loc, [], td)
        _emit(out)

    elif args.cmd == "save-session":
        _emit(save_session_local(args.file))

    elif args.cmd == "post-workout":
        with open(args.session_file) as fh:
            sess = json.load(fh)
        _emit(_pwa.analyze_post_workout(
            sess["date"], sess.get("apple_health"),
            session_exercises=sess.get("exercises"),
            overall_rpe=sess.get("overall_rpe"),
            morning_hrv=(sess.get("snapshot") or {}).get("hrv_ms")))


if __name__ == "__main__":
    main()
