"""
Apple Health payload normalization.

Accepts a small payload from an iOS Shortcut or manual export and turns it into
the apple_health block consumed by post_workout_analysis.py.
"""

from typing import Any, Dict, List, Optional


def _num(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> Optional[int]:
    number = _num(value)
    if number is None:
        return None
    return int(round(number))


def _assessment(hrr_delta: Optional[int]) -> str:
    if hrr_delta is None:
        return "n/a"
    if hrr_delta >= 20:
        return "good"
    if hrr_delta >= 12:
        return "watch"
    return "flag"


def _segment_key(segment: Dict[str, Any], index: int) -> str:
    raw = str(
        segment.get("key")
        or segment.get("name")
        or segment.get("activity")
        or segment.get("type")
        or f"workout_{index + 1}"
    ).lower()
    normalized = []
    previous_underscore = False
    for char in raw:
        if char.isalnum():
            normalized.append(char)
            previous_underscore = False
        elif not previous_underscore:
            normalized.append("_")
            previous_underscore = True
    key = "".join(normalized).strip("_")
    return key or f"workout_{index + 1}"


def _get_first(segment: Dict[str, Any], names: List[str]) -> Any:
    for name in names:
        if name in segment:
            return segment[name]
    return None


def normalize_apple_health_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      {
        "workouts": [
          {
            "name": "strength",
            "duration_min": 35,
            "active_kcal": 160,
            "avg_hr": 130,
            "peak_hr": 170,
            "hr_at_stop": 150,
            "hr_1min_post": 125
          }
        ]
      }

    Output:
      {
        "strength": {
          "duration_min": 35,
          "calories": 160,
          "avg_hr": 130,
          "peak_hr": 170,
          "hr_at_stop": 150,
          "hr_1min_post": 125,
          "hrr_delta": 25,
          "hrr_assessment": "good"
        },
        "total_duration_min": 35,
        "total_calories": 160
      }
    """
    workouts = payload.get("workouts") or payload.get("segments") or []
    if isinstance(workouts, dict):
        workouts = list(workouts.values())
    if not isinstance(workouts, list):
        raise ValueError("Expected 'workouts' or 'segments' to be a list")

    normalized: Dict[str, Any] = {}
    total_duration = 0.0
    total_calories = 0.0
    hr_values = []
    peak_values = []

    for index, segment in enumerate(workouts):
        if not isinstance(segment, dict):
            continue

        key = _segment_key(segment, index)
        duration = _num(_get_first(segment, ["duration_min", "duration_minutes", "duration"]))
        calories = _num(_get_first(segment, ["calories", "active_kcal", "active_calories", "active_energy"]))
        avg_hr = _int(_get_first(segment, ["avg_hr", "hr_avg", "average_hr", "average_heart_rate"]))
        peak_hr = _int(_get_first(segment, ["peak_hr", "hr_peak", "max_hr", "maximum_heart_rate"]))
        hr_at_stop = _int(_get_first(segment, ["hr_at_stop", "hr_at_end", "end_hr"]))
        hr_1min = _int(_get_first(segment, ["hr_1min_post", "hr_1min_recovery", "hr_after_1min"]))

        block: Dict[str, Any] = {}
        if segment.get("start"):
            block["start"] = segment["start"]
        if segment.get("end"):
            block["end"] = segment["end"]
        if duration is not None:
            block["duration_min"] = round(duration, 2)
            total_duration += duration
        if calories is not None:
            block["calories"] = round(calories, 1)
            total_calories += calories
        if avg_hr is not None:
            block["avg_hr"] = avg_hr
            hr_values.append(avg_hr)
        if peak_hr is not None:
            block["peak_hr"] = peak_hr
            peak_values.append(peak_hr)
        if hr_at_stop is not None:
            block["hr_at_stop"] = hr_at_stop
        if hr_1min is not None:
            block["hr_1min_post"] = hr_1min

        explicit_hrr = _int(_get_first(segment, ["hrr_delta", "hrr_1min", "hrr_60s"]))
        hrr_delta = explicit_hrr
        if hrr_delta is None and hr_at_stop is not None and hr_1min is not None:
            hrr_delta = hr_at_stop - hr_1min
        if hrr_delta is not None:
            block["hrr_delta"] = hrr_delta
            block["hrr_assessment"] = _assessment(hrr_delta)

        if block:
            normalized[key] = block

    if total_duration > 0:
        normalized["total_duration_min"] = round(total_duration, 2)
    if total_calories > 0:
        normalized["total_calories"] = round(total_calories, 1)

    payload_duration = _num(_get_first(payload, ["total_duration_min", "duration_min", "duration_minutes"]))
    payload_calories = _num(_get_first(payload, ["total_calories", "total_active_kcal", "active_kcal", "calories"]))
    payload_avg_hr = _int(_get_first(payload, ["avg_hr", "hr_avg", "average_hr", "average_heart_rate"]))
    payload_peak_hr = _int(_get_first(payload, ["peak_hr", "hr_peak", "max_hr", "maximum_heart_rate"]))
    payload_hr_at_stop = _int(_get_first(payload, ["hr_at_stop", "hr_at_end", "end_hr"]))
    payload_hr_1min = _int(_get_first(payload, ["hr_1min_post", "hr_1min_recovery", "hr_after_1min"]))
    payload_hrr = _int(_get_first(payload, ["hrr_delta", "hrr_1min", "hrr_60s"]))

    if payload_duration is not None:
        normalized["total_duration_min"] = round(payload_duration, 2)
    if payload_calories is not None:
        normalized["total_calories"] = round(payload_calories, 1)
    if payload_avg_hr is not None:
        normalized["avg_hr"] = payload_avg_hr
    elif hr_values:
        normalized["avg_hr"] = int(round(sum(hr_values) / len(hr_values)))
    if payload_peak_hr is not None:
        normalized["peak_hr"] = payload_peak_hr
    elif peak_values:
        normalized["peak_hr"] = max(peak_values)

    if payload_hr_at_stop is not None:
        normalized["hr_at_stop"] = payload_hr_at_stop
    if payload_hr_1min is not None:
        normalized["hr_1min_post"] = payload_hr_1min
    if payload_hrr is None and payload_hr_at_stop is not None and payload_hr_1min is not None:
        payload_hrr = payload_hr_at_stop - payload_hr_1min
    if payload_hrr is not None:
        normalized["hrr_delta"] = payload_hrr
        normalized["hrr_assessment"] = _assessment(payload_hrr)

    normalized["data_quality"] = payload.get(
        "data_quality",
        "Shortcut/manual Apple Health export; verify HRR if workout segments were not separated.",
    )

    return normalized
