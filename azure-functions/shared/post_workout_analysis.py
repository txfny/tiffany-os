"""
Post-workout analysis — crunches Apple Health data against session history.
Returns flags that feed into the next morning's readiness scoring.

Research backing:
- Cole 1999: HRR < 12 bpm is abnormal; declining HRR = overtraining signal
- Gabbett 2016: Acute:chronic workload ratio > 1.5 = injury risk
- Stanley 2013: Next-morning HRV drop > 15% = session was harder than expected
"""

import os
import json
import glob
from datetime import date, datetime, timedelta


# ─── SESSION FILE READING ───────────────────────────────────────────────────

def _get_sessions_dir():
    """Find the data/sessions directory."""
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "..", "data", "sessions")
    if os.path.isdir(d):
        return d
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "data", "sessions")


def _load_sessions(sessions_dir, days_back=56):
    """Load session JSON files from the last N days, newest first."""
    pattern = os.path.join(sessions_dir, "*.json")
    files = sorted(glob.glob(pattern), reverse=True)
    cutoff = (date.today() - timedelta(days=days_back)).isoformat()

    sessions = []
    for f in files:
        with open(f) as fh:
            session = json.load(fh)
        if session.get("date", "") < cutoff:
            break
        sessions.append(session)
    return sessions


# ─── HRR TREND ANALYSIS ────────────────────────────────────────────────────

def _extract_best_hrr(apple_health):
    """Extract the best HRR reading from today's Apple Health data.
    Best = from the activity with highest peak HR that has a valid hrr_delta.
    """
    if not apple_health:
        return None, None

    best_hrr = None
    best_activity = None
    best_peak = 0

    for key, data in apple_health.items():
        if not isinstance(data, dict):
            continue
        hrr = data.get("hrr_delta")
        if hrr is None or hrr == 0 or data.get("hrr_assessment") == "n/a":
            continue
        if isinstance(hrr, str):
            continue
        peak = data.get("peak_hr", 0)
        if peak > best_peak:
            best_peak = peak
            best_hrr = hrr
            best_activity = key

    return best_hrr, best_activity


def _get_historical_hrr(activity_type, sessions):
    """Get HRR readings from past sessions for the same activity type."""
    readings = []
    for session in sessions:
        ah = session.get("apple_health")
        if not ah or not isinstance(ah, dict):
            continue
        activity_data = ah.get(activity_type)
        if not activity_data or not isinstance(activity_data, dict):
            continue
        hrr = activity_data.get("hrr_delta")
        if hrr is None or hrr == 0 or activity_data.get("hrr_assessment") == "n/a":
            continue
        if isinstance(hrr, str):
            continue
        readings.append({
            "date": session.get("date"),
            "hrr": hrr,
        })
    return readings


def _compute_trend(values):
    """Simple linear trend. Returns slope direction."""
    n = len(values)
    if n < 3:
        return "insufficient_data", 0
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return "stable", 0
    slope = numerator / denominator
    if slope < -1.0:
        return "declining", slope
    elif slope > 1.0:
        return "improving", slope
    return "stable", slope


def _analyze_hrr(apple_health, sessions):
    """HRR trend analysis. Cole 1999."""
    today_hrr, activity_type = _extract_best_hrr(apple_health)

    if today_hrr is None:
        return {
            "today_hrr": None,
            "activity_type": None,
            "absolute_flag": False,
            "trend_flag": False,
            "trend_direction": "no_data",
            "data_points": 0,
            "note": "No valid HRR data in today's session.",
        }

    absolute_flag = today_hrr < 12
    historical = _get_historical_hrr(activity_type, sessions)
    hrr_values = [r["hrr"] for r in historical]

    if len(hrr_values) >= 3:
        # Include today's reading at the end for trend
        all_values = hrr_values[:6] + [today_hrr]
        # Reverse so oldest is first (readings come newest-first)
        all_values = list(reversed(all_values))
        direction, slope = _compute_trend(all_values)
        trend_flag = direction == "declining" and today_hrr < (sum(hrr_values) / len(hrr_values))
    else:
        direction = "insufficient_data"
        trend_flag = False

    note_parts = [f"HRR {today_hrr} bpm ({activity_type})."]
    if absolute_flag:
        note_parts.append("BELOW 12 bpm threshold (Cole 1999).")
    if trend_flag:
        note_parts.append(f"Declining trend across {len(hrr_values) + 1} readings.")
    elif direction == "insufficient_data":
        note_parts.append(f"Only {len(hrr_values)} historical readings, need 3+ for trend.")
    else:
        note_parts.append(f"Trend: {direction}.")

    return {
        "today_hrr": today_hrr,
        "activity_type": activity_type,
        "absolute_flag": absolute_flag,
        "trend_flag": trend_flag,
        "trend_direction": direction,
        "historical_hrr_values": [r["hrr"] for r in historical[:6]],
        "data_points": len(hrr_values) + 1,
        "note": " ".join(note_parts),
    }


# ─── ACUTE:CHRONIC WORKLOAD RATIO ──────────────────────────────────────────

