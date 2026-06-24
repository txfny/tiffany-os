"""
Trend brain — deterministic cross-session digest.
Reads recent session JSONs and returns structured patterns Claude can reason over.

Code owns the digest shape. Claude owns the narrative interpretation on top of it.
"""

import os
import json
import glob
import re
import statistics
from collections import Counter
from datetime import date, timedelta


def _get_sessions_dir():
    """Find the data/sessions directory."""
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "..", "data", "sessions")
    if os.path.isdir(d):
        return d
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "data", "sessions")


def _load_window_sessions(sessions_dir, target_date, lookback_days):
    """Load session JSONs within the lookback window, newest first."""
    if not os.path.isdir(sessions_dir):
        return []

    cutoff = (target_date - timedelta(days=lookback_days)).isoformat()
    end = target_date.isoformat()

    pattern = os.path.join(sessions_dir, "*.json")
    files = sorted(glob.glob(pattern), reverse=True)

    sessions = []
    for f in files:
        try:
            with open(f) as fh:
                session = json.load(fh)
        except (json.JSONDecodeError, IOError):
            continue
        d = session.get("date", "")
        if not d:
            continue
        if d > end:
            continue
        if d < cutoff:
            break
        sessions.append(session)
    return sessions


def _extract_flag_title(flag_text):
    """Extract a normalized title from a flag string.

    Flag strings look like:
      "🟢 PELVIC-FLOOR / BREATH-LED CORE LANDED: Stomach vacuum..."
      "📌 SLEEP PATTERN: 6hr sleep two days in a row..."

    We strip emoji/leading symbols, take the part before the first colon,
    and uppercase it for bucketing.
    """
    if not isinstance(flag_text, str):
        return None
    # Strip leading non-letter characters (emojis, spaces, punctuation)
    stripped = re.sub(r"^[^A-Za-z]+", "", flag_text).strip()
    if not stripped:
        return None
    # Take part before first colon (the title)
    title = stripped.split(":", 1)[0].strip().upper()
    if len(title) < 3 or len(title) > 60:
        return None
    return title


def _tier_binding_signal(sessions):
    """Across sessions, find the most common 'lowest_signal' from readiness.

    Sessions store readiness as either a dict (with 'lowest_signal' list) or
    a string reason. We look at the dict shape only.
    """
    signals = []
    for s in sessions:
        r = s.get("readiness") or {}
        if not isinstance(r, dict):
            continue
        # Honor the structured lowest_signal field if present
        ls = r.get("lowest_signal")
        if isinstance(ls, list) and len(ls) == 1:
            # Single binding signal — interesting
            signals.append(ls[0])
        elif isinstance(ls, list) and len(ls) > 1:
            # All-tied = HIGH tier with no single binding signal
            continue
        else:
            # Fallback: parse "driven by: X" out of reasoning
            reason = r.get("reasoning", "")
            m = re.search(r"driven by:\s*([a-z_,\s]+)", reason)
            if m:
                parts = [p.strip() for p in m.group(1).split(",")]
                if len(parts) == 1:
                    signals.append(parts[0])

    if not signals:
        return None
    counter = Counter(signals)
    most_common, count = counter.most_common(1)[0]
    if count < 2:
        return None  # Not a pattern, just one occurrence
    return {"signal": most_common, "occurrences": count, "of_sessions": len(sessions)}


