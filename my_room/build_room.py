#!/usr/bin/env python3
"""Regenerate my_room/room-data.js from Tiffany's latest real data.

This is the "adaptive" seam: the room reads room-data.js (a plain
<script src>, so it works on file:// with no server). Run this whenever
the day changes and the room updates on refresh.

    python3 my_room/build_room.py
"""
import json
import glob
import os
import re
import datetime
import subprocess

# the Apple Reminders list that literally names the goal
FEEL_HUMAN_LIST = "things i want to do again to feel human"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS = os.path.join(ROOT, "data", "sessions")
OUT = os.path.join(ROOT, "my_room", "room-data.js")

# --- cozy content (edit freely; later we can wire these to memory/reminders) ---
ARABIC_WORDS = [
    {"ar": "فراشة", "tr": "farāsha", "en": "butterfly"},
    {"ar": "حنين", "tr": "ḥaneen", "en": "tender longing for something past"},
    {"ar": "دفء", "tr": "dif'", "en": "warmth"},
    {"ar": "شغف", "tr": "shaghaf", "en": "passion / the spark"},
    {"ar": "نور", "tr": "noor", "en": "light"},
    {"ar": "هدوء", "tr": "hudū'", "en": "calm, stillness"},
]
TRAVEL_DREAMS = [
    "espresso in a tiny piazza, Italy ✈️",
    "table mountain at golden hour, Cape Town",
    "the train up to Machu Picchu",
    "chasing the northern lights, Iceland",
    "a quiet small town in Germany",
]


# Which section each known item belongs under. AppleScript can't recover the
# section->item mapping (notes are empty, list order is jumbled), so we keep it
# here. Anything not listed lands in "to sort" — edit freely as Tiffany corrects.
SECTION_OF = {
    "Caffe Paradiso": "local & fun",
    "suka sushi (restaurant)": "local & fun",
    "lexington candy shop to try original coke": "local & fun",
    "vintage bookstore (has maps\nmaybe buy)": "local & fun",
    "GO TO THIS PLACE": "local & fun",
    "make your own candle": "creative / mindful",
    "book a lymphatic drainage here": "creative / mindful",
    "fit in a massage": "creative / mindful",
    "get free entry on bday to qcny spa": "creative / mindful",
}


def _osascript(lines, timeout=20):
    cmd = ["osascript"]
    for ln in lines:
        cmd += ["-e", ln]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def pull_feel_human():
    """Pull open reminders (names) from the 'feel human' list via AppleScript,
    joined with a robust delimiter so commas/newlines inside an item don't split
    it. Returns [] if Reminders is unavailable/denied."""
    lines = [
        'set AppleScript\'s text item delimiters to "|||"',
        'tell application "Reminders" to set ns to name of '
        '(every reminder of list "%s" whose completed is false)' % FEEL_HUMAN_LIST,
        'return ns as string',
    ]
    try:
        out = _osascript(lines)
        if out.returncode != 0 or not out.stdout.strip():
            return []
        return [i.strip() for i in out.stdout.split("|||") if i.strip()]
    except Exception:
        return []


def build_someday():
    """Group the live 'feel human' list into its subsections.
    Returns (groups, ok). groups = [{title, items}], with empty sections kept
    (so the structure shows) and an extra 'to sort' bucket for unmapped items."""
    raw = pull_feel_human()
    if not raw:
        return [], False
    headers = [x for x in raw if x.rstrip().endswith(":")]
    items = [x for x in raw if not x.rstrip().endswith(":")]
    sections = [h.rstrip().rstrip(":").strip() for h in headers]

    buckets = {s: [] for s in sections}
    tosort = []
    for it in items:
        sec = SECTION_OF.get(it)
        (buckets[sec].append(it) if sec in buckets else tosort.append(it))

    groups = [{"title": s, "items": buckets[s]} for s in sections]
    if tosort:
        groups.append({"title": "to sort", "items": tosort})
    return groups, True


def latest_session():
    files = sorted(glob.glob(os.path.join(SESSIONS, "*-session.json")))
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)


def build_receipts(s):
    """Pull the day's wins from the session flags (the 🟢 ones) + HRV notes."""
    receipts = []
    for flag in s.get("flags", []):
        if flag.startswith("🟢"):
            receipts.append(flag[1:].strip())
    snap = s.get("snapshot", {})
    hrv = snap.get("hrv_ms")
    if hrv and hrv >= 100:
        receipts.append(f"HRV {hrv} — your body voting 'responsive,' loudly.")
    return receipts[:4]


