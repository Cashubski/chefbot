#!/usr/bin/env python3
"""Roasting time, temperature, resting, defrosting and a serving timeline for a joint or bird.

Usage:
  python3 roast_timer.py --meat chicken --weight-kg 1.8
  python3 roast_timer.py --meat beef --weight-kg 2 --doneness medium-rare --serve-at 19:30
  python3 roast_timer.py --meat turkey --weight-kg 5.5 --stuffed --json

Meats: chicken, turkey, beef, lamb, pork, ham, duck, goose. Times follow standard UK
guidance (minutes per 500 g or per kg plus a base). Always check with a probe
thermometer; the time is an estimate. Python 3.10+, standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta

MEATS = ("chicken", "turkey", "beef", "lamb", "pork", "ham", "duck", "goose")
DONENESS = ("rare", "medium-rare", "medium", "well")

# per-500g minutes, base minutes, oven °C conventional, target internal °C, rest minutes
RULES: dict[str, dict] = {
    "chicken": {"per500": 20, "base": 20, "oven": 200, "fan": 190, "target": 75, "rest": 15},
    "beef": {
        "rare": {"per500": 20, "base": 20, "target": 52},
        "medium-rare": {"per500": 22, "base": 22, "target": 56},
        "medium": {"per500": 25, "base": 25, "target": 60},
        "well": {"per500": 30, "base": 30, "target": 70},
        "oven": 190, "fan": 170, "rest": 20,
    },
    "lamb": {
        "rare": {"per500": 20, "base": 20, "target": 54},
        "medium-rare": {"per500": 22, "base": 22, "target": 57},
        "medium": {"per500": 25, "base": 25, "target": 60},
        "well": {"per500": 30, "base": 30, "target": 70},
        "oven": 190, "fan": 170, "rest": 20,
    },
    "pork": {"per500": 35, "base": 35, "oven": 180, "fan": 160, "target": 70, "rest": 15},
    "ham": {"per500": 20, "base": 20, "oven": 180, "fan": 160, "target": 70, "rest": 15},
    "goose": {"per500": 15, "base": 30, "oven": 180, "fan": 160, "target": 75, "rest": 30},
    # duck and turkey are per kilogram
    "duck": {"perkg": 45, "base": 0, "oven": 180, "fan": 160, "target": 75, "rest": 20},
    "turkey": {"perkg": 20, "oven": 180, "fan": 160, "target": 75, "rest": 30},
}
STUFFED_EXTRA = 20
PREHEAT = 20
OUT_OF_FRIDGE = 60


def parse_time(s: str) -> datetime:
    today = datetime.now().replace(second=0, microsecond=0)
    for fmt in ("%H:%M", "%H.%M", "%I:%M %p", "%I%p", "%I %p"):
        try:
            t = datetime.strptime(s.strip(), fmt)
            return today.replace(hour=t.hour, minute=t.minute)
        except ValueError:
            continue
    raise ValueError(f"could not read time {s!r}; use HH:MM")


def cooking_minutes(meat: str, weight_kg: float, doneness: str = "medium", stuffed: bool = False) -> dict:
    if meat not in RULES:
        raise ValueError(f"unknown meat {meat!r}; choose from {', '.join(MEATS)}")
    if not (0.2 <= weight_kg <= 25):
        raise ValueError("weight must be between 0.2 and 25 kg")
    r = RULES[meat]
    if meat in ("beef", "lamb"):
        d = r.get(doneness) or r["medium"]
        per500, base, target = d["per500"], d["base"], d["target"]
        minutes = per500 * weight_kg * 2 + base
        rule = f"{per500} min per 500 g plus {base} min ({doneness})"
    elif meat == "turkey":
        base = 70 if 4 <= weight_kg <= 6 else 90
        minutes = r["perkg"] * weight_kg + base
        target = r["target"]
        rule = f"{r['perkg']} min per kg plus {base} min"
    elif meat == "duck":
        minutes = r["perkg"] * weight_kg
        target = r["target"]
        rule = f"{r['perkg']} min per kg"
    else:
        minutes = r["per500"] * weight_kg * 2 + r["base"]
        target = r["target"]
        rule = f"{r['per500']} min per 500 g plus {r['base']} min"
    if stuffed:
        minutes += STUFFED_EXTRA
        rule += f", plus {STUFFED_EXTRA} min for stuffing"
    minutes = int(round(minutes / 5.0) * 5)
    if meat == "turkey":
        defrost_hours = 24 * weight_kg / 2
    else:
        defrost_hours = 11 * weight_kg
    return {
        "meat": meat, "weight_kg": weight_kg, "doneness": doneness if meat in ("beef", "lamb") else None,
        "stuffed": stuffed, "minutes": minutes, "rule": rule, "oven_c": r["oven"], "fan_c": r["fan"],
        "target_c": target, "rest_minutes": r["rest"], "defrost_hours": int(round(defrost_hours)),
    }


def timeline(result: dict, serve_at: str) -> dict:
    serve = parse_time(serve_at)
    carve = serve - timedelta(minutes=5)
    out = carve - timedelta(minutes=result["rest_minutes"])
    in_oven = out - timedelta(minutes=result["minutes"])
    oven_on = in_oven - timedelta(minutes=PREHEAT)
    fridge_out = in_oven - timedelta(minutes=OUT_OF_FRIDGE)
    f = lambda d: d.strftime("%H:%M")
    return {"fridge_out": f(fridge_out), "oven_on": f(oven_on), "in_oven": f(in_oven), "out_of_oven": f(out),
            "carve": f(carve), "serve": f(serve), "probe_check": f(out - timedelta(minutes=max(10, result["minutes"] // 8)))}


def render(result: dict, tl: dict | None) -> str:
    name = result["meat"]
    head = f"**{name.capitalize()}, {result['weight_kg']:g} kg"
    if result["doneness"]:
        head += f", {result['doneness']}"
    if result["stuffed"]:
        head += ", stuffed"
    head += "**"
    hours, mins = divmod(result["minutes"], 60)
    dur = f"{hours} h {mins:02d} min" if hours else f"{mins} min"
    lines = [head, "",
             f"- Roast about **{dur}** at {result['oven_c']} °C / {result['fan_c']} °C fan ({result['rule']}).",
             f"- Done at **{result['target_c']} °C** in the thickest part, away from the bone. Start probing {max(10, result['minutes'] // 8)} minutes before the end; the time is only an estimate.",
             f"- Rest **{result['rest_minutes']} min**, loosely covered. Large joints rise 3 to 5 °C while resting.",
             f"- Frozen? Defrost in the fridge for about **{result['defrost_hours']} hours** ({result['defrost_hours'] / 24:.1f} days). Take it out of the fridge an hour before roasting."]
    if name == "pork":
        lines.append("- For crackling: dry the skin, score, salt, and start at 240 °C for the first 20 to 30 minutes, then drop to 180 °C for the time above.")
    if name in ("duck", "goose"):
        lines.append("- Prick the skin, roast on a rack, and pour off the fat two or three times; keep it for the potatoes.")
    if name == "turkey":
        lines.append("- Cover with foil for the first two thirds, uncover to brown. Cook stuffing separately if the bird is over 5 kg.")
    if tl:
        lines += ["", f"**Timeline for serving at {tl['serve']}**",
                  f"1. **{tl['fridge_out']}** Out of the fridge.",
                  f"2. **{tl['oven_on']}** Oven on to preheat.",
                  f"3. **{tl['in_oven']}** Into the oven.",
                  f"4. **{tl['probe_check']}** First probe check.",
                  f"5. **{tl['out_of_oven']}** Out of the oven to rest.",
                  f"6. **{tl['carve']}** Carve.",
                  f"7. **{tl['serve']}** Serve."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meat", required=True, choices=MEATS)
    ap.add_argument("--weight-kg", type=float, required=True)
    ap.add_argument("--doneness", choices=DONENESS, default="medium", help="beef and lamb only")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--bone", action="store_true", help="on the bone (default; times assume it)")
    g.add_argument("--boneless", action="store_true", help="boneless joint: cooks a little faster, check early")
    ap.add_argument("--stuffed", action="store_true")
    ap.add_argument("--oven-c", type=int, help="override the oven temperature shown")
    ap.add_argument("--serve-at", help="HH:MM to build the timeline")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        result = cooking_minutes(a.meat, a.weight_kg, a.doneness, a.stuffed)
        if a.boneless:
            result["rule"] += "; boneless, so start checking 10 min early"
        if a.oven_c:
            result["oven_c"] = a.oven_c
            result["fan_c"] = a.oven_c - 20
        tl = timeline(result, a.serve_at) if a.serve_at else None
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({**result, "timeline": tl}, indent=2))
    else:
        print(render(result, tl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
