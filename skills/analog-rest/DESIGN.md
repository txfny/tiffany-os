# analog-rest — design notes (not yet implemented)

Work-in-progress design. Not a SKILL.md yet. Do not treat as live.

## Why this skill exists

Tiffany (Apr 21–22, 2026): feeling brain fog, work/AI thoughts looping, "ai ai ai" is the only thing that interests her right now. Wants to reclaim analog hobbies she used to enjoy — coloring, embroidery, things that use hands and attention without a screen. Sees this as a health issue, not a productivity issue.

## Design principles

**The skill's job is to end the conversation, not extend it.**

Using more AI to fix AI-dependency is a trap. This skill must be deliberately minimal. If it asks many questions, produces dashboards, or becomes another thing to engage with at length, it has failed on purpose.

## Proposed shape (awaiting approval)

- **Morning hook:** added to snapshot flow. One question: "What's one non-screen thing you'll do today?" She picks. No suggestions unless she asks.
- **Next-day check:** one question. "Did you do it?" yes/no/partial. No guilt, no streaks, no percentages.
- **Hobby library:** small list saved to memory. Starter entries: coloring, embroidery. Add as she mentions others. Surfaced only when she asks for a suggestion.
- **Weekly signal:** if last 7 days are mostly "no," flag the pattern once. Not as failure — as observation. No scoring system.

## What this skill must NOT do

- Track time/duration/minutes
- Optimize or rank hobbies
- Feed into readiness tier or workout planning
- Produce trends, charts, or dashboards
- Give mental-health advice or psychological framing
- Nutrition advice (hard boundary — ED history)

## Open questions before building

1. Is one-in / one-out the right scope, or too thin?
2. Should starter hobbies (coloring, embroidery) be saved to memory as a list she owns, and extended as she mentions more?
3. Where does the morning question live — inside the existing snapshot skill, or as a standalone prompt?

## Status

Paused 2026-04-22 to resume pipeline work (log Apr 20–21 sessions + today's snapshot). Return to this after.