def _get_session_load(session):
    """Extract session load. Primary: total_calories. Fallback: HR × duration proxy."""
    ah = session.get("apple_health")
    if ah and isinstance(ah, dict):
        cals = ah.get("total_calories")
        if cals and isinstance(cals, (int, float)) and cals > 0:
            return cals, "calories"
        # Fallback: sum activity calories
        total = 0
        for key, data in ah.items():
            if isinstance(data, dict) and "calories" in data:
                total += data.get("calories", 0)
        if total > 0:
            return total, "calories_summed"
        # Fallback: HR × duration proxy
        total_dur = ah.get("total_duration_min", 0)
        if total_dur > 0:
            # Find an avg HR
            hrs = [data.get("avg_hr", 0) for key, data in ah.items()
                   if isinstance(data, dict) and data.get("avg_hr")]
            if hrs:
                avg_hr = sum(hrs) / len(hrs)
                return avg_hr * total_dur / 100, "hr_duration_proxy"
    return None, "missing"


def _compute_acwr(apple_health, session_date, sessions):
    """Acute:chronic workload ratio. Gabbett 2016."""
    if isinstance(session_date, str):
        session_date = date.fromisoformat(session_date)

    # Get today's load
    today_load, today_method = None, "missing"
    if apple_health and isinstance(apple_health, dict):
        cals = apple_health.get("total_calories")
        if cals and isinstance(cals, (int, float)) and cals > 0:
            today_load, today_method = cals, "calories"
        else:
            total = sum(data.get("calories", 0) for key, data in apple_health.items()
                        if isinstance(data, dict) and "calories" in data)
            if total > 0:
                today_load, today_method = total, "calories_summed"

    # Get week boundaries (Mon-Sun)
    week_start = session_date - timedelta(days=session_date.weekday())
    week_end = week_start + timedelta(days=6)

    # Compute weekly loads for past 4 weeks + current
    weekly_loads = {}
    for session in sessions:
        s_date = date.fromisoformat(session["date"])
        s_week_start = s_date - timedelta(days=s_date.weekday())
        load, _ = _get_session_load(session)
        if load:
            week_key = s_week_start.isoformat()
            weekly_loads[week_key] = weekly_loads.get(week_key, 0) + load

    # Add today's load to current week
    current_week_key = week_start.isoformat()
    if today_load:
        weekly_loads[current_week_key] = weekly_loads.get(current_week_key, 0) + today_load

    # Acute = current week
    acute = weekly_loads.get(current_week_key, 0)

    # Chronic = average of previous 4 weeks (not including current)
    past_weeks = []
    for i in range(1, 5):
        pw_start = week_start - timedelta(weeks=i)
        pw_key = pw_start.isoformat()
        if pw_key in weekly_loads:
            past_weeks.append(weekly_loads[pw_key])

    if len(past_weeks) < 2:
        return {
            "today_load": today_load,
            "load_method": today_method,
            "acute_load": acute,
            "chronic_load": None,
            "acwr": None,
            "acwr_flag": False,
            "weeks_of_data": len(past_weeks),
            "confidence": "insufficient",
            "note": f"Only {len(past_weeks)} week(s) of historical data. Need 2+ for ACWR.",
        }

    chronic = sum(past_weeks) / len(past_weeks)
    acwr = acute / chronic if chronic > 0 else 0

    confidence = "high" if len(past_weeks) >= 4 else "moderate"

    return {
        "today_load": today_load,
        "load_method": today_method,
        "acute_load": round(acute),
        "chronic_load": round(chronic),
        "acwr": round(acwr, 2),
        "acwr_flag": acwr > 1.5,
        "weeks_of_data": len(past_weeks),
        "confidence": confidence,
        "note": f"ACWR {acwr:.2f} — {'ABOVE 1.5 threshold' if acwr > 1.5 else 'within safe range'}. {len(past_weeks)} weeks of data.",
    }


# ─── SESSION COST PREDICTION ───────────────────────────────────────────────