# Receipts are written for Claude in coaching voice. Anything naming the
# food-loop / compensation / body-image / medical machinery is a clinical note,
# NOT wall decor. The long view's ethic: growth on display, never a wound.
# Those arcs live (carefully) in knowing.json instead.
_SENSITIVE = re.compile(
    r"compensat|trigger|munch|bloat|mirror|food|loop|purg|laxativ|undereat|"
    r"\bED\b|eating|disorder|\bfat\b|skinny|scale|\bcyst|\bGI\b|bladder|nausea|"
    r"rumination|"
    r"weigh(?:ed|ing|s)?\s*(?:myself|herself|in\b|\d)|"  # body-weight, NOT 'top weight'
    r"broke(?:n)?\s+(?:my\s+)?(?:body|me)\b|broken body",  # 'broke my body', NOT 'broken set'
    re.I,
)
_LINK = re.compile(r"\s*\(?[Ss]ee\s*\[\[[^\]]+\]\]\.?\)?|\[\[[^\]]+\]\]")


def _clean(text):
    """Strip internal memory-links and tidy whitespace for display."""
    return _LINK.sub("", str(text)).replace("  ", " ").strip()


def _rel_tag(text):
    """Best-effort tag for a receipt line so the long view can filter it."""
    t = text.lower()
    if any(k in t for k in ["hrv", "responsive", "bounce", "rhr"]):
        return "responsive"
    if any(k in t for k in ["chris", "weekend", "living", "regulation", "downshift",
                            "present", "walk", "audience", "steps", "social", "massage"]):
        return "alive"
    if re.search(r"\bsquat|pulldown|press|thrust|\blb\b|reps|confirmed|\bpr\b|"
                 r"build-reps|working weight|sets?\b", t):
        return "strength"
    return "growth"


def _fmt_update(upd):
    """Render a working-weight update as a readable line."""
    if isinstance(upd, dict):
        ex = str(upd.get("exercise", "")).replace("_", " ").strip()
        old, new = upd.get("old"), upd.get("new")
        if ex and old and new:
            return f"{ex}: {_clean(old)} → {_clean(new)}"
        return _clean(", ".join(f"{k} {v}" for k, v in upd.items() if v))
    return _clean(upd)


