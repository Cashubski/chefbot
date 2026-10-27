#!/usr/bin/env python3
"""Merge the ingredient lines of several recipes into one shopping list by aisle.

Usage:
  python3 shopping_list.py plan.json              # {"recipes":[{"name":..,"ingredients":[..]}, ..]}
  python3 shopping_list.py plan.txt               # "# Recipe name" headers, one ingredient per line
  python3 shopping_list.py plan.json --have have.txt   # drop items already in the cupboard
  python3 shopping_list.py plan.json --json

Python 3.10+, standard library only. Quantities with the same unit are summed;
teaspoons, tablespoons and cups are converted to millilitres; incompatible units
for one item are listed side by side rather than guessed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from fractions import Fraction

UNICODE_FRACTIONS = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}
UNIT_ALIASES = {
    "g": ("g", "gram", "grams", "gr"), "kg": ("kg", "kilogram", "kilograms", "kilo", "kilos"),
    "oz": ("oz", "ounce", "ounces"), "lb": ("lb", "lbs", "pound", "pounds"),
    "ml": ("ml", "millilitre", "millilitres", "milliliter", "milliliters"), "l": ("l", "litre", "litres", "liter", "liters"),
    "fl oz": ("fl oz", "fl. oz", "fluid ounce", "fluid ounces"), "cup": ("cup", "cups"),
    "tsp": ("tsp", "tsps", "teaspoon", "teaspoons"), "tbsp": ("tbsp", "tbsps", "tbs", "tablespoon", "tablespoons"),
    "clove": ("clove", "cloves"), "slice": ("slice", "slices"), "sprig": ("sprig", "sprigs"), "stick": ("stick", "sticks"),
    "tin": ("tin", "tins", "can", "cans"), "bunch": ("bunch", "bunches"), "piece": ("piece", "pieces"),
    "sheet": ("sheet", "sheets"), "sachet": ("sachet", "sachets", "packet", "packets", "pack", "packs"),
    "pinch": ("pinch", "pinches"), "handful": ("handful", "handfuls"), "dash": ("dash", "splash", "glug", "drizzle"),
}
ALIAS = {a: u for u, al in UNIT_ALIASES.items() for a in al}
UNIT_PATTERN = "|".join(sorted((re.escape(a) for a in ALIAS), key=len, reverse=True))
NUMBER = r"(?:\d*\s?[½¼¾⅓⅔⅛⅜⅝⅞]|\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
LINE_RE = re.compile(rf"^\s*(?P<q>{NUMBER})(?:\s*(?:-|–|to)\s*(?P<qh>{NUMBER}))?\s*(?:x\s*)?(?:(?P<unit>{UNIT_PATTERN})\b\.?\s*)?(?:of\s+)?(?P<name>.+?)\s*$", re.IGNORECASE)
VAGUE_RE = re.compile(r"^\s*(?:a|an|one|some)\s+(?P<unit>pinch|handful|dash|splash|glug|drizzle|few|little)\s+(?:of\s+)?(?P<name>.+?)\s*$", re.IGNORECASE)
TO_ML = {"tsp": 5.0, "tbsp": 15.0, "cup": 240.0, "fl oz": 29.5735, "l": 1000.0, "ml": 1.0}
TO_G = {"g": 1.0, "kg": 1000.0, "oz": 28.3495, "lb": 453.592}

# words stripped from names so "finely chopped onion" and "onions" merge
PREP_WORDS = {"finely", "roughly", "thinly", "thickly", "freshly", "chopped", "diced", "sliced", "minced", "grated",
              "crushed", "peeled", "cubed", "shredded", "halved", "quartered", "beaten", "melted", "softened", "ripe",
              "large", "medium", "small", "fresh", "dried", "ground", "whole", "boneless", "skinless", "cooked",
              "raw", "warm", "cold", "hot", "room", "temperature", "to", "taste", "for", "serving", "garnish",
              "plus", "extra", "optional", "zest", "juice", "of", "the", "a", "an", "and", "or"}
KEEP_COMPOUND = ("spring onion", "red onion", "olive oil", "sesame oil", "coconut oil", "vegetable oil", "soy sauce",
                 "fish sauce", "tomato puree", "tomato purée", "red pepper", "green pepper", "chilli flakes",
                 "baking powder", "bicarbonate of soda", "baking soda", "lemon juice", "lime juice", "lemon zest",
                 "sweet potato", "double cream", "single cream", "sour cream", "cream cheese", "greek yoghurt",
                 "coconut milk", "plain flour", "bread flour", "self-raising flour", "all-purpose flour", "brown sugar",
                 "caster sugar", "icing sugar", "chicken thighs", "chicken breasts", "chicken stock", "vegetable stock",
                 "beef stock", "bay leaves", "bay leaf", "spring greens", "black pepper", "sea salt")

AISLES = (
    ("Fruit and vegetables", ("onion", "garlic", "carrot", "potato", "tomato", "pepper", "chilli", "chili", "lemon", "lime", "apple",
                              "banana", "orange", "spinach", "kale", "cabbage", "lettuce", "salad", "cucumber", "courgette", "zucchini",
                              "aubergine", "eggplant", "mushroom", "leek", "celery", "broccoli", "cauliflower", "pea", "bean", "corn",
                              "avocado", "herb", "parsley", "coriander", "cilantro", "basil", "mint", "thyme", "rosemary", "dill",
                              "chive", "ginger", "spring onion", "shallot", "squash", "pumpkin", "sweet potato", "beetroot", "fennel",
                              "asparagus", "berry", "berries", "grape", "pear", "peach", "mango", "pineapple", "melon", "cherry",
                              "plum", "radish", "rocket", "arugula", "sprout", "turnip", "parsnip", "swede", "chard", "pak choi", "bok choy")),
    ("Meat and fish", ("chicken", "beef", "pork", "lamb", "turkey", "sausage", "bacon", "ham", "mince", "steak", "fillet", "salmon",
                       "cod", "tuna", "prawn", "shrimp", "fish", "haddock", "mackerel", "trout", "duck", "chorizo", "pancetta", "anchov")),
    ("Dairy and eggs", ("milk", "butter", "cheese", "cheddar", "mozzarella", "parmesan", "feta", "yoghurt", "yogurt", "cream", "egg",
                        "halloumi", "ricotta", "mascarpone", "crème", "creme fraiche", "paneer")),
    ("Bakery", ("bread", "roll", "bun", "tortilla", "pitta", "pita", "naan", "wrap", "baguette", "croissant", "crumpet", "sourdough")),
    ("Tins, jars and sauces", ("tin", "can", "chopped tomatoes", "passata", "puree", "purée", "paste", "stock", "soy", "fish sauce",
                               "vinegar", "mustard", "ketchup", "mayonnaise", "harissa", "pesto", "curry paste", "coconut milk",
                               "chickpea", "lentil", "kidney bean", "black bean", "butter bean", "cannellini", "tahini", "honey",
                               "syrup", "jam", "olive", "caper", "pickle", "sauce", "oil")),
    ("Rice, pasta and dry goods", ("rice", "pasta", "spaghetti", "penne", "noodle", "couscous", "quinoa", "bulgur", "flour", "sugar", "oat",
                                   "polenta", "cornflour", "cornstarch", "breadcrumb", "yeast", "baking powder", "bicarbonate", "cocoa",
                                   "chocolate", "nut", "almond", "walnut", "cashew", "peanut", "seed", "raisin", "sultana", "date", "lentils")),
    ("Herbs and spices", ("salt", "pepper", "cumin", "coriander seed", "paprika", "turmeric", "cinnamon", "nutmeg", "clove", "cardamom",
                          "garam masala", "curry powder", "chilli flakes", "chili flakes", "cayenne", "oregano", "bay", "mixed herbs",
                          "mixed spice", "allspice", "saffron", "vanilla", "star anise", "fennel seed", "mustard seed", "sumac", "za'atar")),
    ("Frozen", ("frozen", "ice cream", "ice")),
    ("Drinks", ("wine", "beer", "cider", "juice", "water", "stout", "sherry", "brandy", "rum", "whisky", "vermouth")),
)


def to_number(tok: str) -> float:
    tok = tok.strip()
    for u, f in UNICODE_FRACTIONS.items():
        tok = tok.replace(u, " " + f).strip()
    return sum(float(Fraction(p)) if "/" in p else float(p.replace(",", ".")) for p in tok.split())


def parse_line(line: str) -> dict | None:
    raw = line.strip().lstrip("-*•").strip()
    if not raw or raw.lower().startswith(("optional", "to serve", "for the", "garnish")):
        return None
    m = LINE_RE.match(raw)
    if m:
        q = to_number(m.group("q"))
        qh = to_number(m.group("qh")) if m.group("qh") else None
        unit = ALIAS[m.group("unit").lower()] if m.group("unit") else None
        name = m.group("name")
    else:
        v = VAGUE_RE.match(raw)
        if v:
            q, qh, unit, name = 1.0, None, ALIAS.get(v.group("unit").lower(), "pinch"), v.group("name")
        else:
            q, qh, unit, name = None, None, None, raw
    if "(" in name:
        name = name.split("(")[0]
    name = name.split(",")[0].strip()
    return {"raw": raw, "quantity": q if qh is None else max(q, qh), "unit": unit, "name": name}


def canonical_name(name: str) -> str:
    n = name.lower().strip().replace("’", "'").split(",")[0].split("(")[0]
    n = re.sub(r"[^\w\s'-]", " ", n).strip()
    for comp in KEEP_COMPOUND:
        if comp in n:
            return comp
    words = [w for w in re.split(r"[\s/]+", n) if w and w not in PREP_WORDS]
    if not words:
        words = [n]
    w = words[-1]
    # naive singular
    if w.endswith("ies"):
        w = w[:-3] + "y"
    elif w.endswith("oes"):
        w = w[:-2]
    elif w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    words[-1] = w
    return " ".join(words)


def aisle_for(name: str) -> str:
    n = name.lower()
    for aisle, keys in AISLES:
        if any(k in n for k in keys):
            return aisle
    return "Other"


def fmt(q: float) -> str:
    if float(q).is_integer():
        return str(int(q))
    return f"{q:.2f}".rstrip("0").rstrip(".")


def merge(recipes: list[dict], have: set[str] | None = None) -> dict[str, list[dict]]:
    """Return aisle -> list of {name, amounts: {unit: qty}, used_in: [..]}"""
    items: dict[str, dict] = {}
    for r in recipes:
        for line in r["ingredients"]:
            p = parse_line(line)
            if p is None:
                continue
            key = canonical_name(p["name"])
            if have and (key in have or p["name"].lower() in have):
                continue
            it = items.setdefault(key, {"name": key, "amounts": defaultdict(float), "used_in": [], "unparsed": []})
            if r["name"] not in it["used_in"]:
                it["used_in"].append(r["name"])
            q, u = p["quantity"], p["unit"]
            if q is None:
                it["unparsed"].append(p["raw"])
                continue
            if u in TO_ML:
                it["amounts"]["ml"] += q * TO_ML[u]
            elif u in TO_G:
                it["amounts"]["g"] += q * TO_G[u]
            else:
                it["amounts"][u or "whole"] += q
    by_aisle: dict[str, list[dict]] = defaultdict(list)
    for it in items.values():
        by_aisle[aisle_for(it["name"])].append(it)
    for lst in by_aisle.values():
        lst.sort(key=lambda d: d["name"])
    return dict(by_aisle)


def amount_text(amounts: dict[str, float]) -> str:
    parts = []
    for unit, q in amounts.items():
        if unit == "g" and q >= 1000:
            parts.append(f"{fmt(round(q / 10) / 100)} kg")
        elif unit == "ml" and q >= 1000:
            parts.append(f"{fmt(round(q / 10) / 100)} l")
        elif unit in ("g", "ml"):
            parts.append(f"{fmt(round(q))} {unit}")
        elif unit == "whole":
            parts.append(fmt(q))
        else:
            parts.append(f"{fmt(q)} {unit}{'s' if q != 1 and unit not in ('tsp', 'tbsp', 'pinch', 'dash') else ''}")
    return " + ".join(parts)


def render(by_aisle: dict[str, list[dict]]) -> str:
    out = ["**Shopping list**"]
    order = [a for a, _ in AISLES] + ["Other"]
    for aisle in order:
        if aisle not in by_aisle:
            continue
        out += ["", f"*{aisle}*"]
        for it in by_aisle[aisle]:
            amt = amount_text(it["amounts"])
            name = it["name"]
            whole = it["amounts"].get("whole")
            if whole and whole != 1 and len(it["amounts"]) == 1 and not name.endswith("s"):
                name = name[:-1] + "ies" if name.endswith("y") else name + "s"
            line = f"- {name}" + (f": {amt}" if amt else "")
            if it["unparsed"]:
                line += " (" + "; ".join(it["unparsed"]) + ")"
            if len(it["used_in"]) > 1:
                line += f"  ·  {', '.join(it['used_in'])}"
            out.append(line)
    return "\n".join(out)


def load(path: str) -> list[dict]:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        data = json.loads(text)
        return data["recipes"] if isinstance(data, dict) else data
    recipes, current = [], None
    for line in text.splitlines():
        if line.startswith("#"):
            current = {"name": line.lstrip("#").strip(), "ingredients": []}
            recipes.append(current)
        elif line.strip():
            if current is None:
                current = {"name": "Recipe", "ingredients": []}
                recipes.append(current)
            current["ingredients"].append(line)
    return recipes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--have", help="text file of items already in the cupboard, one per line")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    recipes = load(a.file)
    have = None
    if a.have:
        have = {canonical_name(l) for l in open(a.have, encoding="utf-8").read().splitlines() if l.strip()}
    by_aisle = merge(recipes, have)
    if a.json:
        print(json.dumps({k: [{**it, "amounts": dict(it["amounts"])} for it in v] for k, v in by_aisle.items()}, indent=2, ensure_ascii=False))
    else:
        print(render(by_aisle))
    return 0


if __name__ == "__main__":
    sys.exit(main())
