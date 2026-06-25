#!/usr/bin/env python3
"""
fetch_reading.py — pulls RSS from every Substack in reading-list.json,
scores each post by topic-match + freshness, and bakes reading/reading-data.js.

Claude owns the vibe; this owns the data. Run it whenever the follow list
changes or you want fresh posts:  python3 my_room/fetch_reading.py

Stdlib only — no pip installs.
"""
import json, re, html, sys, os
import urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LIST_PATH = os.path.join(HERE, "reading-list.json")
OUT_PATH = os.path.join(HERE, "reading", "reading-data.js")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) reading-room/1.0"
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def feed_url(base):
    base = base.rstrip("/")
    return base if base.endswith("/feed") else base + "/feed"


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_dt(s):
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def text_of(item, tag, ns=None):
    el = item.find(tag, ns) if ns else item.find(tag)
    return el.text if el is not None and el.text else ""


def first_image(*chunks):
    for c in chunks:
        if not c:
            continue
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', c)
        if m:
            return m.group(1)
    return None


def score_post(title, summary, interests, dt, now):
    # Score on what the post is ABOUT (title + the opening summary), not the
    # full body — otherwise long essays win just by repeating a word. The title
    # counts double; each topic is capped so one keyword-stuffed post can't run away.
    title_l = title.lower()
    text_l = (title + " " + summary).lower()
    topic_hits = []
    topic_score = 0.0
    for topic, kws in interests.items():
        distinct = sum(1 for kw in kws if kw.lower() in text_l)
        in_title = any(kw.lower() in title_l for kw in kws)
        if distinct:
            t = min(distinct, 3) + (1.5 if in_title else 0)  # cap + title bonus
            topic_score += t
            topic_hits.append((topic, t))
    # best-matching topic becomes the post's tag
    top_topic = max(topic_hits, key=lambda t: t[1])[0] if topic_hits else None

    # freshness: full points if brand-new, decaying to ~0 by ~120d
    fresh = 0.0
    if dt:
        days = max(0.0, (now - dt).total_seconds() / 86400.0)
        fresh = max(0.0, 1.0 - days / 120.0)

    score = topic_score + fresh * 4.0
    return round(score, 3), top_topic, round(topic_score, 2)


def main():
    with open(LIST_PATH) as f:
        cfg = json.load(f)

    interests = cfg.get("interests", {})
    follows = list(cfg.get("follows", []))
    mine = cfg.get("mine") or {}
    if mine.get("url"):
        follows = [dict(mine, _mine=True)] + follows

    now = datetime.now(timezone.utc)
    posts = []
    sources = []
    errors = []

    for pub in follows:
        url = pub.get("url")
        if not url:
            continue
        name = pub.get("name") or url
        try:
            raw = fetch(feed_url(url))
            root = ET.fromstring(raw)
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue

        channel = root.find("channel")
        if channel is None:
            errors.append(f"{name}: no <channel>")
            continue

        chan_title = strip_html(text_of(channel, "title")) or name
        n_here = 0
        for item in channel.findall("item"):
            title = strip_html(text_of(item, "title"))
            link = text_of(item, "link").strip()
            if not title or not link:
                continue
            desc = text_of(item, "description")
            content = text_of(item, "content:encoded", NS)
            body_text = strip_html(content) or strip_html(desc)
            summary = body_text[:280].rstrip()
            if len(body_text) > 280:
                summary = summary.rsplit(" ", 1)[0] + "…"
            author = strip_html(text_of(item, "dc:creator", NS))
            dt = parse_dt(text_of(item, "pubDate"))
            words = len(body_text.split())
            read_min = max(1, round(words / 220)) if words else None
            img = first_image(content, desc)

            score, topic, topic_score = score_post(title, summary, interests, dt, now)
            posts.append({
                "title": title,
                "link": link,
                "summary": summary,
                "publication": chan_title,
                "author": author or None,
                "date": dt.isoformat() if dt else None,
                "date_label": dt.strftime("%b %-d, %Y") if dt else None,
                "read_min": read_min,
                "image": img,
                "topic": topic,
                "score": score,
                "is_mine": bool(pub.get("_mine")),
            })
            n_here += 1
            if n_here >= 25:
                break

        sources.append({"name": chan_title, "url": url, "count": n_here, "why": pub.get("why")})

    posts.sort(key=lambda p: (p["is_mine"], p["score"], p["date"] or ""), reverse=True)

    # the couple to greet her with: top-scored posts spanning different publications
    featured, seen_pub = [], set()
    for p in posts:
        if p["publication"] in seen_pub:
            continue
        featured.append(p["link"])
        seen_pub.add(p["publication"])
        if len(featured) >= 3:
            break

    # Diversify the shelf: keep it score-ranked but don't let one prolific blog
    # cluster — greedily skip a publication that already appeared in the last 2 slots.
    MAX_SHELF = 200
    pool = posts[:]  # already score-sorted
    diversified, recent = [], []
    while pool and len(diversified) < MAX_SHELF:
        pick_i = 0
        for i, p in enumerate(pool):
            if p["publication"] not in recent[-2:]:
                pick_i = i
                break
        p = pool.pop(pick_i)
        diversified.append(p)
        recent.append(p["publication"])
    posts = diversified

    topics = sorted({p["topic"] for p in posts if p["topic"]})

    out = {
        "generated": now.isoformat(),
        "generated_label": now.astimezone().strftime("%b %-d, %Y · %-I:%M %p"),
        "posts": posts,
        "sources": sources,
        "topics": topics,
        "featured": featured,
        "errors": errors,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write("// auto-generated by fetch_reading.py — do not hand-edit\n")
        f.write("window.READING = ")
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    print(f"✓ {len(posts)} posts from {len(sources)} sources → {os.path.relpath(OUT_PATH, HERE)}")
    if errors:
        print("  skipped:", "; ".join(errors))


if __name__ == "__main__":
    main()
