"""
Readiness computation — deterministic scoring from snapshot data.
Implements rules/readiness.yaml exactly. No interpretation.
"""

import json
import os
import glob as _glob
import statistics
from datetime import date, timedelta


# Cold start baselines (used only when < 14 days of data exist)
HRV_COLD_START_MEAN = 57.0
HRV_COLD_START_SD = 4.5
HRV_COLD_START_MIN_SD = 4.5  # floor so SD never collapses to near-zero
RHR_BASELINE_MEAN = 53.0


def compute_hrv_baseline(sessions_dir: str, target_date: date, window_days: int = 14) -> dict:
    """
    Compute rolling HRV baseline from session history.
    Returns { mean, sd, n, source } where source is 'rolling' or 'cold_start'.
    """
    hrv_values = []
    if not os.path.isdir(sessions_dir):
        return {"mean": HRV_COLD_START_MEAN, "sd": HRV_COLD_START_SD, "n": 0, "source": "cold_start"}
    for days_back in range(1, window_days + 1):
        check_date = target_date - timedelta(days=days_back)
        pattern = os.path.join(sessions_dir, f"{check_date.isoformat()}*.json")
        files = _glob.glob(pattern)
        for f in files:
            try:
                with open(f) as fh:
                    session = json.load(fh)
                hrv = (session.get("snapshot") or {}).get("hrv_ms")
                if hrv is not None:
                    hrv_values.append(hrv)
            except (json.JSONDecodeError, IOError):
                continue

    if len(hrv_values) >= 7:
        mean = statistics.mean(hrv_values)
        sd = statistics.pstdev(hrv_values)
        # Floor: SD can't go below cold start minimum to avoid over-sensitivity
        sd = max(sd, HRV_COLD_START_MIN_SD)
        return {"mean": round(mean, 1), "sd": round(sd, 1), "n": len(hrv_values), "source": "rolling"}
    else:
        return {"mean": HRV_COLD_START_MEAN, "sd": HRV_COLD_START_SD, "n": len(hrv_values), "source": "cold_start"}


