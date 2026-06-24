# Self-Review Pass

Before showing the final session card to Tiffany, Claude runs one second-pass critique against its own draft. The goal is to catch sloppy reasoning, contradictions with recent patterns, and load decisions that don't actually follow from the readiness reasoning.

## When to run

- After the planner has drafted the session card
- BEFORE the card is shown to the user
- On every strength session. Optional on active-recovery / rest days (low value).

## How to run

Compose this prompt to yourself (no tool call needed — it's an internal pass):

> **You are reviewing the draft plan below as if you were a different coach.**
> Inputs available: the draft session card, the `reasoning_trace` so far, the `trend_digest` from /pre-session.
>
> Check three things:
> 1. **Internal consistency** — does the plan act on what the `readiness` reasoning said? If the trace says "sleep is the binding signal, volume should reduce 20-30%" but the plan keeps full volume, that's a contradiction.
> 2. **Pattern fit** — does the plan contradict any recurring flag from `trend_digest.recurring_flags`? E.g. if "RDL FORM HOLD" appears 3+ times, the plan must not prescribe RDL.
> 3. **Progression defensibility** — given the last 3 sessions of this focus (visible in `trend_digest.rpe_trend` and recent session JSONs), is the load progression defensible? Specifically: is the user attempting a PR on a day the readiness reasoning didn't greenlight? Is a working weight being held when the user is ready to bump?
>
> Return a JSON object:
> ```json
> {
>   "decision": "ship" | "revise",
>   "changes": [
>     {"target": "exercise_name | section", "change": "what to change", "why": "..."}
>   ],
>   "reasoning": "2-3 sentence summary of the critique"
> }
> ```

## What to do with the result

- If `decision == "ship"`: append the review result as `{layer: "self_review", ...}` to `reasoning_trace`, then present the card unchanged.
- If `decision == "revise"`: apply the changes, append the review result to `reasoning_trace`, then present the revised card. The fact that a revision happened goes in the card itself only if it materially changes what Tiffany is doing (e.g., dropped an exercise). Cosmetic changes don't need user-facing acknowledgment.

## Anti-patterns to avoid

- **Rubber-stamping.** If every self-review returns `ship` with `changes: []`, the pass is too soft. The critique prompt above is intentionally adversarial; honor that framing.
- **Bikeshedding.** Don't revise for stylistic preferences. Revise for substantive misfits with the trace or trend digest.
- **Double-counting.** The mechanical audit already runs in `/review-plan` (Step 6). This self-review is for the *judgment* layer — load decisions, progression calls, contradictions with stated reasoning. Don't re-do what `review_plan.py` already checked.

## Why this exists

Until now, the planner was single-shot: data → reasoning → card → user. The card was sometimes drifting from the readiness reasoning that produced it (e.g., "we should reduce volume on low sleep" → plan keeps full volume because Tiffany pushed back). The self-review catches that gap before it reaches her, so the drift becomes a visible decision rather than a silent one.
