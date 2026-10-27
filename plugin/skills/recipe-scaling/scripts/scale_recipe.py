#!/usr/bin/env python3
"""Scale a recipe's ingredient lines and optionally convert units.

Usage:
  python3 scale_recipe.py --from 4 --to 6 ingredients.txt
  python3 scale_recipe.py --factor 0.5 --units us ingredients.txt
  cat ingredients.txt | python3 scale_recipe.py --factor 2 --json

One ingredient per line, e.g. "250 g strong white bread flour", "1½ tsp salt",
"2 eggs", "1-2 cloves garlic", "a pinch of nutmeg". Lines that cannot be parsed
are passed through unchanged and reported. Python 3.10+, standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict, field
from fractions import Fraction

UNICODE_FRACTIONS = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3",
                     "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}

# canonical unit -> (aliases, kind)   kind: weight | volume | spoon | count | vague
UNITS: dict[str, tuple[tuple[str, ...], str]] = {
    "g": (("g", "gram", "grams", "gr"), "weight"),
    "kg": (("kg", "kilogram", "kilograms", "kilo", "kilos"), "weight"),
    "oz": (("oz", "ounce", "ounces"), "weight"),
    "lb": (("lb", "lbs", "pound", "pounds"), "weight"),
    "ml": (("ml", "millilitre", "millilitres", "milliliter", "milliliters"), "volume"),
    "l": (("l", "litre", "litres", "liter", "liters"), "volume"),
    "fl oz": (("fl oz", "fl. oz", "fl.oz", "fluid ounce", "fluid ounces"), "volume"),
    "cup": (("cup", "cups", "c"), "volume"),
    "tsp": (("tsp", "tsps", "teaspoon", "teaspoons"), "spoon"),
    "tbsp": (("tbsp", "tbsps", "tbs", "tablespoon", "tablespoons"), "spoon"),
    "pinch": (("pinch", "pinches"), "vague"),
    "handful": (("handful", "handfuls"), "vague"),
    "dash": (("dash", "dashes", "splash", "glug", "drizzle"), "vague"),
    "clove": (("clove", "cloves"), "count"),
    "slice": (("slice", "slices"), "count"),
    "sprig": (("sprig", "sprigs"), "count"),
    "stick": (("stick", "sticks"), "count"),
    "tin": (("tin", "tins", "can", "cans"), "count"),
    "bunch": (("bunch", "bunches"), "count"),
    "piece": (("piece", "pieces"), "count"),
    "sheet": (("sheet", "sheets"), "count"),
    "sachet": (("sachet", "sachets", "packet", "packets", "pack", "packs"), "count"),
}
ALIAS_TO_UNIT = {a: u for u, (aliases, _) in UNITS.items() for a in aliases}
UNIT_PATTERN = "|".join(sorted((re.escape(a) for a in ALIAS_TO_UNIT), key=len, reverse=True))

# seasoning-type ingredients that should not scale linearly for large factors
TASTE_WORDS = ("salt", "yeast", "baking powder", "bicarbonate", "baking soda", "chilli", "chili",
               "cayenne", "pepper", "vanilla", "extract", "vinegar", "soy", "fish sauce", "stock cube",
               "bouillon", "curry powder", "garam masala", "cinnamon", "nutmeg", "clove", "cumin",
               "paprika", "turmeric", "saffron", "mustard", "worcestershire", "hot sauce", "sriracha",
               "harissa", "zest")
LEAVENING_WORDS = ("yeast", "baking powder", "bicarbonate", "baking soda")
COUNT_WORDS = ("egg", "eggs", "onion", "onions", "lemon", "lemons", "lime", "limes", "apple", "apples",
               "potato", "potatoes", "carrot", "carrots", "pepper", "peppers", "chicken thigh",
               "chicken thighs", "chicken breast", "chicken breasts", "fillet", "fillets", "tortilla",
               "tortillas", "bay leaf", "bay leaves", "banana", "bananas", "courgette", "courgettes",
               "aubergine", "aubergines", "sausage", "sausages", "steak", "steaks", "shallot", "shallots")

G_PER_OZ = 28.349523125
G_PER_LB = 453.59237
ML_PER_CUP = 240.0
ML_PER_FLOZ = 29.5735295625
ML_PER_TBSP = 15.0
ML_PER_TSP = 5.0

# grams per US cup for common dry ingredients (used only for cup <-> gram)
DENSITY_G_PER_CUP = (
    ("icing sugar", 120), ("powdered sugar", 120), ("brown sugar", 220), ("caster sugar", 200),
    ("granulated sugar", 200), ("sugar", 200), ("plain flour", 125), ("all-purpose flour", 125),
    ("bread flour", 127), ("strong white", 127), ("wholemeal", 120), ("whole wheat", 120),
    ("self-raising", 125), ("flour", 125), ("butter", 227), ("rice", 185), ("rolled oats", 90),
    ("oats", 90), ("cocoa", 85), ("honey", 340), ("golden syrup", 340), ("maple syrup", 320),
    ("ground almonds", 96), ("almond flour", 96), ("cornflour", 128), ("cornstarch", 128),
    ("breadcrumbs", 110), ("desiccated coconut", 85), ("lentils", 190), ("couscous", 175),
    ("quinoa", 170), ("chocolate chips", 170), ("grated cheese", 100), ("parmesan", 100),
    ("peas", 145), ("water", 240), ("milk", 240), ("cream", 240), ("yoghurt", 245), ("yogurt", 245),
    ("oil", 220), ("stock", 240), ("wine", 240), ("juice", 240),
)
LIQUID_WORDS = ("water", "milk", "cream", "stock", "broth", "wine", "juice", "oil", "vinegar", "beer",
                "coconut milk", "buttermilk", "sauce", "syrup", "honey", "yoghurt", "yogurt")


@dataclass
class Ingredient:
    raw: str
    quantity: float | None = None
    quantity_high: float | None = None   # for ranges like 1-2
    unit: str | None = None
    name: str = ""
    note: str = ""                       # anything after a comma or in brackets
    parsed: bool = True
    scaled_quantity: float | None = None
    scaled_quantity_high: float | None = None
    scaled_unit: str | None = None
    flags: list[str] = field(default_factory=list)

    def display(self) -> str:
        if not self.parsed:
            return self.raw
        q = fmt_quantity(self.scaled_quantity, self.scaled_unit)
        top = self.scaled_quantity
        if self.scaled_quantity_high is not None:
            q = f"{q}-{fmt_quantity(self.scaled_quantity_high, self.scaled_unit)}"
            top = self.scaled_quantity_high
        unit = plural_unit(self.scaled_unit, top)
        name = plural_name(self.name, top) if self.scaled_unit is None else self.name
        parts = [p for p in (q, unit, name) if p]
        text = " ".join(parts)
        if self.note:
            text += f", {self.note}"
        return text


PLURAL_UNITS = {"clove": "cloves", "cup": "cups", "tin": "tins", "slice": "slices", "sprig": "sprigs",
                "stick": "sticks", "bunch": "bunches", "piece": "pieces", "sheet": "sheets",
                "sachet": "sachets", "pinch": "pinches", "handful": "handfuls", "dash": "dashes"}


def plural_unit(unit: str | None, q: float | None) -> str | None:
    if unit is None or q is None:
        return unit
    if q == 1:
        return unit
    return PLURAL_UNITS.get(unit, unit)


def plural_name(name: str, q: float | None) -> str:
    """Singularise a bare countable ('2 eggs' -> '1 egg') or pluralise ('1 egg' -> '3 eggs')."""
    if q is None:
        return name
    words = name.split()
    if not words:
        return name
    head, rest = words[0], words[1:]
    lower = head.lower()
    if q == 1 and lower.endswith("s") and (lower[:-1] in COUNT_WORDS or lower[:-2] + "y" in COUNT_WORDS and lower.endswith("ies")):
        head = lower[:-3] + "y" if lower.endswith("ies") else head[:-1]
    elif q != 1 and not lower.endswith("s") and lower in COUNT_WORDS:
        head = head[:-1] + "ies" if lower.endswith("y") else head + "s"
    return " ".join([head] + rest)


def to_number(token: str) -> float:
    token = token.strip()
    for u, f in UNICODE_FRACTIONS.items():
        token = token.replace(u, " " + f).strip()
    total = 0.0
    for part in token.split():
        if "/" in part:
            total += float(Fraction(part))
        else:
            total += float(part.replace(",", "."))
    return total


NUMBER = r"(?:\d*\s?[½¼¾⅓⅔⅛⅜⅝⅞]|\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
LINE_RE = re.compile(
    rf"^\s*(?P<q>{NUMBER})(?:\s*(?:-|–|to)\s*(?P<qh>{NUMBER}))?\s*(?:x\s*)?"
    rf"(?:(?P<unit>{UNIT_PATTERN})\b\.?\s*)?(?:of\s+)?(?P<name>.+?)\s*$",
    re.IGNORECASE,
)
VAGUE_RE = re.compile(rf"^\s*(?:a|an|one)\s+(?P<unit>pinch|handful|dash|splash|glug|drizzle|few|little)\s+(?:of\s+)?(?P<name>.+?)\s*$",
                      re.IGNORECASE)


def parse_line(line: str) -> Ingredient:
    raw = line.strip().lstrip("-*•").strip()
    ing = Ingredient(raw=raw)
    if not raw:
        ing.parsed = False
        return ing
    name_part = raw
    m = LINE_RE.match(raw)
    if m:
        ing.quantity = to_number(m.group("q"))
        ing.quantity_high = to_number(m.group("qh")) if m.group("qh") else None
        unit = m.group("unit")
        ing.unit = ALIAS_TO_UNIT[unit.lower()] if unit else None
        name_part = m.group("name")
    else:
        v = VAGUE_RE.match(raw)
        if v:
            ing.quantity = 1.0
            ing.unit = ALIAS_TO_UNIT.get(v.group("unit").lower(), "pinch")
            name_part = v.group("name")
        else:
            ing.parsed = False
            return ing
    # split off notes after a comma or in brackets
    note = ""
    if "(" in name_part and name_part.endswith(")"):
        name_part, _, inner = name_part.rpartition("(")
        note = inner.rstrip(")").strip()
    if "," in name_part:
        name_part, _, after = name_part.partition(",")
        note = (after.strip() + ("; " + note if note else "")).strip("; ")
    ing.name = name_part.strip()
    ing.note = note
    return ing


def is_taste(ing: Ingredient) -> bool:
    n = ing.name.lower()
    if ing.unit in ("g", "kg", "ml", "l", "cup", "oz", "lb") and ing.quantity and ing.quantity >= 100:
        return False  # 200 g of peppers is a vegetable, not a seasoning
    return any(w in n for w in TASTE_WORDS)


def is_count(ing: Ingredient) -> bool:
    if ing.unit in ("clove", "slice", "sprig", "stick", "tin", "bunch", "piece", "sheet", "sachet"):
        return True
    if ing.unit is None:
        n = ing.name.lower()
        return any(n.startswith(w) or f" {w}" in f" {n}" for w in COUNT_WORDS) or True
    return False


def _round(x: float) -> int:
    return math.floor(x + 0.5)


def round_quantity(q: float, unit: str | None, countable: bool) -> float:
    if unit in ("pinch", "handful", "dash"):
        return float(max(1, _round(q)))
    if countable or unit in ("tin", "clove", "slice", "sprig", "stick", "bunch", "piece", "sheet", "sachet"):
        return round(q * 2) / 2
    if unit in ("tsp", "tbsp"):
        return round(q * 4) / 4
    if unit == "cup":
        return round(q * 8) / 8
    if unit in ("g", "ml"):
        if q < 10:
            return round(q * 2) / 2
        if q < 100:
            return float(_round(q))
        if q < 1000:
            return float(_round(q / 5) * 5)
        return float(_round(q / 10) * 10)
    if unit in ("kg", "l"):
        return round(q, 2)
    if unit in ("oz", "fl oz"):
        return round(q * 4) / 4
    if unit == "lb":
        return round(q * 8) / 8
    return round(q * 2) / 2


def fmt_quantity(q: float | None, unit: str | None) -> str:
    if q is None:
        return ""
    if unit in ("tsp", "tbsp", "cup", "oz", "fl oz", "lb") or unit is None or unit in ("tin", "clove", "slice", "sprig", "stick", "bunch", "piece", "sheet", "sachet", "pinch", "handful", "dash"):
        whole = int(q)
        frac = Fraction(q - whole).limit_denominator(8)
        if frac == 0:
            return str(whole)
        sym = {Fraction(1, 2): "½", Fraction(1, 4): "¼", Fraction(3, 4): "¾", Fraction(1, 3): "⅓",
               Fraction(2, 3): "⅔", Fraction(1, 8): "⅛", Fraction(3, 8): "⅜", Fraction(5, 8): "⅝",
               Fraction(7, 8): "⅞"}.get(frac, str(frac))
        return f"{whole}{sym}" if whole else sym
    if float(q).is_integer():
        return str(int(q))
    return f"{q:.2f}".rstrip("0").rstrip(".")


def density_for(name: str) -> float | None:
    n = name.lower()
    for key, g in DENSITY_G_PER_CUP:
        if key in n:
            return float(g)
    return None


def convert_units(ing: Ingredient, target: str) -> None:
    """Convert ing.scaled_quantity/unit in place to metric or us."""
    q, u = ing.scaled_quantity, ing.scaled_unit
    if q is None or u is None:
        return
    qh = ing.scaled_quantity_high

    def apply(factor: float, new_unit: str) -> None:
        ing.scaled_quantity = q * factor
        ing.scaled_quantity_high = qh * factor if qh is not None else None
        ing.scaled_unit = new_unit

    if target == "metric":
        if u == "oz":
            apply(G_PER_OZ, "g")
        elif u == "lb":
            apply(G_PER_LB, "g")
        elif u == "fl oz":
            apply(ML_PER_FLOZ, "ml")
        elif u == "cup":
            d = density_for(ing.name)
            if d is not None and not any(w in ing.name.lower() for w in LIQUID_WORDS):
                apply(d, "g")
                ing.flags.append("cups converted by weight using a standard density")
            else:
                apply(ML_PER_CUP, "ml")
    elif target == "us":
        if u == "kg":
            apply(1000 / G_PER_LB, "lb")
        elif u == "g":
            d = density_for(ing.name)
            if d is not None and not any(w in ing.name.lower() for w in LIQUID_WORDS) and q >= 30:
                apply(1 / d, "cup")
                ing.flags.append("grams converted to cups using a standard density; weigh if precision matters")
            else:
                apply(1 / G_PER_OZ, "oz")
        elif u == "l":
            apply(1000 / ML_PER_CUP, "cup")
        elif u == "ml":
            if q >= 60:
                apply(1 / ML_PER_CUP, "cup")
            elif q >= 15:
                apply(1 / ML_PER_TBSP, "tbsp")
            else:
                apply(1 / ML_PER_TSP, "tsp")


def scale(ingredients: list[Ingredient], factor: float, units: str | None = None) -> list[Ingredient]:
    strong = factor > 2.0 or factor < 0.5
    for ing in ingredients:
        if not ing.parsed or ing.quantity is None:
            continue
        f = factor
        taste = is_taste(ing)
        if taste and strong:
            f = factor ** 0.8
            ing.flags.append("seasoning scaled by factor^0.8; adjust to taste")
        if any(w in ing.name.lower() for w in LEAVENING_WORDS) and factor != 1.0:
            ing.flags.append("leavening: re-check against the flour weight (about 1 tsp baking powder per 100 g flour; 7 g instant yeast per 500 g flour)")
        ing.scaled_quantity = ing.quantity * f
        ing.scaled_quantity_high = ing.quantity_high * f if ing.quantity_high is not None else None
        ing.scaled_unit = ing.unit
        if units:
            convert_units(ing, units)
        countable = ing.unit is None or is_count(ing)
        before = ing.scaled_quantity
        ing.scaled_quantity = round_quantity(ing.scaled_quantity, ing.scaled_unit, countable)
        if ing.scaled_quantity_high is not None:
            ing.scaled_quantity_high = round_quantity(ing.scaled_quantity_high, ing.scaled_unit, countable)
        if ing.scaled_quantity == 0:
            ing.scaled_quantity = 0.5 if countable or ing.scaled_unit in ("tsp", "tbsp", "cup") else 1.0
            ing.flags.append("rounded up to the smallest usable amount")
        elif abs(before - ing.scaled_quantity) / max(before, 1e-9) > 0.08:
            ing.flags.append(f"rounded from {before:.2f}")
        if ing.unit is None and "egg" in ing.name.lower() and not float(ing.scaled_quantity).is_integer():
            ing.flags.append("half an egg: whisk one egg and use half, about 25 g")
        if ing.unit in ("pinch", "handful", "dash"):
            ing.flags.append("vague unit; scaled by count, taste as you go")
    return ingredients


def method_notes(factor: float) -> list[str]:
    notes = []
    if factor == 1.0:
        return notes
    d = math.sqrt(factor)
    notes.append(f"Pan or tin area scales with the factor: a round tin's diameter × {d:.2f} (20 cm → {20 * d:.0f} cm, 23 cm → {23 * d:.0f} cm). Same tin → deeper mixture → longer bake.")
    notes.append("Cooking times do not scale with quantity. Same thickness or depth → similar time; deeper or more crowded → longer. Start checking at the original time and use the doneness cue.")
    if factor > 1.5:
        notes.append("On the hob, cook in batches rather than crowding the pan, or the food steams instead of browning.")
    if factor < 0.5:
        notes.append("Small quantities dry out and catch faster: drop the heat a notch and check early.")
    if factor > 2.0 or factor < 0.5:
        notes.append("Seasoning, chilli and leavening were scaled less than linearly; taste and adjust before serving.")
    return notes


def render_markdown(ings: list[Ingredient], factor: float, from_s: float | None, to_s: float | None, units: str | None) -> str:
    head = f"Scaled ×{factor:g}" + (f", {from_s:g} → {to_s:g} servings" if from_s and to_s else "")
    if units:
        head += f", units: {units}"
    out = [head, "", "**You'll need**"]
    for ing in ings:
        out.append(f"- {ing.display()}")
    adjusted = [(ing, ing.flags) for ing in ings if ing.flags]
    unparsed = [ing.raw for ing in ings if not ing.parsed and ing.raw]
    if adjusted:
        out += ["", "**Adjusted by hand**"]
        for ing, flags in adjusted:
            out.append(f"- {ing.name or ing.raw}: " + "; ".join(flags))
    if unparsed:
        out += ["", "**Not scaled (could not parse; check by hand)**"]
        out += [f"- {u}" for u in unparsed]
    notes = method_notes(factor)
    if notes:
        out += ["", "**Method notes**"] + [f"- {n}" for n in notes]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="ingredient lines; default stdin")
    ap.add_argument("--from", dest="from_s", type=float, help="current servings")
    ap.add_argument("--to", dest="to_s", type=float, help="target servings")
    ap.add_argument("--factor", type=float, help="scale factor (alternative to --from/--to)")
    ap.add_argument("--units", choices=("metric", "us"), help="convert units")
    ap.add_argument("--json", action="store_true", help="JSON output")
    a = ap.parse_args(argv)
    if a.factor is None:
        if not (a.from_s and a.to_s):
            ap.error("give --factor, or both --from and --to")
        if a.from_s <= 0 or a.to_s <= 0:
            ap.error("servings must be positive")
        factor = a.to_s / a.from_s
    else:
        if a.factor <= 0:
            ap.error("factor must be positive")
        factor = a.factor
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    ings = [parse_line(l) for l in text.splitlines() if l.strip()]
    if not ings:
        print("No ingredient lines found.", file=sys.stderr)
        return 1
    scale(ings, factor, a.units)
    if a.json:
        print(json.dumps({"factor": factor, "units": a.units, "ingredients": [asdict(i) | {"display": i.display()} for i in ings],
                          "method_notes": method_notes(factor)}, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(ings, factor, a.from_s, a.to_s, a.units))
    return 0


if __name__ == "__main__":
    sys.exit(main())