def compute_readiness(snapshot: dict, previous_session_flags: list = None,
                      hrv_baseline: dict = None) -> dict:
    """
    Compute readiness tier from snapshot data.
    Returns: { tier, signals, reasoning, volume_adjustment, rpe_cap }

    Conflict resolution: lowest signal wins.
    """
    signals = {}

    # --- HRV baseline ---
    if hrv_baseline is None:
        hrv_baseline = {"mean": HRV_COLD_START_MEAN, "sd": HRV_COLD_START_SD, "n": 0, "source": "cold_start"}
    hrv_mean = hrv_baseline["mean"]
    hrv_sd_val = hrv_baseline["sd"]

    # --- HRV signal ---
    hrv = snapshot.get("hrv_ms")
    if hrv is not None:
        hrv_sd = (hrv - hrv_mean) / hrv_sd_val
        baseline_label = f"baseline {hrv_mean}ms, SD {hrv_sd_val}, {hrv_baseline['source']} n={hrv_baseline['n']}"
        if hrv_sd < -1.5:
            signals["hrv"] = {"tier": "LOW", "value": hrv, "sd": round(hrv_sd, 1),
                              "reason": f"HRV {hrv}ms is {abs(round(hrv_sd, 1))} SD below {baseline_label}"}
        elif hrv_sd < -0.5:
            signals["hrv"] = {"tier": "MODERATE", "value": hrv, "sd": round(hrv_sd, 1),
                              "reason": f"HRV {hrv}ms is {abs(round(hrv_sd, 1))} SD below {baseline_label}"}
        else:
            signals["hrv"] = {"tier": "HIGH", "value": hrv, "sd": round(hrv_sd, 1),
                              "reason": f"HRV {hrv}ms is at/above {baseline_label}"}

    # --- RHR signal ---
    rhr = snapshot.get("rhr_bpm")
    rhr_avg = snapshot.get("rhr_7day_avg", RHR_BASELINE_MEAN)
    if rhr is not None:
        rhr_delta = rhr - rhr_avg
        if rhr_delta > 8:
            signals["rhr"] = {"tier": "LOW", "value": rhr, "delta": rhr_delta,
                              "reason": f"RHR {rhr} is +{rhr_delta} above 7-day avg ({rhr_avg})"}
        elif rhr_delta > 3:
            signals["rhr"] = {"tier": "MODERATE", "value": rhr, "delta": rhr_delta,
                              "reason": f"RHR {rhr} is +{rhr_delta} above 7-day avg"}
        else:
            signals["rhr"] = {"tier": "HIGH", "value": rhr, "delta": rhr_delta,
                              "reason": f"RHR {rhr} is within normal range (delta {rhr_delta:+.0f})"}

    # --- Sleep signal ---
    sleep = snapshot.get("sleep_hours")
    if sleep is not None:
        if sleep < 5:
            signals["sleep"] = {"tier": "LOW", "value": sleep,
                                "reason": f"Sleep {sleep}hrs — below 5hr threshold"}
        elif sleep <= 7:
            signals["sleep"] = {"tier": "MODERATE", "value": sleep,
                                "reason": f"Sleep {sleep}hrs — suboptimal (5-7hr range)"}
        else:
            signals["sleep"] = {"tier": "HIGH", "value": sleep,
                                "reason": f"Sleep {sleep}hrs — good"}

    # --- Symptom load signal ---
    symptom_load = snapshot.get("symptom_load", 0)
    if symptom_load >= 8:
        signals["symptoms"] = {"tier": "LOW", "value": symptom_load,
                                "reason": f"Symptom load {symptom_load}/12 — high"}
    elif symptom_load >= 4:
        signals["symptoms"] = {"tier": "MODERATE", "value": symptom_load,
                                "reason": f"Symptom load {symptom_load}/12 — moderate"}
    else:
        signals["symptoms"] = {"tier": "HIGH", "value": symptom_load,
                                "reason": f"Symptom load {symptom_load}/12 — low"}

    # --- Subjective energy override ---
    energy = snapshot.get("energy")
    if energy is not None and energy <= 3:
        signals["energy_override"] = {"tier": "MODERATE", "value": energy,
                                       "reason": f"Subjective energy {energy}/10 — downgrade if otherwise HIGH"}

    # --- Previous session flags (post-workout analysis feedback) ---
    if previous_session_flags:
        high_flags = [f for f in previous_session_flags if f.get("severity") == "HIGH"]
        moderate_flags = [f for f in previous_session_flags if f.get("severity") == "MODERATE"]

        if high_flags:
            signals["previous_session"] = {
                "tier": "MODERATE",
                "value": len(high_flags),
                "reason": f"Yesterday's session raised {len(high_flags)} HIGH flag(s): "
                          + ", ".join(f["signal"] for f in high_flags),
            }
        elif len(moderate_flags) >= 2:
            signals["previous_session"] = {
                "tier": "MODERATE",
                "value": len(moderate_flags),
                "reason": f"Yesterday's session raised {len(moderate_flags)} MODERATE flags: "
                          + ", ".join(f["signal"] for f in moderate_flags),
            }

    # --- Conflict resolution: lowest signal wins ---
    tier_rank = {"LOW": 0, "MODERATE": 1, "HIGH": 2}

    if not signals:
        return {"tier": "MODERATE", "signals": {}, "reasoning": "Insufficient data — defaulting to MODERATE",
                "volume_adjustment": "reduce 20-30%", "rpe_cap": 7}

    # Post-workout flags can pull to MODERATE but never to LOW
    lowest_tier = min(signals.values(), key=lambda s: tier_rank[s["tier"]])["tier"]
    if lowest_tier == "LOW" and "previous_session" in signals:
        non_prev = {k: v for k, v in signals.items() if k != "previous_session"}
        if non_prev:
            lowest_tier_without_prev = min(non_prev.values(), key=lambda s: tier_rank[s["tier"]])["tier"]
            if lowest_tier_without_prev != "LOW":
                lowest_tier = lowest_tier_without_prev
    lowest_signal = [k for k, v in signals.items() if v["tier"] == lowest_tier]

    # --- Dietary context: fasting cap ---
    dietary = snapshot.get("dietary_context")
    if dietary and lowest_tier == "HIGH":
        lowest_tier = "MODERATE"
        signals["dietary"] = {
            "tier": "MODERATE",
            "value": dietary,
            "reason": f"Fasting ({dietary}) — capping at MODERATE. Maintain intensity, reduce volume.",
        }
        lowest_signal = ["dietary"]

    # Build output
    result = {
        "tier": lowest_tier,
        "signals": signals,
        "lowest_signal": lowest_signal,
        "reasoning": f"Tier {lowest_tier} — driven by: {', '.join(lowest_signal)}. Lowest signal wins.",
    }

    if lowest_tier == "LOW":
        result["volume_adjustment"] = "active recovery only"
        result["rpe_cap"] = None
        result["description"] = "Recovery only — walking, easy elliptical, no structured strength"
    elif lowest_tier == "MODERATE":
        result["volume_adjustment"] = "reduce 20-30%"
        result["rpe_cap"] = 7
        result["description"] = "Reduced volume, RPE cap 7, no PRs"
    else:  # HIGH
        result["volume_adjustment"] = "full programming"
        result["rpe_cap"] = 10
        result["description"] = "Full volume and intensity, progression attempts OK"

    return result