def _predict_session_cost(apple_health, overall_rpe, morning_hrv, sessions):
    """Predict next-morning HRV impact. Stanley 2013."""
    # Compute intensity score from available components
    components = {}
    if apple_health and isinstance(apple_health, dict):
        # Find max peak HR across activities
        peak_hrs = [data.get("peak_hr", 0) for key, data in apple_health.items()
                    if isinstance(data, dict) and data.get("peak_hr")]
        if peak_hrs:
            components["peak_hr"] = max(peak_hrs) / 200  # normalized to estimated max

        cals = apple_health.get("total_calories")
        if not cals:
            cals = sum(data.get("calories", 0) for key, data in apple_health.items()
                       if isinstance(data, dict) and "calories" in data)
        if cals and cals > 0:
            components["calories"] = min(cals / 500, 1.0)

        dur = apple_health.get("total_duration_min")
        if not dur:
            dur = sum(data.get("duration_min", 0) for key, data in apple_health.items()
                      if isinstance(data, dict) and "duration_min" in data)
        if dur and dur > 0:
            components["duration"] = min(dur / 90, 1.0)

    if overall_rpe and isinstance(overall_rpe, (int, float)):
        components["rpe"] = overall_rpe / 10

    if not components:
        return {
            "intensity_score": None,
            "components_available": [],
            "predicted_hrv_suppression": False,
            "confidence": "no_data",
            "note": "No intensity data available for session cost prediction.",
        }

    intensity_score = sum(components.values()) / len(components)

    # Look at historical sessions with next-morning data
    historical_costs = []
    for session in sessions:
        nmr = session.get("next_morning_recovery")
        snapshot = session.get("snapshot") or {}
        morning = snapshot.get("hrv_ms")
        if not nmr or not morning or not isinstance(nmr, dict):
            continue
        next_hrv = nmr.get("hrv_ms")
        if not next_hrv:
            continue
        change_pct = (next_hrv - morning) / morning * 100
        historical_costs.append({
            "date": session.get("date"),
            "morning_hrv": morning,
            "next_hrv": next_hrv,
            "change_pct": round(change_pct, 1),
        })

    predicted_suppression = False
    confidence = "low"

    if morning_hrv and len(historical_costs) >= 3:
        # Compare today's intensity to historical patterns
        suppressed = [h for h in historical_costs if h["change_pct"] < -15]
        if suppressed and intensity_score > 0.7:
            predicted_suppression = True
        confidence = "moderate" if len(historical_costs) >= 5 else "low"
    elif morning_hrv and intensity_score > 0.7:
        # Heuristic fallback: high intensity + HRV already below baseline
        HRV_BASELINE = 57.0
        if morning_hrv < HRV_BASELINE * 0.85:
            predicted_suppression = True
            confidence = "heuristic"

    threshold_15pct = round(morning_hrv * 0.85, 1) if morning_hrv else None

    return {
        "intensity_score": round(intensity_score, 2),
        "components_available": list(components.keys()),
        "predicted_hrv_suppression": predicted_suppression,
        "confidence": confidence,
        "morning_hrv": morning_hrv,
        "threshold_15pct": threshold_15pct,
        "historical_comparisons": len(historical_costs),
        "note": f"Intensity {intensity_score:.2f}. "
                + (f"Predicted >15% HRV drop (threshold: {threshold_15pct} ms). " if predicted_suppression
                   else "No predicted HRV suppression. ")
                + f"{len(historical_costs)} historical comparisons available.",
    }


# ─── MAIN FUNCTION ─────────────────────────────────────────────────────────

def analyze_post_workout(session_date, apple_health, session_exercises=None,
                         overall_rpe=None, morning_hrv=None):
    """
    Analyze post-workout data and return flags for readiness consumption.

    Args:
        session_date: ISO date string
        apple_health: Apple Health data block from session
        session_exercises: list of exercises performed
        overall_rpe: overall session RPE
        morning_hrv: this morning's HRV from snapshot

    Returns:
        dict with flags, analysis details, and data quality info
    """
    # Early return for no data
    if not apple_health:
        return {
            "date": session_date,
            "flags": [],
            "hrr_analysis": None,
            "workload_ratio": None,
            "session_cost_prediction": None,
            "data_quality": {"apple_health": "missing"},
            "note": "No Apple Health data — analysis skipped.",
        }

    sessions_dir = _get_sessions_dir()
    sessions = _load_sessions(sessions_dir)

    # Run analyses
    hrr = _analyze_hrr(apple_health, sessions)
    acwr = _compute_acwr(apple_health, session_date, sessions)
    cost = _predict_session_cost(apple_health, overall_rpe, morning_hrv, sessions)

    # Aggregate flags
    flags = []

    if hrr["absolute_flag"]:
        flags.append({
            "signal": "hrr_absolute",
            "severity": "HIGH",
            "source": "cole_1999",
            "detail": f"HRR {hrr['today_hrr']} bpm < 12 bpm threshold",
        })
    if hrr["trend_flag"]:
        flags.append({
            "signal": "hrr_trend",
            "severity": "MODERATE",
            "source": "cole_1999",
            "detail": f"HRR declining across {hrr['data_points']} {hrr['activity_type']} sessions",
        })

    if acwr.get("acwr_flag"):
        flags.append({
            "signal": "acwr_spike",
            "severity": "HIGH",
            "source": "gabbett_2016",
            "detail": f"ACWR {acwr['acwr']:.2f} > 1.5 threshold",
        })

    if cost.get("predicted_hrv_suppression"):
        flags.append({
            "signal": "session_cost_high",
            "severity": "MODERATE",
            "source": "stanley_2013",
            "detail": f"Predicted >15% HRV drop tomorrow (intensity: {cost['intensity_score']})",
        })

    # Data quality report
    data_quality = {
        "apple_health": "present",
        "hrr_available": hrr["today_hrr"] is not None,
        "acwr_confidence": acwr.get("confidence", "unknown"),
        "cost_confidence": cost.get("confidence", "unknown"),
    }

    return {
        "date": session_date,
        "flags": flags,
        "hrr_analysis": hrr,
        "workload_ratio": acwr,
        "session_cost_prediction": cost,
        "data_quality": data_quality,
    }
