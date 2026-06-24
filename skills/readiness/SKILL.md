# Readiness Agent — v2
# Pure function: snapshot → readiness tier + reasoning.

---

## PURPOSE

Run the snapshot through `rules/readiness.yaml` and output a readiness tier (LOW / MODERATE / HIGH) with an explicit reasoning chain.

---

## INPUT

Validated snapshot from the Snapshot Agent.

Required: `hrv_ms`, `rhr_bpm` (or `rhr_delta`), `sleep_hours`.
Influential: `symptom_load`, `subjective_energy`.

---

## SCORING — INDIVIDUALIZED BASELINE MODEL

**HRV scoring uses the user's own rolling 14-day baseline, not fixed thresholds.**

1. The pipeline computes a rolling baseline from the last 14 days of session data (mean + SD). Falls back to cold start values (mean 57ms, SD 4.5ms) only if fewer than 7 days of data exist. SD has a floor of 4.5ms to prevent over-sensitivity.
2. Compare today's HRV to baseline:
   - **HIGH:** within 0.5 SD of mean or above
   - **MODERATE:** 0.5–1.5 SD below mean
   - **LOW:** > 1.5 SD below mean

**RHR and sleep use the same thresholds as v1** (already individualized via delta).

**Symptom load is a NEW signal:**
- 0–3: no impact
- 4–7: can downgrade to MODERATE
- 8–12: can downgrade to LOW

3. Apply conflict resolution: **lowest signal wins.**
4. Subjective energy override: can downgrade (energy ≤ 3 with HIGH → MODERATE), never upgrade.
5. **Dietary context:** if `dietary_context` is set in the snapshot (e.g., during a religious fast), readiness is capped at MODERATE even if all signals say HIGH. This reduces volume while maintaining intensity — critical for preserving muscle during protein restriction.

---

## OUTPUT

```
Readiness Assessment:
  HRV:         [X] ms | baseline: [mean] ± [SD] | [+/-X] SD → [tier]
  RHR delta:   [+X] bpm → [tier]
  Sleep:       [X] hrs → [tier]
  Symptoms:    [load] → [impact or "no impact"]
  Energy:      [X]/10 → [conflict flag if any]
  ─────────────────────
  → Final readiness: [LOW / MODERATE / HIGH]
  → What this means: [one sentence]
```

---

## NO PHASE-BASED MODIFICATION

On OC (Tyblume), there is no cycle phase intensity ceiling. Readiness tier is the ONLY intensity determinant. Pill pack day is logged for pattern detection but does not affect scoring.

---

## FALLBACK

If HRV is missing: score using RHR delta + sleep + symptom load + subjective energy. Note reduced confidence. The system still works — it's just less precise.
