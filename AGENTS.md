# Coach Pipeline — Deterministic Tools

**Principle: Codex owns reasoning. Code owns data.**

Before building any session plan, you MUST call the deterministic tools. Do not guess session types, compute readiness in your head, or rely on conversation memory for working weights.

## Tool Endpoints

Base URL: `https://gym-healthy-coach.azurewebsites.net/api`
Auth: append `?code=<AZURE_FUNCTION_KEY>` to every request. Key is in `azure-functions/.env.keys` (gitignored).

### Pre-Session (call BEFORE planning)

| Endpoint | Method | Input | Returns |
|---|---|---|---|
| `/session-type?date=YYYY-MM-DD` | GET | date param | Day name, session type, focus, location, with_bf |
| `/readiness` | POST | `{ hrv_ms, rhr_bpm, rhr_7day_avg, sleep_hours, energy, symptom_load, dietary_context? }` | Tier (LOW/MODERATE/HIGH), signals, reasoning, volume_adjustment, rpe_cap. Uses rolling 14-day HRV baseline. If `dietary_context` is set (e.g. `"orthodox_lent"`), caps tier at MODERATE. |
| `/ivg?date=YYYY-MM-DD` | GET | date param | Gap check: status (clear/gaps_found), list of missing days |
| `/working-weights` | GET | none | Latest working weight per exercise from Supabase |
| `/exercise-selection` | POST | `{ date, session_type, focus, location }` | Exercise list with rotation logic, sets, reps, weights |
| `/review-plan` | POST | `{ exercise_plan, readiness_tier, location, symptom_regions?, date? }` | Audit: flags (location, bracing, 48h overlap, weight mismatch), volume adjustments, substitution options. Codex maps free-text symptoms to region keys before calling. |
| `/pre-session` | POST | `{ date, snapshot }` | All of the above in one call (includes exercise selection for strength days) |

### Post-Session (call AFTER logging)

| Endpoint | Method | Input | Returns |
|---|---|---|---|
| `/save-snapshot` | POST | snapshot object | Confirmation of Supabase write |
| `/save-session` | POST | session log object | Confirmation + exercise_history rows saved |
| `/post-workout-analysis` | POST | `{ date, apple_health, exercises, overall_rpe, morning_hrv }` | HRR trend, ACWR, session cost prediction, flags |
| `/ovg` | POST | `{ date, session_plan }` | Validation: errors and warnings |
| `/post-session` | POST | `{ date, session_data }` | Save + post-workout analysis + OVG in one call |

## Mandatory Pipeline Order

```
PRE-SESSION:
1. GET  /session-type        → know what today IS (non-negotiable)
2. POST /readiness           → compute tier from user's snapshot
3. GET  /ivg                 → check for data gaps this week
4. GET  /working-weights     → fetch current weights (don't guess)
5. POST /exercise-selection  → get today's exercises (rotation logic, strength days only)
6. POST /review-plan        → audit exercises against context (symptoms, location, 48h history)
7. [Codex reviews flags, picks substitutions if needed, builds session plan + justification]

POST-SESSION (after user reports what they did):
8. ASK  user to pull Apple Health data via Codex on their phone:
       "Open Codex on your phone and ask: 'Pull my workout data from today [DATE].
       I had [list sessions, e.g. elliptical AM, strength PM]. Give me duration,
       calories, avg HR, peak HR, and heart rate recovery for each.'"
       Wait for user to paste the results before proceeding.
9. ASK  energy after (1-5 or vibe), how they feel, any soreness
10. [Codex logs session WITH the biometrics included]
11. POST /save-session        → persist IMMEDIATELY after collecting metrics
12. POST /post-workout-analysis → HRR trends, workload ratio, session cost (runs automatically in /post-session)
13. POST /ovg                → validate everything before closing out
```

## Missed Session Rescheduling

The pipeline automatically detects missed strength sessions and reschedules them:
- If readiness was LOW on a strength day, the session JSON must include `scheduled_type` and `scheduled_focus` fields (what the template said) alongside `session_type` (what actually happened)
- Wednesday and Thursday can absorb missed strength focuses if readiness is MODERATE or HIGH
- Most recent miss wins (no doubling up). Debt expires at end of week.
- `reschedule_info` in the pre-session output tells you when this happened.

## Rules

- NEVER skip step 1. The session type is determined by code, not by you.
- NEVER prescribe a weight without checking /working-weights first.
- NEVER pick exercises without calling /exercise-selection first (strength days).
- NEVER present a session plan without calling /review-plan first (strength days). Map user symptoms to region keys: abdomen, lower_back, knee, shoulder, wrist, neck, hip, ankle, chest, upper_back.
- NEVER log a session without first collecting post-workout metrics (energy, Apple Health, HRR, how they feel).
- NEVER say a session is "logged" without calling /save-session.
- ALWAYS include `scheduled_type` and `scheduled_focus` in session JSONs (from the pipeline's `scheduled_type`/`scheduled_focus` output).
- If /ivg returns gaps, resolve them before proceeding.
- If /ovg returns errors, fix them before showing output to the user.

## Reference Files

- `rules/readiness.yaml` — readiness scoring logic (implemented in code)
- `rules/progression.yaml` — weekly template, exercise pool, progression model
- `rules/cycle-phase.yaml` — OC rules (no phase-based intensity ceilings)
- `research/citations.yaml` — research sources for justification step
- `skills/` — coaching skill definitions (snapshot, readiness, planner, logger)
- `data/sessions/` — session JSON files (backup, also in Supabase)
