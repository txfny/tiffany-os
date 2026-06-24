# Apple Health Shortcut Export

Goal: avoid relying on a chat connector for post-session metrics. The phone can send a small JSON payload, and the coach API normalizes it into the `apple_health` block used by post-workout analysis.

## Shortcut Output Payload

Send this shape to:

```text
https://gym-healthy-coach.azurewebsites.net/api/apple-health/normalize?code=<AZURE_FUNCTION_KEY>
```

Use `POST`, `Content-Type: application/json`.

## Manual Summary Payload

This is the easiest shape to fill from Apple Fitness/Health:

```json
{
  "date": "2026-05-12",
  "total_duration_min": 62,
  "total_active_kcal": 260,
  "avg_hr": 124,
  "peak_hr": 185,
  "hr_at_stop": 150,
  "hr_1min_post": 124
}
```

`hr_at_stop` and `hr_1min_post` are optional, but if both are present the API computes `hrr_delta` automatically.

Paste template:

```text
total_duration_min:
total_active_kcal:
avg_hr:
peak_hr:
hr_at_stop:
hr_1min_post:
```

## Segmented Payload

```json
{
  "date": "2026-05-12",
  "workouts": [
    {
      "name": "warmup",
      "duration_min": 10,
      "active_kcal": 25,
      "avg_hr": 112,
      "peak_hr": 121
    },
    {
      "name": "strength",
      "duration_min": 38,
      "active_kcal": 160,
      "avg_hr": 138,
      "peak_hr": 176
    },
    {
      "name": "core",
      "duration_min": 10,
      "active_kcal": 40,
      "avg_hr": 132,
      "peak_hr": 158,
      "hr_at_stop": 150,
      "hr_1min_post": 124
    },
    {
      "name": "treadmill_run",
      "duration_min": 4,
      "active_kcal": 35,
      "avg_hr": 145,
      "peak_hr": 165
    }
  ]
}
```

The normalizer computes:

- `total_duration_min`
- `total_calories`
- segment `calories`, `avg_hr`, `peak_hr`
- `hrr_delta` and `hrr_assessment` when `hr_at_stop` and `hr_1min_post` are present

## Local Test

```bash
python3 tools/normalize_apple_health.py payload.json
```

or:

```bash
cat payload.json | python3 tools/normalize_apple_health.py
```

## iOS Shortcut Recipe

Create a shortcut named `Send Workout Metrics`.

1. Add `Find Health Samples`.
2. Type: `Workouts`.
3. Filter: `Start Date is Today`.
4. Sort by `Start Date`, oldest first.
5. For each workout, collect:
   - workout type/name
   - start date
   - end date
   - duration
   - active energy
6. Add a second `Find Health Samples` action for `Heart Rate`.
7. Filter heart-rate samples between the workout start and end time.
8. Compute average HR and max HR for that segment.
9. For HRR, use the final segment:
   - `hr_at_stop`: nearest heart-rate sample at workout end
   - `hr_1min_post`: nearest heart-rate sample 60 seconds after workout end
10. Build the JSON dictionary above.
11. Add `Get Contents of URL`.
12. Method: `POST`.
13. Headers: `Content-Type: application/json`.
14. Request body: JSON.

If Shortcuts cannot access HRR cleanly, send `duration_min`, `active_kcal`, `avg_hr`, and `peak_hr` first. HRR can be added manually later without blocking the whole export.
