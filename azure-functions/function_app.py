"""
Azure Functions HTTP triggers for the coach pipeline.
Each endpoint is a deterministic tool that Claude can call.
"""

import azure.functions as func
import json
import os
from datetime import date, datetime

from shared.weekly_template import get_session_type
from shared.readiness import compute_readiness, compute_hrv_baseline
from shared.ivg import run_ivg
from shared.ovg import run_ovg
from shared.working_weights import get_working_weights
from shared.save_session import save_snapshot, save_session_log
from shared.exercise_selection import select_exercises
from shared.post_workout_analysis import analyze_post_workout
from shared.review_plan import review_plan
from shared.apple_health import normalize_apple_health_payload
from shared.trend_brain import build_trend_digest
from functions.coach_pipeline import run_pre_session, run_post_session

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="session-type")
def session_type(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/session-type?date=2026-03-26 → deterministic session type"""
    date_str = req.params.get("date", date.today().isoformat())
    target = date.fromisoformat(date_str)
    result = get_session_type(target)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="readiness", methods=["POST"])
def readiness(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/readiness { snapshot } → deterministic readiness tier"""
    snapshot = req.get_json()
    # Compute rolling baseline from session files when called standalone
    sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sessions")
    target_date = date.fromisoformat(snapshot.get("date", date.today().isoformat()))
    hrv_baseline = compute_hrv_baseline(sessions_dir, target_date) if os.path.isdir(sessions_dir) else None
    result = compute_readiness(snapshot, hrv_baseline=hrv_baseline)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="ivg")
def ivg(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/ivg?date=2026-03-26 → gap check for this week"""
    date_str = req.params.get("date", date.today().isoformat())
    target = date.fromisoformat(date_str)
    result = run_ivg(target)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="ovg", methods=["POST"])
def ovg(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/ovg { session_plan, date } → validate before output"""
    body = req.get_json()
    target = date.fromisoformat(body["date"])
    weights = get_working_weights()
    result = run_ovg(body.get("session_plan", {}), target, weights.get("weights", {}))
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="working-weights")
def working_weights(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/working-weights → latest weights from exercise_history"""
    result = get_working_weights()
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="exercise-selection", methods=["POST"])
def exercise_selection(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/exercise-selection { date, focus, location } → deterministic exercise pick"""
    body = req.get_json()
    target = date.fromisoformat(body["date"])
    weights_result = get_working_weights()
    result = select_exercises(
        target_date=target,
        session_type=body.get("session_type", "strength"),
        focus=body.get("focus", "lower"),
        location=body.get("location", "home_gym"),
        working_weights=weights_result.get("weights", {}),
    )
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="review-plan", methods=["POST"])
def review_plan_route(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/review-plan { exercise_plan, readiness_tier, location, symptom_regions?, date? }
    → deterministic audit of exercise plan against context"""
    body = req.get_json()
    target = date.fromisoformat(body.get("date", date.today().isoformat()))
    weights_result = get_working_weights()
    result = review_plan(
        exercise_plan=body["exercise_plan"],
        readiness_tier=body["readiness_tier"],
        location=body["location"],
        symptom_regions=body.get("symptom_regions", []),
        working_weights=weights_result.get("weights", {}),
        target_date=target,
    )
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="save-snapshot", methods=["POST"])
def snapshot_save(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/save-snapshot { snapshot } → persist to Supabase"""
    snapshot = req.get_json()
    result = save_snapshot(snapshot)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="save-session", methods=["POST"])
def session_save(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/save-session { session_data } → persist to Supabase"""
    body = req.get_json()
    result = save_session_log(body)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="pre-session", methods=["POST"])
def pre_session(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/pre-session { date, snapshot }
    → Full pre-session pipeline: session type + readiness + IVG + weights
    This is the main tool Claude calls before building a session plan.
    """
    body = req.get_json()
    target = date.fromisoformat(body["date"])
    snapshot = body["snapshot"]
    result = run_pre_session(target, snapshot)
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="post-workout-analysis", methods=["POST"])
def post_workout_analysis(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/post-workout-analysis { date, apple_health, exercises, overall_rpe, morning_hrv }"""
    body = req.get_json()
    result = analyze_post_workout(
        session_date=body["date"],
        apple_health=body.get("apple_health"),
        session_exercises=body.get("exercises", []),
        overall_rpe=body.get("overall_rpe"),
        morning_hrv=body.get("morning_hrv"),
    )
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="apple-health/normalize", methods=["POST"])
def apple_health_normalize(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/apple-health/normalize { workouts: [...] } → normalized apple_health block"""
    body = req.get_json()
    result = normalize_apple_health_payload(body)
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="trend-digest")
def trend_digest(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/trend-digest?date=YYYY-MM-DD&lookback=10
    → cross-session pattern digest: tier counts, recurring flags, HRV drift,
    binding signal mode, recent reasoning_trace entries."""
    date_str = req.params.get("date", date.today().isoformat())
    target = date.fromisoformat(date_str)
    try:
        lookback = int(req.params.get("lookback", "10"))
    except ValueError:
        lookback = 10
    result = build_trend_digest(target, lookback_days=lookback)
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="post-session", methods=["POST"])
def post_session(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/post-session { date, session_data }
    → Full post-session pipeline: save + OVG
    This is the main tool Claude calls after logging a session.
    """
    body = req.get_json()
    target = date.fromisoformat(body["date"])
    session_data = body["session_data"]
    result = run_post_session(session_data, target)
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")
