#!/usr/bin/env python3
"""Rank dishes from the fridge-to-meal library against what the user has.

Usage:
  python3 dish_match.py inventory.txt
  python3 dish_match.py inventory.txt --max-minutes 30 --tag vegetarian --exclude peanut --top 5
  python3 dish_match.py inventory.txt --no-pantry --json

inventory.txt: one ingredient per line, free text ("half a cabbage", "6 eggs",
"tinned chopped tomatoes"). Lines are normalised to keywords; quantities, prep
words and plurals are stripped and common synonyms are mapped. Dishes come from
../references/dishes.json (override with --library). Python 3.10+, stdlib only.

Scoring: coverage of a dish's core ingredients (weight 1.0) plus optional ones
(0.3), divided by the maximum possible. Pantry items (oil, salt, onion, spices)
are assumed present unless --no-pantry. Ties are broken by how many perishable
"uses_up" items the dish clears, then by time.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_LIBRARY = Path(__file__).resolve().parent.parent / "references" / "dishes.json"

UNICODE_FRACTIONS = "½¼¾⅓⅔⅛⅜⅝⅞"
QUANTITY_WORDS = {"half", "quarter", "a", "an", "one", "two", "three", "four", "five", "six", "some", "few", "bit",
                  "couple", "handful", "bunch", "pack", "packet", "bag", "box", "jar", "bottle", "tin", "can", "cup",
                  "cups", "g", "kg", "ml", "l", "oz", "lb", "lbs", "tbsp", "tsp", "slice", "slices", "piece", "pieces",
                  "clove", "cloves", "head", "heads", "stick", "sticks", "leftover", "leftovers", "of", "the", "and",
                  "about", "roughly", "large", "small", "medium", "big", "little"}
PREP_WORDS = {"chopped", "diced", "sliced", "grated", "fresh", "frozen", "cooked", "raw", "ripe", "overripe", "old",
              "stale", "open", "opened", "wilting", "wilted", "leftover", "whole", "skinless", "boneless", "dried",
              "ground", "crushed", "minced", "peeled", "baby", "organic", "free-range", "unsalted", "salted", "plain",
              "natural", "greek", "full-fat", "semi-skimmed", "skimmed", "mature", "extra", "virgin", "soft", "hard",
              "jarred", "canned", "tinned", "smoked", "roast", "roasted", "mixed", "chunky", "cherry", "plum", "new",
              "red", "white", "green", "yellow", "brown", "black", "spring", "sweet"}
# words that stay as part of a compound even though they are in PREP_WORDS or QUANTITY_WORDS
COMPOUNDS = {
    "spring onion": "spring onion", "scallion": "spring onion", "green onion": "spring onion",
    "red onion": "red onion", "tinned tomato": "tinned tomato", "canned tomato": "tinned tomato",
    "chopped tomato": "tinned tomato", "plum tomato": "tinned tomato", "passata": "tinned tomato",
    "cherry tomato": "tomato", "tomato puree": "tomato puree", "tomato paste": "tomato puree",
    "tinned chickpea": "tinned chickpea", "canned chickpea": "tinned chickpea", "chickpea": "tinned chickpea",
    "garbanzo": "tinned chickpea", "tinned bean": "tinned bean", "baked bean": "tinned bean", "cannellini": "tinned bean",
    "butter bean": "tinned bean", "haricot": "tinned bean", "borlotti": "tinned bean", "tinned kidney bean": "tinned kidney bean",
    "kidney bean": "tinned kidney bean", "tinned black bean": "tinned black bean", "black bean": "tinned black bean",
    "tinned tuna": "tinned tuna", "canned tuna": "tinned tuna", "tuna": "tinned tuna",
    "chicken thigh": "chicken thigh", "chicken leg": "chicken thigh", "chicken drumstick": "chicken thigh",
    "chicken breast": "chicken breast", "chicken fillet": "chicken breast", "whole chicken": "whole chicken",
    "minced beef": "minced beef", "beef mince": "minced beef", "ground beef": "minced beef",
    "minced pork": "minced pork", "pork mince": "minced pork", "ground pork": "minced pork",
    "minced lamb": "minced lamb", "lamb mince": "minced lamb", "ground lamb": "minced lamb",
    "stewing beef": "stewing beef", "braising steak": "stewing beef", "chuck": "stewing beef", "beef shin": "stewing beef",
    "roast meat": "roast meat", "leftover chicken": "roast meat", "roast chicken": "roast meat", "roast beef": "roast meat",
    "roast lamb": "roast meat", "roast pork": "roast meat",
    "white fish": "white fish", "cod": "white fish", "haddock": "white fish", "pollock": "white fish", "hake": "white fish",
    "smoked haddock": "smoked haddock", "egg white": "egg white", "egg yolk": "egg yolk",
    "egg noodle": "egg noodle", "rice noodle": "rice noodle", "noodle": "egg noodle", "rice paper": "rice paper",
    "lasagne sheet": "lasagne sheet", "lasagna sheet": "lasagne sheet", "spaghetti": "pasta", "penne": "pasta",
    "fusilli": "pasta", "macaroni": "pasta", "linguine": "pasta", "tagliatelle": "pasta", "rigatoni": "pasta", "orzo": "pasta",
    "puff pastry": "puff pastry", "filo": "filo pastry", "filo pastry": "filo pastry", "phyllo": "filo pastry",
    "coconut milk": "coconut milk", "coconut cream": "coconut milk", "sour cream": "sour cream", "creme fraiche": "sour cream",
    "crème fraîche": "sour cream", "double cream": "cream", "single cream": "cream", "whipping cream": "cream", "heavy cream": "cream",
    "cream cheese": "cheese", "cheddar": "cheese", "gruyere": "cheese", "gruyère": "cheese", "emmental": "cheese",
    "parmesan": "parmesan", "parmigiano": "parmesan", "grana padano": "parmesan", "pecorino": "pecorino",
    "greek yoghurt": "yoghurt", "greek yogurt": "yoghurt", "yogurt": "yoghurt", "natural yoghurt": "yoghurt",
    "sweet potato": "sweet potato", "yam": "sweet potato", "new potato": "potato", "baking potato": "potato",
    "green bean": "green bean", "french bean": "green bean", "runner bean": "green bean", "bean sprout": "bean sprout",
    "beansprout": "bean sprout", "pea": "pea", "frozen pea": "pea", "petit pois": "pea", "garden pea": "pea",
    "red pepper": "pepper", "green pepper": "pepper", "yellow pepper": "pepper", "bell pepper": "pepper", "capsicum": "pepper",
    "sweet pepper": "pepper", "chili": "chilli", "chile": "chilli", "jalapeno": "chilli", "jalapeño": "chilli",
    "scotch bonnet": "scotch bonnet", "habanero": "scotch bonnet", "chilli flake": "chilli flake", "chili flake": "chilli flake",
    "red pepper flake": "chilli flake", "chilli powder": "chilli powder", "chili powder": "chilli powder",
    "courgette": "courgette", "zucchini": "courgette", "aubergine": "aubergine", "eggplant": "aubergine",
    "coriander": "coriander", "cilantro": "coriander", "coriander seed": "coriander seed", "ground coriander": "coriander seed",
    "rocket": "lettuce", "arugula": "lettuce", "salad leaf": "lettuce", "salad leaves": "lettuce", "mixed leaf": "lettuce",
    "spinach": "spinach", "baby spinach": "spinach", "kale": "kale", "cavolo nero": "kale", "chard": "spinach", "pak choi": "cabbage",
    "bok choy": "cabbage", "savoy": "cabbage", "red cabbage": "cabbage", "chinese cabbage": "cabbage", "napa": "cabbage",
    "brussels sprout": "sprout", "sprout": "sprout", "swede": "parsnip", "turnip": "parsnip", "rutabaga": "parsnip",
    "spring green": "cabbage", "lemon grass": "lemongrass", "lime leaf": "lime", "limes": "lime",
    "soy sauce": "soy", "tamari": "soy", "fish sauce": "fish sauce", "oyster sauce": "soy", "sesame oil": "sesame oil",
    "olive oil": "oil", "vegetable oil": "oil", "sunflower oil": "oil", "rapeseed oil": "oil", "canola oil": "oil",
    "stock cube": "stock", "bouillon": "stock", "broth": "stock", "chicken stock": "stock", "vegetable stock": "stock",
    "beef stock": "stock", "red wine": "red wine", "white wine": "white wine", "wine": "white wine",
    "plain flour": "flour", "all-purpose flour": "flour", "all purpose flour": "flour", "bread flour": "flour",
    "self-raising flour": "flour", "self raising flour": "flour", "cornflour": "cornflour", "cornstarch": "cornflour",
    "caster sugar": "sugar", "granulated sugar": "sugar", "brown sugar": "sugar", "icing sugar": "sugar",
    "baking powder": "baking powder", "bicarbonate of soda": "baking powder", "baking soda": "baking powder",
    "peanut butter": "peanut butter", "ground nut": "peanut", "groundnut": "peanut", "sesame seed": "sesame seed",
    "pine nut": "pine nut", "walnut": "walnut", "almond": "almond", "cashew": "cashew",
    "curry powder": "curry powder", "garam masala": "garam masala", "green curry paste": "green curry paste",
    "red curry paste": "red curry paste", "thai curry paste": "green curry paste", "curry paste": "red curry paste",
    "smoked paprika": "smoked paprika", "paprika": "paprika", "cumin seed": "cumin", "ground cumin": "cumin",
    "mustard seed": "mustard seed", "dijon": "mustard", "wholegrain mustard": "mustard", "english mustard": "mustard",
    "bay leaf": "bay leaf", "bay leaves": "bay leaf", "mixed herb": "herb", "dried herb": "herb", "herbs": "herb",
    "fresh herb": "herb", "spring greens": "cabbage", "mixed veg": "mixed vegetable", "mixed vegetable": "mixed vegetable",
    "frozen veg": "mixed vegetable", "vegetables": "mixed vegetable", "veg": "mixed vegetable",
    "bread roll": "bun", "burger bun": "bun", "brioche bun": "bun", "sourdough": "bread", "baguette": "bread", "loaf": "bread",
    "toast": "bread", "pita": "pitta", "pitta bread": "pitta", "flatbread": "pitta", "wrap": "tortilla", "tortilla wrap": "tortilla",
    "tortilla chip": "tortilla chip", "nacho": "tortilla chip", "pancetta": "pancetta", "lardon": "bacon", "streaky bacon": "bacon",
    "back bacon": "bacon", "gammon": "ham", "prosciutto": "ham", "chorizo": "chorizo", "salami": "chorizo",
    "prawn": "prawn", "shrimp": "prawn", "king prawn": "prawn", "salmon fillet": "salmon", "smoked salmon": "salmon",
    "tofu": "tofu", "bean curd": "tofu", "paneer": "paneer", "halloumi": "halloumi", "feta": "feta", "mozzarella": "mozzarella",
    "blue cheese": "blue cheese", "stilton": "blue cheese", "gorgonzola": "blue cheese", "roquefort": "blue cheese",
    "kimchi": "kimchi", "sauerkraut": "sauerkraut", "gochujang": "gochujang", "doubanjiang": "doubanjiang",
    "miso": "miso", "miso paste": "miso", "tahini": "tahini", "hummus": "hummus", "houmous": "hummus",
    "tamarind": "tamarind", "tamarind paste": "tamarind", "tomatillo": "tomatillo", "chipotle": "chipotle",
    "pomegranate molasses": "pomegranate molasses", "maple syrup": "maple syrup", "golden syrup": "maple syrup",
    "honey": "honey", "chocolate chip": "chocolate chip", "chocolate": "chocolate chip", "oats": "oat", "porridge oat": "oat",
    "rolled oat": "oat", "berries": "berry", "blueberries": "blueberry", "blueberry": "blueberry", "strawberries": "berry",
    "strawberry": "berry", "raspberries": "berry", "raspberry": "berry", "apples": "apple", "bananas": "banana",
    "potatoes": "potato", "tomatoes": "tomato", "chillies": "chilli", "lentils": "lentil", "red lentil": "lentil",
    "green lentil": "lentil", "puy lentil": "lentil", "rice cake": "rice cake", "tteok": "rice cake", "basmati": "rice",
    "jasmine rice": "rice", "long grain rice": "rice", "risotto rice": "rice", "arborio": "rice", "bomba": "rice",
    "cooked rice": "rice", "leftover rice": "rice", "short grain rice": "rice", "sushi rice": "rice",
    "whole milk": "milk", "oat milk": "milk", "soya milk": "milk", "soy milk": "milk", "almond milk": "milk",
    "sour milk": "milk", "buttermilk": "milk", "marmalade": "marmalade", "jam": "marmalade", "raisin": "raisin", "sultana": "raisin",
    "currant": "raisin", "dried fruit": "raisin", "prune": "prune", "seaweed": "seaweed", "nori": "seaweed",
    "wakame": "seaweed", "dashi": "dashi", "mirin": "mirin", "sake": "mirin", "sichuan pepper": "sichuan pepper",
    "szechuan pepper": "sichuan pepper", "star anise": "star anise", "allspice": "allspice", "pimento": "allspice",
    "galangal": "galangal", "ginger": "ginger", "turmeric": "turmeric", "cinnamon": "cinnamon", "nutmeg": "nutmeg",
    "cardamom": "cardamom", "saffron": "saffron", "sumac": "sumac", "berbere": "berbere", "injera": "injera",
    "worcestershire": "worcestershire sauce", "worcester sauce": "worcestershire sauce", "ketchup": "tinned tomato",
    "mayo": "mayonnaise", "mayonnaise": "mayonnaise", "vinegar": "vinegar", "balsamic": "vinegar", "lemons": "lemon",
    "lemon juice": "lemon", "lime juice": "lime", "orange": "orange", "apple sauce": "apple sauce", "spam": "spam",
    "black pudding": "black pudding", "perilla": "perilla", "shiso": "perilla", "horseradish": "horseradish",
    "marjoram": "marjoram", "caraway": "caraway", "fennel seed": "fennel seed", "fennel": "fennel", "dill": "dill",
    "mint": "mint", "basil": "basil", "thai basil": "basil", "parsley": "parsley", "chive": "chive", "chives": "chive",
    "thyme": "thyme", "rosemary": "rosemary", "sage": "sage", "oregano": "oregano", "tarragon": "tarragon",
    "curry leaf": "curry leaf", "curry leaves": "curry leaf", "lemongrass": "lemongrass", "sour rye starter": "sour rye starter",
    "zakwas": "sour rye starter", "anchovy": "anchovy", "anchovies": "anchovy", "olive": "olive", "olives": "olive",
    "caper": "caper", "capers": "caper", "pickle": "pickle", "gherkin": "pickle", "cucumber": "cucumber", "radish": "radish",
    "radishes": "radish", "celery": "celery", "carrot": "carrot", "carrots": "carrot", "leek": "leek", "leeks": "leek",
    "mushroom": "mushroom", "mushrooms": "mushroom", "broccoli": "broccoli", "cauliflower": "cauliflower", "lettuce": "lettuce",
    "avocado": "avocado", "avocados": "avocado", "sausage": "sausage", "sausages": "sausage", "ham": "ham", "bacon": "bacon",
    "egg": "egg", "eggs": "egg", "butter": "butter", "milk": "milk", "cream": "cream", "cheese": "cheese", "bread": "bread",
    "flour": "flour", "sugar": "sugar", "rice": "rice", "pasta": "pasta", "potato": "potato", "onion": "onion", "onions": "onion",
    "garlic": "garlic", "lemon": "lemon", "lime": "lime", "tomato": "tomato", "pepper": "pepper", "peppers": "pepper",
    "cabbage": "cabbage", "apple": "apple", "banana": "banana", "yeast": "yeast", "peanut": "peanut", "peanuts": "peanut",
    "gnocchi": "gnocchi", "walnuts": "walnut", "rhubarb": "rhubarb", "plum": "plum", "plums": "plum", "pea": "pea", "peas": "pea",
    "lamb": "lamb", "pork": "pork", "beef": "stewing beef", "chicken": "chicken thigh", "fish": "white fish", "salmon": "salmon",
    "duck": "chicken thigh", "turkey": "chicken breast", "vanilla": "vanilla", "cumin": "cumin", "chilli": "chilli",
    "pitta": "pitta", "tortilla": "tortilla", "bun": "bun", "oil": "oil", "salt": "salt", "stock": "stock", "herb": "herb",
    "yoghurt": "yoghurt", "spring onions": "spring onion", "sweetcorn": "corn", "corn": "corn", "beetroot": "beetroot",
    "squash": "squash", "butternut": "squash", "pumpkin": "squash", "asparagus": "asparagus", "artichoke": "artichoke",
    "mango": "mango", "pineapple": "pineapple", "pear": "pear", "peach": "peach", "grape": "grape", "melon": "melon",
    "cherry": "cherry", "quinoa": "quinoa", "couscous": "couscous", "bulgur": "bulgur", "polenta": "polenta", "breadcrumb": "breadcrumb",
    "breadcrumbs": "breadcrumb", "cocoa": "cocoa", "coffee": "coffee", "tea": "tea", "pickled": "pickle",
}
# words considered "pantry" when matching dish pantry lists against inventory (never required)
ALLERGEN_GROUPS = {
    "nut": {"walnut", "almond", "cashew", "pine nut", "peanut", "peanut butter", "hazelnut", "pistachio", "pecan"},
    "nuts": {"walnut", "almond", "cashew", "pine nut", "peanut", "peanut butter", "hazelnut", "pistachio", "pecan"},
    "peanut": {"peanut", "peanut butter"},
    "dairy": {"milk", "butter", "cheese", "cream", "sour cream", "yoghurt", "parmesan", "pecorino", "mozzarella", "feta",
              "halloumi", "paneer", "blue cheese", "custard"},
    "milk": {"milk", "butter", "cheese", "cream", "sour cream", "yoghurt", "parmesan", "pecorino", "mozzarella", "feta",
             "halloumi", "paneer", "blue cheese"},
    "egg": {"egg", "egg white", "egg yolk", "mayonnaise", "egg noodle"},
    "eggs": {"egg", "egg white", "egg yolk", "mayonnaise", "egg noodle"},
    "gluten": {"flour", "pasta", "bread", "bun", "pitta", "tortilla", "egg noodle", "lasagne sheet", "puff pastry", "filo pastry",
               "breadcrumb", "couscous", "bulgur", "soy", "gnocchi", "sour rye starter", "injera"},
    "wheat": {"flour", "pasta", "bread", "bun", "pitta", "tortilla", "egg noodle", "lasagne sheet", "puff pastry", "filo pastry",
              "breadcrumb", "couscous", "bulgur", "gnocchi"},
    "fish": {"white fish", "salmon", "smoked haddock", "tinned tuna", "anchovy", "fish sauce", "worcestershire sauce", "dashi"},
    "shellfish": {"prawn"}, "crustacean": {"prawn"}, "prawn": {"prawn"},
    "soy": {"soy", "tofu", "miso", "doubanjiang", "gochujang"}, "soya": {"soy", "tofu", "miso", "doubanjiang", "gochujang"},
    "sesame": {"sesame oil", "sesame seed", "tahini", "hummus"},
    "pork": {"pork", "minced pork", "bacon", "ham", "pancetta", "chorizo", "sausage", "spam", "black pudding"},
    "beef": {"minced beef", "stewing beef"}, "lamb": {"lamb", "minced lamb"},
    "meat": {"pork", "minced pork", "bacon", "ham", "pancetta", "chorizo", "sausage", "spam", "black pudding", "minced beef",
             "stewing beef", "lamb", "minced lamb", "chicken thigh", "chicken breast", "whole chicken", "roast meat"},
    "alcohol": {"red wine", "white wine", "mirin"},
    "mushroom": {"mushroom"}, "mushrooms": {"mushroom"}, "coriander": {"coriander"}, "cilantro": {"coriander"},
    "celery": {"celery"}, "mustard": {"mustard", "mustard seed"},
}


def singular(word: str) -> str:
    if len(word) <= 3:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "sses", "xes")):
        return word[:-2]
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def normalise(line: str) -> str | None:
    """Turn one free-text inventory line into a library keyword (or a cleaned phrase)."""
    text = line.strip().lower().lstrip("-*•").strip()
    if not text:
        return None
    text = text.split("(")[0].split(",")[0]
    text = re.sub(rf"[\d{UNICODE_FRACTIONS}/.%]+", " ", text)
    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    # longest compound match first, against the raw phrase and its singularised form
    words = text.split()
    sing = " ".join(singular(w) for w in words)
    candidates = sorted(COMPOUNDS, key=len, reverse=True)
    for key in candidates:
        pattern = rf"\b{re.escape(key)}\b"
        if re.search(pattern, text) or re.search(pattern, sing):
            return COMPOUNDS[key]
    kept = [singular(w) for w in words if w not in QUANTITY_WORDS and w not in PREP_WORDS]
    if not kept:
        kept = [singular(words[-1])]
    phrase = " ".join(kept)
    return COMPOUNDS.get(phrase, phrase)


def load_library(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Dish library not found at {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Dish library is not valid JSON: {e}")
    if not isinstance(data, list):
        raise SystemExit("Dish library must be a JSON list")
    return data


def excluded_set(terms: list[str]) -> set[str]:
    out: set[str] = set()
    for t in terms:
        key = normalise(t) or t.lower().strip()
        out |= ALLERGEN_GROUPS.get(t.lower().strip(), set())
        out |= ALLERGEN_GROUPS.get(key, set())
        out.add(key)
    return out


def score_dish(dish: dict, have: set[str], assume_pantry: bool) -> dict:
    core = dish.get("core", []) or []
    optional = dish.get("optional", []) or []
    pantry = set(dish.get("pantry", []) or [])
    available = set(have)
    if assume_pantry:
        available |= pantry
    has_core = [c for c in core if c in available]
    has_opt = [o for o in optional if o in available]
    own_hits = [c for c in core + optional if c in have]
    missing_core = [c for c in core if c not in available]
    max_score = len(core) * 1.0 + len(optional) * 0.3
    score = (len(has_core) * 1.0 + len(has_opt) * 0.3) / max_score if max_score else 0.0
    uses = [u for u in dish.get("uses_up", []) or [] if u in have]
    return {"name": dish.get("name", "?"), "cuisine": dish.get("cuisine", ""), "minutes": int(dish.get("minutes", 0) or 0),
            "difficulty": dish.get("difficulty", ""), "tags": dish.get("tags", []) or [], "score": round(score, 3),
            "core_coverage": round(len(has_core) / len(core), 3) if core else 0.0,
            "has": has_core + has_opt, "missing_core": missing_core, "uses_up": uses, "own_hits": len(own_hits),
            "one_away": missing_core[0] if len(missing_core) == 1 else None}


def rank(dishes: list[dict], have: set[str], *, max_minutes: int | None = None, tags: list[str] | None = None,
         exclude: set[str] | None = None, assume_pantry: bool = True, top: int = 8) -> list[dict]:
    exclude = exclude or set()
    results = []
    for dish in dishes:
        if not isinstance(dish, dict):
            continue
        if max_minutes is not None and int(dish.get("minutes", 0) or 0) > max_minutes:
            continue
        if tags and not set(tags) <= set(dish.get("tags", []) or []):
            continue
        ingredients = set(dish.get("core", []) or []) | set(dish.get("optional", []) or [])
        if ingredients & exclude or any(x in dish.get("name", "").lower() for x in exclude if len(x) > 3):
            continue
        r = score_dish(dish, have, assume_pantry)
        if r["core_coverage"] > 0 and r["own_hits"] > 0:
            results.append(r)
    results.sort(key=lambda r: (-r["core_coverage"], -r["score"], -len(r["uses_up"]), r["minutes"], r["name"]))
    return results[:top]


def render(results: list[dict], have: set[str]) -> str:
    if not results:
        return ("No dish in the library matches what you have. Add one or two staples (eggs, a tin of tomatoes, pasta, rice) "
                "and several dishes open up.")
    out = [f"**Candidate dishes** (from: {', '.join(sorted(have)) or 'nothing recognised'})", ""]
    for i, r in enumerate(results, 1):
        pct = int(round(r["core_coverage"] * 100))
        line = f"{i}. **{r['name']}** ({r['cuisine']}, {r['minutes']} min, {r['difficulty']}) · core {pct}%"
        out.append(line)
        out.append(f"   has: {', '.join(r['has']) or 'nothing yet'}")
        if r["missing_core"]:
            out.append(f"   missing core: {', '.join(r['missing_core'])}")
        if r["uses_up"]:
            out.append(f"   clears: {', '.join(r['uses_up'])}")
        if r["one_away"]:
            out.append(f"   one {r['one_away']} away from a complete dish")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="inventory lines; default stdin")
    ap.add_argument("--max-minutes", type=int)
    ap.add_argument("--tag", action="append", default=[], help="require a tag (repeatable)")
    ap.add_argument("--exclude", action="append", default=[], help="ingredient or allergen group to avoid (repeatable)")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--no-pantry", action="store_true", help="do not assume store-cupboard items")
    ap.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.top <= 0:
        ap.error("--top must be positive")
    try:
        text = Path(a.file).read_text(encoding="utf-8") if a.file else sys.stdin.read()
    except OSError as e:
        print(f"Could not read inventory: {e}", file=sys.stderr)
        return 1
    have = {k for k in (normalise(l) for l in text.splitlines()) if k}
    if not have:
        print("No ingredients recognised. Give one ingredient per line, for example: 6 eggs, half a cabbage, tinned tomatoes.")
        return 0
    dishes = load_library(a.library)
    results = rank(dishes, have, max_minutes=a.max_minutes, tags=[t.lower() for t in a.tag],
                   exclude=excluded_set(a.exclude), assume_pantry=not a.no_pantry, top=a.top)
    if a.json:
        print(json.dumps({"have": sorted(have), "results": results}, indent=2, ensure_ascii=False))
    else:
        print(render(results, have))
    return 0


if __name__ == "__main__":
    sys.exit(main())