def build_longview():
    """Weave every session's wins + the curated 'knowing' into one growth
    timeline. Two threads: the receipts (data — strength PRs, HRV bounces, the
    green-flag wins) and the knowing (curated reframes, in our voice)."""
    moments = []
    files = sorted(glob.glob(os.path.join(SESSIONS, "*-session.json")))
    sessions_logged = 0
    for f in files:
        try:
            with open(f) as fh:
                s = json.load(fh)
        except Exception:
            continue
        date = s.get("date")
        if not date:
            continue
        sessions_logged += 1
        snap = s.get("snapshot") or {}

        # 🟢 receipts from the day's flags (skip clinical/coaching-voice notes)
        for flag in (s.get("flags") or []):
            if isinstance(flag, str) and flag.startswith("🟢"):
                line = flag[1:].strip()
                if _SENSITIVE.search(line):
                    continue  # coaching note, not wall material
                title = line.split(":")[0].strip().lower() if ":" in line else None
                body = _clean(line.split(":", 1)[1] if ":" in line else line)
                if body:
                    moments.append({"date": date, "kind": "receipt", "tag": _rel_tag(line),
                                    "title": title, "body": body})

        # strength PRs / working-weight updates
        for upd in (s.get("working_weight_updates") or []):
            body = _fmt_update(upd)
            if body and not _SENSITIVE.search(body):
                moments.append({"date": date, "kind": "strength", "tag": "strength",
                                "title": "stronger than last time", "body": body})

        # a loud, responsive body
        hrv = snap.get("hrv_ms")
        if isinstance(hrv, (int, float)) and hrv >= 110:
            moments.append({"date": date, "kind": "responsive", "tag": "responsive",
                            "title": "a responsive body",
                            "body": f"HRV {int(hrv)} — your nervous system voting 'i'm here, i answer.'"})

        # how you came in (the felt layer — flows in going forward)
        mc = s.get("morning_context")
        if mc:
            moments.append({"date": date, "kind": "context", "tag": "growth",
                            "title": "how you came in", "body": mc})

    # the knowing thread (curated)
    knowing_path = os.path.join(ROOT, "my_room", "longview", "knowing.json")
    try:
        with open(knowing_path) as fh:
            for e in json.load(fh).get("entries", []):
                moments.append({"date": e.get("date"), "kind": "knowing",
                                "tag": e.get("tag", "growth"), "title": e.get("title"),
                                "body": e.get("body")})
    except Exception:
        pass

    moments = [m for m in moments if m.get("date")]
    moments.sort(key=lambda m: m["date"], reverse=True)  # newest first

    hrvs = [ (s.get("snapshot") or {}).get("hrv_ms")
             for s in (_safe_load(f) for f in files) if s ]
    hrvs = [h for h in hrvs if isinstance(h, (int, float))]
    stats = {
        "sessions_logged": sessions_logged,
        "moments": len(moments),
        "hrv_low": int(min(hrvs)) if hrvs else None,
        "hrv_high": int(max(hrvs)) if hrvs else None,
        "since": files[0].split("/")[-1][:10] if files else None,
    }

    data = {"moments": moments, "stats": stats,
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds")}
    out = os.path.join(ROOT, "my_room", "longview", "longview-data.js")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write("// auto-generated by build_room.py — do not hand-edit\n")
        fh.write("window.LONGVIEW = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
    print(f"wrote {out}")
    print(f"  long view: {len(moments)} moments across {sessions_logged} sessions")


def _safe_load(f):
    try:
        with open(f) as fh:
            return json.load(fh)
    except Exception:
        return None


def build_working_weights():
    """Derive the CURRENT working weight per exercise from the session logs —
    the local source of truth. The deployed /working-weights endpoint reads a
    broken Supabase and silently returns stale defaults; this file does not.

    Current weight = the most recent of either a logged `load` or an explicit
    `working_weight_updates` entry. Newest wins; on a tie, the deliberate
    progression record wins. Writes data/working-weights.json."""
    current = {}  # exercise -> {"load", "as_of", "basis", "_rank"}
    SKIP = {"treadmill_warmup", "outdoor_walk", "zone2_treadmill_walk", "elliptical", "walk"}

    for f in sorted(glob.glob(os.path.join(SESSIONS, "*-session.json"))):
        s = _safe_load(f)
        if not s:
            continue
        date = s.get("date")
        if not date:
            continue

        # loads actually lifted that day (rank 0 — newest date wins)
        for e in (s.get("exercises") or s.get("actual_exercises") or []):
            if not isinstance(e, dict):
                continue
            name = e.get("name") or e.get("exercise")
            load = e.get("load") or e.get("weight")
            if not name or name in SKIP or not load:
                continue
            rank = (date, 0)
            if name not in current or rank >= current[name]["_rank"]:
                current[name] = {"load": _clean(load), "as_of": date, "basis": "logged", "_rank": rank}

        # explicit progression updates (rank 1 — beats a same-day logged load)
        for u in (s.get("working_weight_updates") or []):
            if not isinstance(u, dict):
                continue
            name, new = u.get("exercise"), u.get("new")
            if not name or not new:
                continue
            rank = (date, 1)
            if name not in current or rank >= current[name]["_rank"]:
                current[name] = {"load": _clean(new), "as_of": date,
                                 "basis": _clean(u.get("basis", "progression")), "_rank": rank}

    weights = {k: {"load": v["load"], "as_of": v["as_of"], "basis": v["basis"]}
               for k, v in sorted(current.items())}
    out = os.path.join(ROOT, "data", "working-weights.json")
    with open(out, "w") as fh:
        json.dump({
            "_note": "SOURCE OF TRUTH for working weights, derived from data/sessions/*.json. "
                     "The deployed /working-weights endpoint is UNRELIABLE (stale Supabase defaults) "
                     "— read THIS file instead. Regenerated by my_room/build_room.py on every session log.",
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "weights": weights,
        }, fh, ensure_ascii=False, indent=2)
    print(f"wrote {out}")
    print(f"  working weights: {len(weights)} exercises (latest from logs)")


def main():
    s = latest_session()
    if not s:
        data = {"empty": True}
    else:
        snap = s.get("snapshot", {})
        r = s.get("readiness", {})
        data = {
            "empty": False,
            "date": s.get("date"),
            "day": s.get("day_of_week"),
            "focus": s.get("focus"),
            "session_type": s.get("session_type"),
            "tier": r.get("tier"),
            "hrv": snap.get("hrv_ms"),
            "rhr": snap.get("rhr_bpm"),
            "sleep": snap.get("sleep_hours"),
            "life_context": s.get("life_context"),
            "receipts": build_receipts(s),
        }

    # "someday" comes from someday.json (imported from the Reminders PDF export —
    # the only source that captures the nested subtasks AppleScript can't see).
    # Re-export the list to PDF and ask Claude to re-import to sync.
    someday_path = os.path.join(ROOT, "my_room", "someday.json")
    try:
        with open(someday_path) as f:
            sd = json.load(f)
        data["someday_areas"] = sd.get("areas", [])
        data["someday_source"] = "reminders-list.pdf"
    except Exception:
        data["someday_areas"] = []
        data["someday_source"] = "someday.json missing"
    data["generated_at"] = datetime.datetime.now().isoformat(timespec="seconds")

    js = "// auto-generated by build_room.py — do not hand-edit\n"
    js += "window.ROOM = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    with open(OUT, "w") as f:
        f.write(js)
    print(f"wrote {OUT}")
    if not data["empty"]:
        print(f"  room reflects {data['date']} ({data['day']}) — {len(data['receipts'])} receipts")

    build_longview()
    build_working_weights()


if __name__ == "__main__":
    main()
