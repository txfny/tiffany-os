"""
Input Validation Gate — checks data completeness before starting a new session.
Queries Supabase first, then falls back to local session backups if Supabase is
unavailable.
"""

import os
from datetime import date, timedelta
from typing import Optional, Tuple
from .supabase_client import get_client
from .weekly_template import DAY_NAMES


def get_week_start(d: date) -> date:
    """Return Monday of the week containing date d."""
    return d - timedelta(days=d.weekday())


def _get_default_sessions_dir() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "sessions")
    )


def _prior_week_dates(target_date: date) -> Tuple[Optional[date], Optional[date]]:
    week_start = get_week_start(target_date)
    week_end = target_date - timedelta(days=1)  # don't check today
    if week_end < week_start:
        return None, None
    return week_start, week_end


def _build_result(target_date: date, logged_dates: set[str], source: str, error: Optional[str] = None) -> dict:
    week_start, week_end = _prior_week_dates(target_date)
    if week_start is None or week_end is None:
        result = {
            "status": "clear",
            "gaps": [],
            "summary": "First day of the week — no prior days to check.",
            "source": source,
        }
        if error:
            result["source_error"] = error
        return result

    gaps = []
    current = week_start
    while current <= week_end:
        day_str = current.isoformat()
        weekday = current.weekday()
        day_name = DAY_NAMES[weekday]

        if day_str not in logged_dates:
            gaps.append({
                "date": day_str,
                "day": day_name,
                "issue": "no_session_logged",
            })

        current += timedelta(days=1)

    if gaps:
        gap_days = ", ".join(f"{g['day']} {g['date']}" for g in gaps)
        result = {
            "status": "gaps_found",
            "gaps": gaps,
            "summary": f"Missing session data for: {gap_days}. Resolve before proceeding.",
            "source": source,
        }
    else:
        result = {
            "status": "clear",
            "gaps": [],
            "summary": "All prior days this week have logged sessions.",
            "source": source,
        }

    if error:
        result["source_error"] = error
    return result


def _run_ivg_supabase(target_date: date) -> dict:
    client = get_client()
    week_start, week_end = _prior_week_dates(target_date)
    if week_start is None or week_end is None:
        return _build_result(target_date, set(), "supabase")

    result = client.table("logs").select("created_at, session_type, overall_rpe").gte(
        "created_at", week_start.isoformat()
    ).lte(
        "created_at", week_end.isoformat() + "T23:59:59"
    ).execute()

    logged_dates = set()
    for row in result.data:
        log_date = row["created_at"][:10]  # extract YYYY-MM-DD
        logged_dates.add(log_date)

    return _build_result(target_date, logged_dates, "supabase")


def _run_ivg_local(target_date: date, sessions_dir: str, error: Optional[str] = None) -> dict:
    week_start, week_end = _prior_week_dates(target_date)
    if week_start is None or week_end is None:
        return _build_result(target_date, set(), "local_files", error)

    if not os.path.isdir(sessions_dir):
        return {
            "status": "gaps_found",
            "gaps": [{
                "date": week_start.isoformat(),
                "day": DAY_NAMES[week_start.weekday()],
                "issue": "ivg_source_unavailable",
            }],
            "summary": "IVG could not query Supabase and local session backups were not found.",
            "source": "unavailable",
            "source_error": error,
        }

    logged_dates = set()
    current = week_start
    while current <= week_end:
        day_str = current.isoformat()
        if os.path.exists(os.path.join(sessions_dir, f"{day_str}-session.json")):
            logged_dates.add(day_str)
        current += timedelta(days=1)

    return _build_result(target_date, logged_dates, "local_files", error)


def run_ivg(target_date: date, sessions_dir: Optional[str] = None) -> dict:
    """
    Check all days from Monday to (target_date - 1) for data gaps.
    Returns: { status: "clear" | "gaps_found", gaps: [...], summary: str }
    """
    sessions_dir = sessions_dir or _get_default_sessions_dir()
    try:
        return _run_ivg_supabase(target_date)
    except Exception as exc:
        return _run_ivg_local(target_date, sessions_dir, str(exc))