def _hrv_drift(sessions):
    """Compute HRV mean across first vs second half of the window.

    Sessions are newest-first. We split them in half by count, compute mean HRV
    of each half, and return the delta.
    """
    hrvs = []
    for s in sessions:
        snap = s.get("snapshot") or {}
        hrv = snap.get("hrv_ms")
        if isinstance(hrv, (int, float)):
            hrvs.append((s.get("date", ""), hrv))

    if len(hrvs) < 4:
        return None

    # Order chronologically (oldest first) for "then" vs "now"
    hrvs.sort(key=lambda x: x[0])
    half = len(hrvs) // 2
    then_vals = [v for _, v in hrvs[:half]]
    now_vals = [v for _, v in hrvs[half:]]

    then_mean = round(statistics.mean(then_vals), 1)
    now_mean = round(statistics.mean(now_vals), 1)
    delta = now_mean - then_mean
    delta_pct = round(delta / then_mean * 100, 1) if then_mean else 0.0

    return {
        "baseline_then": then_mean,
        "baseline_now": now_mean,
        "delta_ms": round(delta, 1),
        "delta_pct": delta_pct,
        "n_then": len(then_vals),
        "n_now": len(now_vals),
    }


def _rpe_trend(sessions):
    """List of overall_rpe values, chronological. None entries kept as null."""
    by_date = sorted(
        [(s.get("date", ""), s.get("overall_rpe")) for s in sessions],
        key=lambda x: x[0],
    )
    return [{"date": d, "rpe": r} for d, r in by_date]


def _recurring_flags(sessions, top_n=5):
    """Bucket flags across sessions by title, return top N with count."""
    titles = []
    for s in sessions:
        for flag in s.get("flags") or []:
            title = _extract_flag_title(flag)
            if title:
                titles.append(title)
    if not titles:
        return []
    counter = Counter(titles)
    return [
        {"title": title, "count": count}
        for title, count in counter.most_common(top_n)
        if count >= 2  # Only "recurring" if it appears 2+ times
    ]


def _readiness_tier_counts(sessions):
    """Count of sessions at each readiness tier."""
    counter = Counter()
    for s in sessions:
        r = s.get("readiness") or {}
        if not isinstance(r, dict):
            continue
        tier = r.get("tier")
        if tier:
            counter[tier] += 1
    return dict(counter)


def _recent_reasoning_decisions(sessions, limit=5):
    """Pull the most recent reasoning_trace entries across all sessions.

    Sessions are newest-first. We walk them in order, take all reasoning_trace
    entries, return the last `limit`.
    """
    out = []
    for s in sessions:
        trace = s.get("reasoning_trace") or []
        if not isinstance(trace, list):
            continue
        for entry in trace:
            if not isinstance(entry, dict):
                continue
            out.append({
                "date": s.get("date"),
                "layer": entry.get("layer"),
                "interpretation": entry.get("interpretation"),
                "decision": entry.get("decision"),
            })
            if len(out) >= limit:
                return out
    return out


def build_trend_digest(target_date, sessions_dir=None, lookback_days=10):
    """Build a structured digest of recent training patterns.

    Args:
        target_date: date object (the pre-session date)
        sessions_dir: optional override; defaults to data/sessions/
        lookback_days: how far back to look (default 10)

    Returns a dict with the shape documented in the plan file.
    """
    if sessions_dir is None:
        sessions_dir = _get_sessions_dir()

    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    sessions = _load_window_sessions(sessions_dir, target_date, lookback_days)

    if not sessions:
        return {
            "window": {
                "from": (target_date - timedelta(days=lookback_days)).isoformat(),
                "to": target_date.isoformat(),
                "n_sessions": 0,
            },
            "readiness_tier_counts": {},
            "rpe_trend": [],
            "recurring_flags": [],
            "tier_binding_signal": None,
            "recent_reasoning_decisions": [],
            "hrv_drift": None,
            "note": "No sessions in window — digest is empty.",
        }

    return {
        "window": {
            "from": (target_date - timedelta(days=lookback_days)).isoformat(),
            "to": target_date.isoformat(),
            "n_sessions": len(sessions),
        },
        "readiness_tier_counts": _readiness_tier_counts(sessions),
        "rpe_trend": _rpe_trend(sessions),
        "recurring_flags": _recurring_flags(sessions),
        "tier_binding_signal": _tier_binding_signal(sessions),
        "recent_reasoning_decisions": _recent_reasoning_decisions(sessions),
        "hrv_drift": _hrv_drift(sessions),
    }
