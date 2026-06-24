# Review Plan — Post-Pipeline Reasoning Gate
# Runs AFTER deterministic tools, BEFORE presenting the plan to the user.

---

## PURPOSE

Review the deterministic pipeline output and decide whether the plan makes sense for today's actual context. Every adjustment must have an explicit reason. No vibes. No guessing.

This skill has two layers:
1. **Deterministic audit** (`/review-plan` endpoint) — mechanical checks that code handles: location conflicts, bracing vs symptoms, 48h muscle overlap, volume adjustments, weight mismatches. Returns flags + substitution options.
2. **Claude reasoning** — interprets the flags, maps free-text symptoms to region keys, decides session type overrides, picks from substitution options, communicates risk to user.

---

## WHEN TO INVOKE

After ALL pre-session tools have returned (session-type, readiness, IVG, working-weights, exercise-selection) and before presenting the session card to the user.

---

## STEP 1 — MAP SYMPTOMS TO REGIONS (Claude)

Before calling `/review-plan`, Claude must translate the user's reported symptoms into standardized region keys:

| Region key | User might say |
|---|---|
| `abdomen` | stomach pain, abdominal pain, cramping, bloating, stabbing in stomach |
| `lower_back` | low back, lumbar, back pain (lower) |
| `knee` | knee pain, knee clicking, knee swelling |
| `shoulder` | shoulder pain, rotator cuff, shoulder impingement |
| `wrist` | wrist pain, wrist strain |
| `neck` | neck pain, stiff neck, neck strain |
| `hip` | hip pain, hip flexor, hip tightness |
| `ankle` | ankle pain, ankle sprain |
| `chest` | chest pain, pec strain |
| `upper_back` | upper back, thoracic, between shoulder blades |

If unsure which region, include all plausible matches. Over-flagging is safer than under-flagging.

---

## STEP 2 — CALL /review-plan (Deterministic)

```
POST /review-plan
{
  "exercise_plan": <output from /exercise-selection>,
  "readiness_tier": "MODERATE",
  "location": "home_gym",
  "symptom_regions": ["abdomen"],
  "date": "2026-04-02"
}
```

The endpoint returns:
- **exercise_flags**: per-exercise flags with check type, reason, and substitution options
- **volume_adjustment**: set/RPE modifications based on readiness tier
- **summary**: total flags, confidence level, categorized conflicts
- **recent_muscle_groups_48h**: what was hit recently (for context)

---

## STEP 3 — REVIEW FLAGS AND DECIDE (Claude)

For each flagged exercise, Claude must:

1. **Read the flag reason** — understand what the mechanical check found
2. **Check substitution options** — the endpoint returns valid alternatives at the current location
3. **Decide: keep, substitute, or remove** — with explicit reasoning
4. **If substituting, verify** the substitute doesn't have the same flags (e.g., don't swap a bracing exercise for another bracing exercise when abdomen is flagged)

### Session Type Override (Claude only)
If the audit returns confidence LOW (many flags), Claude should consider:
- Is a different session type more appropriate? (e.g., full body → upper only)
- Present the reasoning to the user and let them decide

---

## STEP 4 — PRESENT THE REVIEWED PLAN

Output format:

```
Plan Review:
  Session type:     [PASS or ADJUST → what changed and why]
  Exercise check:
    [exercise 1]:   [PASS — from /review-plan] or [ADJUST → flag reason + chosen action]
    [exercise 2]:   ...
  Volume:           [from /review-plan volume_adjustment]
  Gaps:             [PASS or ADJUST → what was removed/substituted and why]
  Progression:      [PASS or ADJUST → reason]
  ─────────────────────
  Adjustments made: [count]
  Confidence: [from /review-plan summary]
```

Then build the session card from the reviewed exercises.

---

## WHAT CODE HANDLES vs WHAT CLAUDE HANDLES

| Check | Code (`/review-plan`) | Claude |
|---|---|---|
| Location/equipment match | Flags mismatches | — |
| Bracing vs symptom regions | Flags conflicts given region keys | Maps free-text → region keys |
| 48h muscle group overlap | Flags from session history | — |
| Volume adjustment | Computes set reduction per readiness | — |
| Weight validation | Flags mismatches vs /working-weights | — |
| Substitution options | Returns valid alternatives at location | Picks best fit for today |
| Session type override | — | Decides if session type should change |
| Risk communication | — | Explains flags to user |
| Symptom interpretation | — | Translates "stabbing stomach" → `["abdomen"]` |

---

## RULES

- **Every ADJUST must have a reason.** "Feels wrong" is not a reason.
- **Never silently drop exercises.** If you remove something, say what and why.
- **Never add exercises the tools didn't select** unless filling a gap from a removal — and state the substitution logic.
- **Never override working weights.** If the weight looks wrong, flag it for the user rather than changing it.
- **If more than 3 adjustments are needed,** the session plan may be fundamentally wrong for today. Consider whether a different session type is more appropriate and explain why.
- **Defer to the user on pain/symptoms.** Flag the concern, explain the risk, but don't refuse to program. The user decides.
- **This is a reasoning step, not a veto.** The goal is to catch mismatches between tool output and reality, not to second-guess the tools.
