#!/usr/bin/env python3
"""Build a backwards timeline so several dishes are ready at the same time.

Usage:
  python3 serving_schedule.py menu.json
  python3 serving_schedule.py menu.json --json

menu.json:
{
  "serve_at": "19:30",
  "oven_preheat_minutes": 15,          # optional, default 15; omit or 0 for no oven
  "tasks": [
    {"name": "Roast chicken", "minutes": 90, "hands_on": 10, "finish_before": 15, "note": "rest, loosely covered", "oven": true},
    {"name": "Roast potatoes", "minutes": 55, "hands_on": 10, "oven": true},
    {"name": "Gravy", "minutes": 10, "hands_on": 10, "after": "Roast chicken"},
    {"name": "Green beans", "minutes": 6, "hands_on": 6}
  ]
}
"minutes" is the total time; "hands_on" the attended minutes (default = minutes);
"finish_before" minutes before serving the task must end (default 0);
"after" names a task this one starts when that one finishes. Python 3.10+, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta


def parse_time(s: str) -> datetime:
    today = datetime.now().replace(second=0, microsecond=0)
    for fmt in ("%H:%M", "%H.%M", "%I:%M %p", "%I%p", "%I %p"):
        try:
            t = datetime.strptime(s.strip(), fmt)
            return today.replace(hour=t.hour, minute=t.minute)
        except ValueError:
            continue
    raise SystemExit(f"Could not read serve_at time {s!r}; use HH:MM")


def schedule(menu: dict) -> dict:
    serve = parse_time(menu["serve_at"])
    tasks = menu["tasks"]
    if not tasks:
        raise SystemExit("No tasks given")
    by_name = {t["name"]: t for t in tasks}
    for t in tasks:
        t.setdefault("hands_on", t["minutes"])
        t.setdefault("finish_before", 0)
        if t["hands_on"] > t["minutes"]:
            t["hands_on"] = t["minutes"]
    # resolve end times: a task with "after" ends relative to its predecessor's end
    ends: dict[str, datetime] = {}

    def end_of(t: dict, depth: int = 0) -> datetime:
        if t["name"] in ends:
            return ends[t["name"]]
        if depth > len(tasks):
            raise SystemExit("Circular 'after' chain")
        if t.get("after"):
            pred = by_name.get(t["after"])
            if pred is None:
                raise SystemExit(f"{t['name']!r} is after unknown task {t['after']!r}")
            start = end_of(pred, depth + 1)
            end = start + timedelta(minutes=t["minutes"])
            latest = serve - timedelta(minutes=t["finish_before"])
            if end > latest:
                # the predecessor must finish earlier to make room
                shift = end - latest
                ends[pred["name"]] = ends[pred["name"]] - shift
                pred["_shifted"] = int(shift.total_seconds() // 60)
                end = latest
        else:
            end = serve - timedelta(minutes=t["finish_before"])
        ends[t["name"]] = end
        return end

    for t in tasks:
        end_of(t)
    rows = []
    for t in tasks:
        end = ends[t["name"]]
        start = end - timedelta(minutes=t["minutes"])
        rows.append({"name": t["name"], "start": start, "end": end, "minutes": t["minutes"], "hands_on": t["hands_on"],
                     "note": t.get("note", ""), "oven": bool(t.get("oven")), "shifted": t.get("_shifted", 0)})
    rows.sort(key=lambda r: r["start"])
    # hands-on overlap check: assume attended minutes sit at the start of each task
    warnings = []
    minute_load: dict[datetime, list[str]] = {}
    for r in rows:
        for m in range(r["hands_on"]):
            key = r["start"] + timedelta(minutes=m)
            minute_load.setdefault(key, []).append(r["name"])
    busy = sorted({tuple(v) for v in minute_load.values() if len(v) > 1})
    for names in busy:
        warnings.append("Hands-on work overlaps: " + " and ".join(names) + ". Prep one of them earlier or get a second pair of hands.")
    preheat = menu.get("oven_preheat_minutes", 15 if any(r["oven"] for r in rows) else 0)
    oven_on = None
    if preheat and any(r["oven"] for r in rows):
        first_oven = min(r["start"] for r in rows if r["oven"])
        oven_on = first_oven - timedelta(minutes=preheat)
    return {"serve_at": serve, "oven_on": oven_on, "rows": rows, "warnings": warnings}


def render(result: dict) -> str:
    fmt = lambda d: d.strftime("%H:%M")
    lines = [f"**Timeline, serving at {fmt(result['serve_at'])}**", ""]
    events = []
    if result["oven_on"]:
        events.append((result["oven_on"], "Oven on to preheat."))
    for r in result["rows"]:
        what = f"Start {r['name']} ({r['minutes']} min" + (f", {r['hands_on']} min hands-on" if r["hands_on"] != r["minutes"] else "") + ")"
        if r["note"]:
            what += f"; {r['note']}"
        events.append((r["start"], what))
        if r["end"] < result["serve_at"]:
            events.append((r["end"], f"{r['name']} done; keep warm or rest until serving."))
    events.append((result["serve_at"], "Serve."))
    events.sort(key=lambda e: e[0])
    for i, (t, what) in enumerate(events, 1):
        lines.append(f"{i}. **{fmt(t)}** {what}")
    if any(r["shifted"] for r in result["rows"]):
        lines += ["", "Note: " + "; ".join(f"{r['name']} was moved {r['shifted']} min earlier so what follows it fits" for r in result["rows"] if r["shifted"]) + "."]
    if result["warnings"]:
        lines += ["", "**Watch out**"] + [f"- {w}" for w in result["warnings"]]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    menu = json.load(open(a.file, encoding="utf-8"))
    result = schedule(menu)
    if a.json:
        out = {"serve_at": result["serve_at"].strftime("%H:%M"), "oven_on": result["oven_on"].strftime("%H:%M") if result["oven_on"] else None,
               "rows": [{**r, "start": r["start"].strftime("%H:%M"), "end": r["end"].strftime("%H:%M")} for r in result["rows"]],
               "warnings": result["warnings"]}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
