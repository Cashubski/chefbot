#!/usr/bin/env python3
"""Baker's percentages and classic ratios, deterministically.

Usage:
  bakers_percent.py --flour 500 --hydration 70 --salt 2 --yeast 1
  bakers_percent.py --dough 900 --hydration 65 --salt 2 --yeast 0.8 --extra oil=4 --extra sugar=3
  bakers_percent.py --flour 500 --hydration 75 --salt 2 --starter 20          # sourdough; starter is 100 % hydration
  bakers_percent.py --analyse recipe.txt                                       # lines like "500 g flour", "350 g water", "10 g salt"
  bakers_percent.py --ratio pie-dough --yield 600                              # classic ratio scaled to a total weight
  bakers_percent.py --list-ratios
Add --json for structured output. Python 3.10+, standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys

# name -> (parts by weight, labels, note)
RATIOS: dict[str, tuple[list[float], list[str], str]] = {
    "bread": ([5, 3, 0.1, 0.05], ["flour", "water", "salt", "instant yeast"], "60 % hydration, 2 % salt, 1 % yeast"),
    "pizza": ([100, 62, 2.5, 0.3], ["flour", "water", "salt", "instant yeast"], "62 % hydration; cold ferment 24-72 h"),
    "pasta": ([3, 2], ["00 flour", "egg"], "about 100 g flour per egg"),
    "flatbread": ([2, 1, 0.03, 0.1], ["flour", "water", "salt", "oil"], "rest 20 min; hot dry pan"),
    "pie-dough": ([3, 2, 1], ["flour", "cold butter", "ice water"], "shortcrust; rest before rolling"),
    "biscuit": ([3, 1, 2], ["flour", "cold butter", "milk or buttermilk"], "add 5 % baking powder; UK scone / US biscuit"),
    "rough-puff": ([1, 1, 0.5], ["flour", "cold butter", "water"], "four book folds"),
    "choux": ([2, 1, 1, 2], ["water", "butter", "flour", "eggs"], "beat eggs in until the paste falls in a V"),
    "pound-cake": ([1, 1, 1, 1], ["eggs", "flour", "butter", "sugar"], "weigh the eggs first; 1 tsp baking powder per 100 g plain flour"),
    "genoise": ([1, 1, 1], ["eggs", "sugar", "flour"], "whisk to the ribbon; fold"),
    "muffin": ([2, 2, 1, 1], ["flour", "milk", "eggs", "butter"], "plus sugar to taste; barely mix"),
    "pancake": ([2, 2, 1, 0.5], ["flour", "milk", "eggs", "butter"], "1 tsp baking powder per 100 g flour"),
    "crepe": ([1, 1, 0.5], ["milk", "eggs", "flour"], "rest 30 min"),
    "yorkshire": ([2, 1, 1], ["milk", "eggs", "flour"], "very hot fat"),
    "cookie": ([1, 2, 3], ["sugar", "butter", "flour"], "more sugar spreads, more flour cakes"),
    "crumble": ([2, 1, 1], ["flour", "butter", "sugar"], "swap up to half the flour for oats"),
    "custard": ([2, 1], ["milk or cream", "eggs"], "bake in a bain-marie to 82 C"),
    "creme-anglaise": ([4, 1, 1], ["milk or cream", "egg yolks", "sugar"], "82-84 C, strain"),
    "caramel-sauce": ([1, 1, 0.25], ["sugar", "cream", "butter"], "cream added off the heat"),
    "ganache": ([1, 1], ["dark chocolate", "cream"], "2:1 for firm, 1:2 for pouring"),
    "vinaigrette": ([3, 1], ["oil", "vinegar or citrus"], "add mustard to emulsify"),
    "roux": ([1, 1], ["butter", "flour"], "60 g thickens 1 litre"),
    "brine": ([20, 1], ["water", "salt"], "5 % brine"),
    "stock": ([3, 2], ["water", "bones"], "bare simmer"),
    "simple-syrup": ([1, 1], ["sugar", "water"], ""),
}
EGG_G = 55.0


def fmt(g: float) -> str:
    if g >= 100:
        return f"{round(g):d} g"
    if g >= 10:
        return f"{g:.0f} g"
    return f"{g:.1f} g".replace(".0 g", " g")


def formula(flour: float, hydration: float, salt: float, yeast: float, starter: float, extras: dict[str, float]) -> dict:
    """Return weights given total flour (including the starter's flour)."""
    rows = []
    starter_g = flour * starter / 100
    flour_in_starter = starter_g / 2
    water_in_starter = starter_g / 2
    rows.append(("flour (added)", 100 - starter / 2, flour - flour_in_starter))
    rows.append(("water (added)", hydration - starter / 2, flour * hydration / 100 - water_in_starter))
    if starter:
        rows.append(("starter, 100 % hydration", starter, starter_g))
    rows.append(("salt", salt, flour * salt / 100))
    if yeast:
        rows.append(("instant yeast", yeast, flour * yeast / 100))
    for name, pct in extras.items():
        rows.append((name, pct, flour * pct / 100))
    total = sum(r[2] for r in rows)
    notes = []
    if not 55 <= hydration <= 85:
        notes.append(f"hydration {hydration:g} % is outside the usual 55-85 % range")
    if not 1.5 <= salt <= 2.5:
        notes.append(f"salt {salt:g} % is outside the usual 1.8-2.2 % range")
    if yeast and yeast > 2:
        notes.append("more than 2 % instant yeast tastes yeasty; use time instead")
    if starter and yeast:
        notes.append("starter and commercial yeast together: fine for a hybrid loaf, but the rise will be fast")
    notes.append("hold back 5 % of the water and add it only if the dough is stiff")
    return {"flour_total": flour, "rows": [{"ingredient": n, "percent": p, "grams": g} for n, p, g in rows], "total": total, "notes": notes}


def solve_flour(dough: float, hydration: float, salt: float, yeast: float, starter: float, extras: dict[str, float]) -> float:
    pct_sum = 100 + hydration + salt + yeast + sum(extras.values())  # starter is already inside flour+water
    return dough * 100 / pct_sum


FLOUR_WORDS = ("flour", "semolina", "rye", "spelt", "wholemeal", "whole wheat")
WATER_WORDS = ("water", "milk", "buttermilk", "beer")


def analyse(text: str) -> dict:
    """Read 'quantity g name' lines and return baker's percentages."""
    items = []
    for line in text.splitlines():
        m = re.match(r"\s*([\d.,]+)\s*(g|gram|grams|kg|ml|millilitres?)\b\s*(?:of\s+)?(.+)", line.strip().lstrip("-*•"), re.I)
        if not m:
            continue
        q = float(m.group(1).replace(",", "."))
        if m.group(2).lower() == "kg":
            q *= 1000
        items.append((m.group(3).strip().lower(), q))
    flour = sum(q for n, q in items if any(w in n for w in FLOUR_WORDS) and "corn" not in n)
    water = sum(q for n, q in items if any(w in n for w in WATER_WORDS))
    starter = sum(q for n, q in items if "starter" in n or "levain" in n or "sourdough" in n)
    if not flour and not starter:
        raise SystemExit("No flour line found (expected lines like '500 g strong white flour').")
    flour_total = flour + starter / 2
    water_total = water + starter / 2
    rows = [{"ingredient": n, "grams": q, "percent": q / flour_total * 100} for n, q in items]
    hydration = water_total / flour_total * 100
    salt = sum(q for n, q in items if "salt" in n) / flour_total * 100
    verdict = ("stiff: bagels, pretzels" if hydration < 58 else "standard: sandwich loaves, pizza" if hydration < 66
               else "soft and open: focaccia, ciabatta, country sourdough" if hydration < 80 else "very wet: high-hydration ciabatta, pan loaves")
    return {"flour_total": flour_total, "hydration": hydration, "salt_percent": salt, "rows": rows, "verdict": verdict}


def ratio_table(name: str, total: float) -> dict:
    parts, labels, note = RATIOS[name]
    s = sum(parts)
    rows = []
    for p, label in zip(parts, labels):
        grams = total * p / s
        row = {"ingredient": label, "parts": p, "grams": grams}
        if label.startswith("egg"):
            row["count"] = round(grams / EGG_G * 2) / 2
        rows.append(row)
    return {"ratio": name, "total": total, "rows": rows, "note": note}


def render_formula(f: dict) -> str:
    out = [f"**Formula for {fmt(f['flour_total'])} total flour (dough about {fmt(f['total'])})**", "", "| Ingredient | % | Weight |", "| --- | --- | --- |"]
    for r in f["rows"]:
        out.append(f"| {r['ingredient']} | {r['percent']:g} | {fmt(r['grams'])} |")
    out += [""] + [f"- {n}" for n in f["notes"]]
    return "\n".join(out)


def render_analysis(a: dict) -> str:
    out = [f"**Hydration {a['hydration']:.0f} %, salt {a['salt_percent']:.1f} % of {fmt(a['flour_total'])} flour** ({a['verdict']})", "", "| Ingredient | Weight | % of flour |", "| --- | --- | --- |"]
    for r in a["rows"]:
        out.append(f"| {r['ingredient']} | {fmt(r['grams'])} | {r['percent']:.1f} |")
    return "\n".join(out)


def render_ratio(t: dict) -> str:
    out = [f"**{t['ratio']} for {fmt(t['total'])}** ({t['note']})" if t["note"] else f"**{t['ratio']} for {fmt(t['total'])}**", "", "| Ingredient | Parts | Weight |", "| --- | --- | --- |"]
    for r in t["rows"]:
        w = fmt(r["grams"]) + (f" (about {r['count']:g} eggs)" if "count" in r else "")
        out.append(f"| {r['ingredient']} | {r['parts']:g} | {w} |")
    return "\n".join(out)


def parse_extras(values: list[str] | None) -> dict[str, float]:
    extras = {}
    for v in values or []:
        if "=" not in v:
            raise SystemExit(f"--extra expects name=percent, got {v!r}")
        name, pct = v.split("=", 1)
        try:
            extras[name.strip()] = float(pct)
        except ValueError:
            raise SystemExit(f"--extra {v!r}: percent must be a number")
    return extras


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flour", type=float, help="total flour in grams")
    ap.add_argument("--dough", type=float, help="target dough weight in grams (solves for flour)")
    ap.add_argument("--hydration", type=float, default=65.0)
    ap.add_argument("--salt", type=float, default=2.0)
    ap.add_argument("--yeast", type=float, default=0.0, help="instant yeast %% of flour")
    ap.add_argument("--starter", type=float, default=0.0, help="sourdough starter %% of flour, at 100%% hydration")
    ap.add_argument("--extra", action="append", help="name=percent, e.g. oil=5")
    ap.add_argument("--analyse", "--analyze", dest="analyse", help="recipe file to turn into percentages")
    ap.add_argument("--ratio", choices=sorted(RATIOS), help="classic ratio")
    ap.add_argument("--yield", dest="total", type=float, help="total weight for --ratio, in grams")
    ap.add_argument("--list-ratios", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.list_ratios:
        for k, (parts, labels, note) in RATIOS.items():
            print(f"{k}: " + " : ".join(f"{p:g}" for p in parts) + " (" + " : ".join(labels) + ")" + (f"; {note}" if note else ""))
        return 0
    for v, name in ((a.flour, "flour"), (a.dough, "dough"), (a.total, "yield")):
        if v is not None and (not math.isfinite(v) or v <= 0):
            ap.error(f"--{name} must be a positive number")
    if a.analyse:
        result = analyse(open(a.analyse, encoding="utf-8").read())
        print(json.dumps(result, indent=2) if a.json else render_analysis(result))
        return 0
    if a.ratio:
        if not a.total:
            ap.error("--ratio needs --yield (total grams)")
        result = ratio_table(a.ratio, a.total)
        print(json.dumps(result, indent=2) if a.json else render_ratio(result))
        return 0
    extras = parse_extras(a.extra)
    if a.flour is None and a.dough is None:
        ap.error("give --flour, --dough, --analyse, --ratio or --list-ratios")
    flour = a.flour if a.flour is not None else solve_flour(a.dough, a.hydration, a.salt, a.yeast, a.starter, extras)
    result = formula(flour, a.hydration, a.salt, a.yeast, a.starter, extras)
    print(json.dumps(result, indent=2) if a.json else render_formula(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
