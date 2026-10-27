#!/usr/bin/env python3
"""Work out how much food and drink to buy for a group.

Usage:
  python3 party_quantities.py menu.txt --people 12
  python3 party_quantities.py menu.txt --people 20 --kids 4 --teens 2 --buffet
  python3 party_quantities.py menu.txt --people 8 --courses starter,main,side,dessert --json

menu.txt has one dish per line, optionally "dish | type". Types: main-boneless,
main-bone-in, fish, whole-bird, potatoes, rice, pasta-main, pasta-starter,
green-veg, salad, bread, sauce, cheese, dessert, canape, soup. Without a type the
script guesses from the dish name. --people is the total head count; --kids and
--teens are how many of those are children under 12 and teenagers. Python 3.10+,
standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

# type -> (per adult, unit, rounding step for the total, label of what is weighed)
PORTIONS: dict[str, tuple[float, str, float, str]] = {
    "main-boneless": (180, "g", 50, "raw, boneless"),
    "main-bone-in": (300, "g", 50, "raw, on the bone"),
    "fish": (170, "g", 50, "raw fillet"),
    "whole-bird": (450, "g", 100, "raw, on the bone"),
    "potatoes": (200, "g", 250, "raw"),
    "rice": (75, "g", 100, "dry"),
    "pasta-main": (90, "g", 100, "dry"),
    "pasta-starter": (60, "g", 100, "dry"),
    "green-veg": (90, "g", 50, "trimmed"),
    "salad": (70, "g", 50, "leaves and vegetables"),
    "bread": (70, "g", 50, "about 1 to 2 slices or a roll"),
    "sauce": (90, "ml", 50, "gravy, sauce or dressing"),
    "cheese": (70, "g", 50, "total across the board"),
    "dessert": (135, "g", 50, "finished weight"),
    "canape": (5, "pieces", 1, "per hour before dinner"),
    "soup": (250, "ml", 250, "as a starter"),
}
TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("canape", ("canap", "blini", "crostini", "vol-au-vent", "nibbles", "bites", "skewers", "arancini", "croquette")),
    ("soup", ("soup", "broth", "bisque", "chowder", "gazpacho", "consomm")),
    ("whole-bird", ("whole chicken", "roast chicken", "turkey", "goose", "whole duck", "roast duck", "poussin", "capon")),
    ("fish", ("salmon", "cod", "haddock", "sea bass", "seabass", "bream", "trout", "tuna", "fish", "prawn", "halibut", "monkfish", "hake", "mackerel", "sole", "plaice")),
    ("main-bone-in", ("chop", "rib", "shoulder", "leg of lamb", "on the bone", "bone-in", "wings", "drumstick", "thighs", "shank", "rack of lamb", "spare rib", "t-bone")),
    ("main-boneless", ("beef", "lamb", "pork", "chicken", "fillet", "steak", "loin", "sirloin", "brisket", "mince", "burger", "sausage", "ham", "gammon", "tofu", "tempeh", "paneer", "curry", "stew", "casserole", "chilli", "chili", "ragu", "tagine", "lasagne", "lasagna", "pie", "nut roast", "wellington", "kebab", "kofta", "meatball", "dal", "dhal")),
    ("potatoes", ("potato", "mash", "chips", "wedges", "dauphinoise", "gratin", "fries")),
    ("rice", ("rice", "pilaf", "pilau", "risotto", "biryani", "paella", "jollof")),
    ("pasta-main", ("pasta", "spaghetti", "penne", "rigatoni", "tagliatelle", "linguine", "macaroni", "noodle", "gnocchi", "orzo", "fusilli")),
    ("green-veg", ("green", "bean", "broccoli", "sprout", "cabbage", "carrot", "pea", "asparagus", "spinach", "kale", "courgette", "leek", "cauliflower", "veg", "parsnip", "squash", "roots")),
    ("salad", ("salad", "slaw", "leaves", "tabbouleh", "coleslaw")),
    ("bread", ("bread", "roll", "baguette", "focaccia", "naan", "pitta", "pita", "flatbread", "garlic bread", "cornbread", "bun")),
    ("sauce", ("gravy", "sauce", "dressing", "jus", "chutney", "salsa", "dip", "raita", "tzatziki", "hummus", "aioli", "mayo")),
    ("cheese", ("cheese board", "cheeseboard", "cheese", "brie", "cheddar", "stilton")),
    ("dessert", ("dessert", "pudding", "cake", "tart", "pie", "trifle", "pavlova", "cheesecake", "brownie", "mousse", "ice cream", "crumble", "tiramisu", "panna cotta", "sorbet", "cookie", "biscuit", "cupcake", "meringue", "fruit")),
)
DEFAULT_COURSES = "main,side,side,dessert"


def guess_type(name: str) -> str:
    n = name.lower()
    # dessert words beat the "pie" in main-boneless when sweet words are present
    sweet = ("apple", "cherry", "lemon", "chocolate", "banoffee", "pecan", "pumpkin pie", "mince pie", "key lime", "custard")
    if "pie" in n and any(w in n for w in sweet):
        return "dessert"
    for type_, keys in TYPE_KEYWORDS:
        if any(k in n for k in keys):
            return type_
    return "main-boneless"


def parse_menu(text: str) -> list[dict]:
    dishes = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*•").strip()
        if not line or line.startswith("#"):
            continue
        name, _, type_ = line.partition("|")
        name = name.strip()
        type_ = type_.strip().lower().replace(" ", "-").replace("_", "-")
        guessed = False
        if type_ not in PORTIONS:
            type_ = guess_type(name)
            guessed = True
        dishes.append({"dish": name, "type": type_, "guessed": guessed})
    return dishes


def round_up(value: float, step: float) -> float:
    if step <= 0:
        return value
    return math.ceil(value / step - 1e-9) * step


def compute(dishes: list[dict], people: int, kids: int = 0, teens: int = 0, buffet: bool = False,
            courses: str = DEFAULT_COURSES, hours: float = 3.0) -> dict:
    people = max(0, int(people))
    kids = min(max(0, int(kids)), people)
    teens = min(max(0, int(teens)), people - kids)
    adults = people - kids - teens
    # kids eat half, teens eat a quarter more on mains/starch/bread, the same on the rest
    eaters_general = adults + teens + 0.5 * kids
    eaters_hearty = adults + 1.25 * teens + 0.5 * kids
    hearty_types = {"main-boneless", "main-bone-in", "fish", "whole-bird", "potatoes", "rice", "pasta-main", "pasta-starter", "bread"}
    # several dishes of the same kind share the per-head total
    counts: dict[str, int] = {}
    groups = {"main": ("main-boneless", "main-bone-in", "fish", "whole-bird"),
              "starch": ("potatoes", "rice", "pasta-main"),
              "veg": ("green-veg", "salad")}
    group_of = {t: g for g, ts in groups.items() for t in ts}
    for d in dishes:
        g = group_of.get(d["type"], d["type"])
        counts[g] = counts.get(g, 0) + 1
    buffet_factor = 1.0
    if buffet:
        buffet_factor = 0.8 if people > 20 else 0.9 if people >= 12 else 1.0
    rows = []
    for d in dishes:
        per_adult, unit, step, basis = PORTIONS[d["type"]]
        g = group_of.get(d["type"], d["type"])
        share = counts.get(g, 1)
        share_factor = 1.0 if share <= 1 else max(1.0 / share, 0.5 if g == "main" else 0.6)
        per_adult_adj = per_adult * share_factor * buffet_factor
        if d["type"] == "canape":
            per_adult_adj = per_adult * hours if hours else per_adult
            basis = f"{per_adult} per person per hour over {hours:g} h"
        eaters = eaters_hearty if d["type"] in hearty_types else eaters_general
        total = per_adult_adj * eaters
        rows.append({
            "dish": d["dish"], "type": d["type"], "guessed": d["guessed"],
            "per_person": int(round(per_adult_adj)),
            "unit": unit, "basis": basis,
            "total": round_up(total, step) if total > 0 else 0,
            "notes": "; ".join(n for n in (
                f"shared with {share - 1} other {g} dish{'es' if share > 2 else ''}" if share > 1 else "",
                "buffet reduction applied" if buffet_factor < 1 else "",
                "type guessed from the name" if d["guessed"] else "") if n),
        })
    drink_adults = adults + teens  # teenagers drink soft drinks; wine counts adults only
    drinks = {
        "wine_bottles": math.ceil(adults * 0.5 * max(hours, 2) / 2) if adults else 0,
        "soft_drinks_litres": round(people * 0.5 * (1 + 0.25 * max(0, (hours - 3) / 2)), 1),
        "ice_kg": round(people * 0.5, 1),
        "alcohol_free_servings": drink_adults + kids,
    }
    return {"people": people, "adults": adults, "teens": teens, "kids": kids, "buffet": buffet, "hours": hours,
            "courses": courses, "rows": rows, "drinks": drinks}


def fmt_amount(value: float, unit: str) -> str:
    if unit == "pieces":
        return f"{int(value)} pieces"
    if unit in ("g", "ml") and value >= 1000:
        return f"{value / 1000:.2f}".rstrip("0").rstrip(".") + (" kg" if unit == "g" else " l")
    return f"{int(value)} {unit}"


def render(result: dict) -> str:
    who = f"{result['people']} people"
    detail = []
    if result["adults"] != result["people"]:
        detail.append(f"{result['adults']} adults")
    if result["teens"]:
        detail.append(f"{result['teens']} teenagers")
    if result["kids"]:
        detail.append(f"{result['kids']} children")
    if detail:
        who += " (" + ", ".join(detail) + ")"
    lines = [f"**Quantities for {who}{', buffet' if result['buffet'] else ''}**", ""]
    if not result["rows"]:
        lines.append("No dishes given. Add one dish per line to the menu file.")
    else:
        lines += ["| Dish | Per person | Total to buy | Notes |", "| --- | --- | --- | --- |"]
        for r in result["rows"]:
            per = f"{r['per_person']} {r['unit']}" if r["unit"] != "pieces" else f"{r['per_person']} pieces"
            lines.append(f"| {r['dish']} | {per} ({r['basis']}) | {fmt_amount(r['total'], r['unit'])} | {r['notes']} |")
    d = result["drinks"]
    lines += ["", f"**Drinks and ice**: about {d['wine_bottles']} bottles of wine for the adults over {result['hours']:g} hours, "
                  f"{d['soft_drinks_litres']} l of soft drinks and water, {d['ice_kg']} kg of ice, and a planned alcohol-free drink "
                  f"for {d['alcohol_free_servings']} people."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("menu", nargs="?", help="menu file, one dish per line; default stdin")
    ap.add_argument("--people", type=int, required=True, help="total head count")
    ap.add_argument("--kids", type=int, default=0, help="children under 12 among them")
    ap.add_argument("--teens", type=int, default=0, help="teenagers among them")
    ap.add_argument("--buffet", action="store_true")
    ap.add_argument("--courses", default=DEFAULT_COURSES)
    ap.add_argument("--hours", type=float, default=3.0, help="length of the event, for drinks and canapés")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.people <= 0:
        ap.error("--people must be positive")
    try:
        text = open(a.menu, encoding="utf-8").read() if a.menu else sys.stdin.read()
    except OSError as e:
        print(f"Could not read menu: {e}", file=sys.stderr)
        return 1
    result = compute(parse_menu(text), a.people, a.kids, a.teens, a.buffet, a.courses, a.hours)
    print(json.dumps(result, indent=2, ensure_ascii=False) if a.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
