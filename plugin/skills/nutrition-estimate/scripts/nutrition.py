#!/usr/bin/env python3
"""Estimate the nutrition of a recipe from its ingredient lines.

Usage:
  python3 nutrition.py ingredients.txt --servings 4
  python3 nutrition.py ingredients.txt --servings 4 --json

One ingredient per line ("250 g strong white bread flour", "2 eggs", "1 tbsp olive oil",
"400 g tin chopped tomatoes", "1 onion"). Values come from references/nutrition-table.csv
(per 100 g). Volumes and counts are converted to grams with typical densities and weights,
and every assumption is reported. The output is an ESTIMATE. Python 3.10+, stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

TABLE_PATH = Path(__file__).resolve().parent.parent / "references" / "nutrition-table.csv"
NUTRIENTS = ("kcal", "protein_g", "fat_g", "saturates_g", "carbs_g", "sugars_g", "fibre_g", "salt_g")

UNICODE_FRACTIONS = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3",
                     "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}
UNITS: dict[str, tuple[str, ...]] = {
    "g": ("g", "gram", "grams", "gr"), "kg": ("kg", "kilogram", "kilograms", "kilo", "kilos"),
    "oz": ("oz", "ounce", "ounces"), "lb": ("lb", "lbs", "pound", "pounds"),
    "ml": ("ml", "millilitre", "millilitres", "milliliter", "milliliters"), "l": ("l", "litre", "litres", "liter", "liters"),
    "fl oz": ("fl oz", "fl. oz", "fl.oz", "fluid ounce", "fluid ounces"), "cup": ("cup", "cups"),
    "tsp": ("tsp", "tsps", "teaspoon", "teaspoons"), "tbsp": ("tbsp", "tbsps", "tbs", "tablespoon", "tablespoons"),
    "pinch": ("pinch", "pinches"), "handful": ("handful", "handfuls"), "dash": ("dash", "dashes", "splash", "glug", "drizzle"),
    "clove": ("clove", "cloves"), "slice": ("slice", "slices"), "sprig": ("sprig", "sprigs"), "stick": ("stick", "sticks"),
    "tin": ("tin", "tins", "can", "cans"), "bunch": ("bunch", "bunches"), "piece": ("piece", "pieces"),
    "sheet": ("sheet", "sheets"), "sachet": ("sachet", "sachets", "packet", "packets", "pack", "packs"),
    "rasher": ("rasher", "rashers"), "fillet": ("fillet", "fillets"), "stalk": ("stalk", "stalks"),
}
ALIAS_TO_UNIT = {a: u for u, aliases in UNITS.items() for a in aliases}
UNIT_PATTERN = "|".join(sorted((re.escape(a) for a in ALIAS_TO_UNIT), key=len, reverse=True))
NUMBER = r"(?:\d*\s?[½¼¾⅓⅔⅛⅜⅝⅞]|\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
LINE_RE = re.compile(
    rf"^\s*(?P<q>{NUMBER})(?:\s*(?:-|–|to)\s*(?P<qh>{NUMBER}))?\s*(?:x\s*)?"
    rf"(?:(?P<unit>{UNIT_PATTERN})\b\.?\s*)?(?:of\s+)?(?P<name>.+?)\s*$", re.IGNORECASE)
VAGUE_RE = re.compile(r"^\s*(?:a|an|one|some)\s+(?P<unit>pinch|handful|dash|splash|glug|drizzle|knob|few|little)\s+(?:of\s+)?(?P<name>.+?)\s*$",
                      re.IGNORECASE)

G_PER_OZ, G_PER_LB = 28.3495, 453.592
ML = {"ml": 1.0, "l": 1000.0, "fl oz": 29.5735, "cup": 240.0, "tbsp": 15.0, "tsp": 5.0}

# grams per ml for volume -> weight; default 1.0 (water-like)
DENSITY = (
    ("olive oil", 0.91), ("oil", 0.91), ("butter", 0.95), ("honey", 1.42), ("syrup", 1.35), ("treacle", 1.4),
    ("flour", 0.53), ("icing sugar", 0.5), ("caster sugar", 0.85), ("granulated sugar", 0.85), ("brown sugar", 0.9),
    ("sugar", 0.85), ("cocoa", 0.35), ("oats", 0.38), ("rice", 0.78), ("couscous", 0.73), ("quinoa", 0.72),
    ("breadcrumbs", 0.45), ("ground almonds", 0.4), ("almonds", 0.6), ("nuts", 0.6), ("seeds", 0.6),
    ("desiccated coconut", 0.35), ("peas", 0.6), ("lentils", 0.8), ("cream", 1.0), ("yoghurt", 1.03),
    ("mayonnaise", 0.95), ("tahini", 1.1), ("peanut butter", 1.1), ("mustard", 1.0), ("soy sauce", 1.1),
    ("fish sauce", 1.1), ("salt", 1.2), ("baking powder", 0.9), ("yeast", 0.6), ("spice", 0.5), ("cumin", 0.5),
    ("paprika", 0.5), ("cinnamon", 0.5), ("turmeric", 0.5), ("pepper", 0.5), ("chilli flakes", 0.4),
    ("dried herbs", 0.2), ("parmesan", 0.45), ("cheese", 0.5), ("tomato puree", 1.1), ("passata", 1.0),
)
# grams per whole item (or per unit) for counted ingredients
COUNT_WEIGHTS = (
    ("egg yolk", 18), ("egg white", 33), ("egg", 50), ("onion", 150), ("red onion", 150), ("shallot", 30),
    ("spring onion", 15), ("garlic", 5), ("leek", 200), ("carrot", 80), ("celery", 40), ("potato", 170),
    ("sweet potato", 200), ("parsnip", 120), ("beetroot", 100), ("tomato", 120), ("cherry tomato", 15),
    ("pepper", 150), ("chilli", 15), ("aubergine", 300), ("courgette", 200), ("cucumber", 300), ("mushroom", 20),
    ("lemon", 100), ("lime", 65), ("orange", 150), ("apple", 180), ("pear", 170), ("banana", 120), ("avocado", 170),
    ("peach", 150), ("plum", 65), ("kiwi", 75), ("mango", 300), ("chicken thigh", 120), ("chicken breast", 170),
    ("chicken wing", 90), ("whole chicken", 1600), ("sausage", 65), ("bacon", 30), ("rasher", 30), ("pork chop", 180),
    ("lamb chop", 100), ("steak", 225), ("fillet", 150), ("salmon", 150), ("cod", 150), ("prawn", 10),
    ("tortilla", 60), ("pitta", 60), ("naan", 130), ("bread", 40), ("slice", 40), ("biscuit", 15), ("date", 8),
    ("stock cube", 10), ("tin", 400), ("can", 400), ("bay leaf", 0.2), ("sprig", 2), ("bunch", 30), ("handful", 30),
    ("pinch", 0.5), ("dash", 2), ("knob", 15), ("clove", 5), ("stick", 40), ("stalk", 40), ("sheet", 25), ("sachet", 10),
    ("piece", 100),
)
SYNONYMS = (
    ("zucchini", "courgette"), ("cilantro", "coriander"), ("eggplant", "aubergine"), ("heavy cream", "double cream"),
    ("whipping cream", "whipping cream"), ("all-purpose flour", "plain flour"), ("all purpose flour", "plain flour"),
    ("bread flour", "strong white bread flour"), ("granulated sugar", "granulated sugar"), ("superfine sugar", "caster sugar"),
    ("powdered sugar", "icing sugar"), ("confectioners sugar", "icing sugar"), ("ground beef", "beef mince"),
    ("minced beef", "beef mince"), ("ground pork", "pork mince"), ("minced pork", "pork mince"), ("ground lamb", "lamb mince"),
    ("ground turkey", "turkey mince"), ("shrimp", "prawns"), ("scallion", "spring onion"), ("green onion", "spring onion"),
    ("bell pepper", "bell pepper"), ("capsicum", "bell pepper"), ("rutabaga", "swede"), ("arugula", "rocket"),
    ("garbanzo", "chickpeas tinned"), ("chick peas", "chickpeas"), ("corn starch", "cornflour"), ("cornstarch", "cornflour"),
    ("baking soda", "bicarbonate of soda"), ("bicarb", "bicarbonate of soda"), ("yogurt", "yoghurt"), ("greek yogurt", "greek yoghurt"),
    ("plain yoghurt", "natural yoghurt"), ("plain yogurt", "natural yoghurt"), ("tomato paste", "tomato puree"),
    ("tomato purée", "tomato puree"), ("tinned tomatoes", "chopped tomatoes"), ("canned tomatoes", "chopped tomatoes"),
    ("plum tomatoes", "chopped tomatoes"), ("crushed tomatoes", "passata"), ("mozzarella", "mozzarella"), ("cheddar cheese", "cheddar"),
    ("parmigiano", "parmesan"), ("pecorino", "parmesan"), ("grana padano", "parmesan"), ("goat's cheese", "goat cheese"),
    ("goats cheese", "goat cheese"), ("stilton", "blue cheese"), ("gorgonzola", "blue cheese"), ("roquefort", "blue cheese"),
    ("spaghetti", "pasta dry"), ("penne", "pasta dry"), ("fusilli", "pasta dry"), ("linguine", "pasta dry"), ("macaroni", "pasta dry"),
    ("tagliatelle", "pasta dry"), ("lasagne sheets", "pasta dry"), ("orzo", "pasta dry"), ("arborio", "risotto rice"),
    ("carnaroli", "risotto rice"), ("jasmine rice", "white rice dry"), ("long grain rice", "white rice dry"),
    ("cooked rice", "white rice cooked"), ("leftover rice", "white rice cooked"), ("cooked pasta", "pasta cooked"),
    ("porridge oats", "oats"), ("rolled oats", "oats"), ("jumbo oats", "oats"), ("skinless chicken thigh", "chicken thigh skinless"),
    ("chicken thigh fillets", "chicken thigh skinless"), ("boneless chicken thigh", "chicken thigh skinless"),
    ("chicken drumsticks", "chicken thigh"), ("chicken legs", "chicken thigh"), ("chicken", "chicken breast"),
    ("beef steak", "beef steak"), ("sirloin", "beef steak"), ("rump", "beef steak"), ("ribeye", "beef steak"), ("fillet steak", "beef steak"),
    ("braising steak", "stewing beef"), ("chuck", "stewing beef"), ("diced beef", "stewing beef"), ("beef", "stewing beef"),
    ("pork fillet", "pork loin"), ("pork tenderloin", "pork loin"), ("pork chops", "pork loin"), ("pork", "pork shoulder"),
    ("lamb", "lamb shoulder"), ("streaky bacon", "bacon"), ("back bacon", "bacon"), ("lardons", "pancetta"),
    ("king prawns", "prawns"), ("salmon fillet", "salmon"), ("cod fillet", "cod"), ("white fish", "cod"), ("tuna steak", "tuna"),
    ("tin of tuna", "tinned tuna"), ("tinned chickpeas", "chickpeas tinned"), ("tin chickpeas", "chickpeas tinned"),
    ("can chickpeas", "chickpeas tinned"), ("chickpeas", "chickpeas tinned"), ("red lentils", "red lentils dried"),
    ("red split lentils", "red lentils dried"), ("green lentils", "green lentils cooked"), ("brown lentils", "green lentils cooked"),
    ("puy lentils", "puy lentils cooked"), ("kidney beans", "kidney beans tinned"), ("black beans", "black beans tinned"),
    ("butter beans", "butter beans tinned"), ("cannellini", "cannellini beans tinned"), ("haricot", "cannellini beans tinned"),
    ("borlotti", "kidney beans tinned"), ("vegetable stock", "stock"), ("chicken stock", "stock"), ("beef stock", "stock"),
    ("broth", "stock"), ("bouillon", "stock cube"), ("salted butter", "butter"), ("extra virgin olive oil", "olive oil"),
    ("sunflower oil", "sunflower oil"), ("groundnut oil", "vegetable oil"), ("canola", "rapeseed oil"), ("sea salt", "salt"),
    ("flaky salt", "salt"), ("kosher salt", "salt"), ("black peppercorns", "black pepper"), ("ground black pepper", "black pepper"),
    ("white pepper", "black pepper"), ("cumin", "spice"), ("paprika", "spice"), ("turmeric", "spice"), ("cinnamon", "spice"),
    ("garam masala", "spice"), ("curry powder", "spice"), ("coriander seed", "spice"), ("ground coriander", "spice"),
    ("chilli flakes", "spice"), ("chilli powder", "spice"), ("cayenne", "spice"), ("nutmeg", "spice"), ("cardamom", "spice"),
    ("cloves", "spice"), ("star anise", "spice"), ("fennel seed", "spice"), ("mustard seed", "spice"), ("sumac", "spice"),
    ("za'atar", "spice"), ("mixed spice", "spice"), ("allspice", "spice"), ("saffron", "spice"), ("oregano", "dried herbs"),
    ("thyme", "dried herbs"), ("rosemary", "dried herbs"), ("bay", "dried herbs"), ("mixed herbs", "dried herbs"),
    ("dill", "fresh herbs"), ("chives", "fresh herbs"), ("tarragon", "fresh herbs"), ("sage", "fresh herbs"),
    ("fresh coriander", "coriander"), ("fresh parsley", "parsley"), ("fresh basil", "basil"), ("fresh mint", "mint"),
    ("instant yeast", "yeast"), ("dried yeast", "yeast"), ("fast action yeast", "yeast"), ("white wine vinegar", "vinegar"),
    ("red wine vinegar", "vinegar"), ("cider vinegar", "vinegar"), ("rice vinegar", "vinegar"), ("malt vinegar", "vinegar"),
    ("dark chocolate", "dark chocolate"), ("plain chocolate", "dark chocolate"), ("70% chocolate", "dark chocolate"),
    ("cooking chocolate", "dark chocolate"), ("milk", "whole milk"), ("cream", "double cream"), ("cheese", "cheddar"),
    ("flour", "plain flour"), ("sugar", "caster sugar"), ("oil", "vegetable oil"), ("rice", "white rice dry"),
    ("pasta", "pasta dry"), ("noodles", "egg noodles dry"), ("lentils", "red lentils dried"), ("beans", "dried beans"),
    ("tomatoes", "tomato"), ("peppers", "bell pepper"), ("mushrooms", "mushrooms"), ("nuts", "almonds"),
    ("wine", "white wine"), ("bread", "white bread"), ("stock", "stock"), ("herbs", "fresh herbs"),
)
SKIP_PREFIXES = ("optional", "to serve", "for the", "garnish", "serve with", "to taste")


@dataclass
class Line:
    raw: str
    quantity: float | None = None
    unit: str | None = None
    name: str = ""
    grams: float | None = None
    match: str | None = None
    note: str = ""
    nutrients: dict = field(default_factory=dict)


def to_number(tok: str) -> float:
    tok = tok.strip()
    for u, f in UNICODE_FRACTIONS.items():
        tok = tok.replace(u, " " + f).strip()
    return sum(float(Fraction(p)) if "/" in p else float(p.replace(",", ".")) for p in tok.split())


def parse_line(line: str) -> Line | None:
    raw = line.strip().lstrip("-*•").strip()
    if not raw or raw.lower().startswith(SKIP_PREFIXES):
        return None
    ln = Line(raw=raw)
    m = LINE_RE.match(raw)
    if m:
        q = to_number(m.group("q"))
        if m.group("qh"):
            q = (q + to_number(m.group("qh"))) / 2
        ln.quantity = q
        ln.unit = ALIAS_TO_UNIT[m.group("unit").lower()] if m.group("unit") else None
        name = m.group("name")
    else:
        v = VAGUE_RE.match(raw)
        if v:
            ln.quantity = 1.0
            ln.unit = ALIAS_TO_UNIT.get(v.group("unit").lower(), v.group("unit").lower())
            name = v.group("name")
        else:
            ln.name = raw
            return ln
    if "(" in name:
        name = name.split("(")[0]
    name = name.split(",")[0].strip()
    # "400 g tin chopped tomatoes" -> unit g, name "tin chopped tomatoes": drop a leading container word
    name = re.sub(r"^(tin|tins|can|cans|jar|packet|pack|bag)\s+(of\s+)?", "", name, flags=re.I)
    ln.name = name.strip()
    return ln


def normalise(name: str) -> str:
    n = name.lower().replace("’", "'")
    n = re.sub(r"[^\w\s'%-]", " ", n)
    n = re.sub(r"\b(finely|roughly|thinly|freshly|chopped|diced|sliced|minced|grated|crushed|peeled|cubed|shredded|halved|"
               r"quartered|beaten|melted|softened|ripe|large|medium|small|whole|boneless|skinless|skin on|skin-on|raw|warm|cold|"
               r"hot|room temperature|to taste|for serving|plus extra|extra|good quality|organic|free range|free-range|the|a|an|of)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def load_table(path: Path = TABLE_PATH) -> dict[str, dict]:
    table = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            table[row["name"]] = {k: float(row[k]) for k in NUTRIENTS} | {"category": row["category"]}
    return table


def match_name(name: str, table: dict[str, dict]) -> str | None:
    n = normalise(name)
    if not n:
        return None
    if n in table:
        return n
    # Try the lightly cleaned name first (keeps words like "chopped" that distinguish table entries),
    # then the fully normalised one. Longest key wins; an exact synonym beats everything.
    light = re.sub(r"\s+", " ", re.sub(r"[^\w\s'%-]", " ", name.lower().replace("’", "'"))).strip()
    for text in (light, n):
        candidates: list[tuple[int, str]] = []
        for key, target in SYNONYMS:
            if target in table and (text == key or re.search(rf"\b{re.escape(key)}(?:e?s)?\b", text)):
                candidates.append((len(key) + (1000 if text == key else 0), target))
        for key in table:
            if re.search(rf"\b{re.escape(key)}(?:e?s)?\b", text):
                candidates.append((len(key) + 1, key))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
    alt = n[:-1] if n.endswith("s") else n + "s"
    return alt if alt in table else None


def grams_for(ln: Line) -> tuple[float | None, str]:
    """Return (grams, note) for a parsed line."""
    q, u, n = ln.quantity, ln.unit, normalise(ln.name)
    if q is None:
        return None, "no quantity"
    if u == "g":
        return q, ""
    if u == "kg":
        return q * 1000, ""
    if u == "oz":
        return q * G_PER_OZ, ""
    if u == "lb":
        return q * G_PER_LB, ""
    if u in ML:
        density = 1.0
        for key, d in DENSITY:
            if key in n:
                density = d
                break
        return q * ML[u] * density, f"{ML[u] * q:g} ml at {density} g/ml"
    for key, w in COUNT_WEIGHTS:
        if (u and key == u) or (u in (None, "piece") and re.search(rf"\b{re.escape(key)}s?\b", n)):
            return q * w, f"assumed {w:g} g each"
    if u in ("tin", "piece", "sheet", "sachet", "bunch", "handful", "pinch", "dash", "sprig", "stick", "stalk", "slice", "clove"):
        w = dict(COUNT_WEIGHTS).get(u, 50)
        return q * w, f"assumed {w:g} g per {u}"
    return q * 100, "assumed 100 g each"


def estimate(lines: list[str], servings: float, table: dict[str, dict] | None = None) -> dict:
    table = table or load_table()
    parsed = [p for p in (parse_line(l) for l in lines) if p is not None]
    total = {k: 0.0 for k in NUTRIENTS}
    matched_g = total_g = 0.0
    assumptions, unmatched = [], []
    for ln in parsed:
        ln.grams, ln.note = grams_for(ln)
        ln.match = match_name(ln.name, table)
        if ln.grams is None:
            unmatched.append(f"'{ln.raw}': no quantity, not counted")
            continue
        total_g += ln.grams
        if ln.match is None:
            unmatched.append(f"'{ln.raw}': no table entry, not counted ({ln.grams:.0f} g)")
            continue
        matched_g += ln.grams
        ref = table[ln.match]
        ln.nutrients = {k: ref[k] * ln.grams / 100 for k in NUTRIENTS}
        for k in NUTRIENTS:
            total[k] += ln.nutrients[k]
        if ln.note.startswith("assumed"):
            assumptions.append(f"{ln.note} for '{ln.raw}'")
        if ln.match != normalise(ln.name):
            assumptions.append(f"'{ln.raw}' read as {ln.match}")
    servings = max(float(servings), 1e-9)
    per = {k: total[k] / servings for k in NUTRIENTS}
    share = matched_g / total_g if total_g else 0.0
    return {"servings": servings, "per_serving": per, "per_recipe": total, "matched_share": share,
            "total_grams": total_g, "assumptions": assumptions, "unmatched": unmatched,
            "lines": [{"raw": l.raw, "grams": l.grams, "match": l.match, "note": l.note} for l in parsed]}


def _r(v: float, k: str) -> str:
    if k == "kcal":
        return f"{round(v / 5) * 5:.0f}" if v >= 50 else f"{v:.0f}"
    if k == "salt_g":
        return f"{v:.2f}" if v < 1 else f"{v:.1f}"
    return f"{v:.1f}" if v < 10 else f"{v:.0f}"


LABELS = {"kcal": "Energy (kcal)", "protein_g": "Protein (g)", "fat_g": "Fat (g)", "saturates_g": "of which saturates (g)",
          "carbs_g": "Carbohydrate (g)", "sugars_g": "of which sugars (g)", "fibre_g": "Fibre (g)", "salt_g": "Salt (g)"}


def render(result: dict) -> str:
    out = [f"**Estimate** per serving ({result['servings']:g} servings, about {result['total_grams'] / result['servings']:.0f} g each)", "",
           "| | Per serving | Whole recipe |", "| --- | --- | --- |"]
    for k in NUTRIENTS:
        out.append(f"| {LABELS[k]} | {_r(result['per_serving'][k], k)} | {_r(result['per_recipe'][k], k)} |")
    out.append("")
    out.append(f"Matched {result['matched_share'] * 100:.0f}% of the recipe weight against the reference table." +
               (" Treat the figures as rough." if result["matched_share"] < 0.8 else ""))
    if result["assumptions"]:
        out += ["", "**Assumed**"] + [f"- {a}" for a in result["assumptions"]]
    if result["unmatched"]:
        out += ["", "**Not counted**"] + [f"- {u}" for u in result["unmatched"]]
    out += ["", "Figures are estimates from typical composition values for raw ingredients; cooking losses, brands and trimming change them."]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="ingredient lines; default stdin")
    ap.add_argument("--servings", type=float, required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.servings <= 0:
        ap.error("servings must be positive")
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        print("No ingredient lines found.", file=sys.stderr)
        return 1
    result = estimate(lines, a.servings)
    print(json.dumps(result, indent=2, ensure_ascii=False) if a.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
