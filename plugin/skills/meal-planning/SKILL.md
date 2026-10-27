---
name: meal-planning
description: Plan several meals at once and produce one consolidated shopping list. Use when the user asks for a weekly or multi-day meal plan, batch cooking, meal prep, a budget plan, feeding a household for the week, or a shopping list that combines several recipes. Reuses ingredients across meals to cut waste and cost, then merges quantities by aisle with scripts/shopping_list.py when a Python tool is available.
metadata:
  publisher: NeuralTake
  version: "0.16.0"
---

# Meal planning and shopping lists

## Input

- Number of days and meals (default: dinners only), number of people, budget or time constraints, diet and dislikes, what is already in the fridge and cupboard, cooking skill and the equipment available.
- Ask only for people count and any allergy if missing; assume dinners for one week otherwise and say so.

## Steps

1. **Anchor on what is already there.** Use the fridge-to-meal skill's inventory rules; the first one or two meals use up perishables.
2. **Design the week as a chain.** Each fresh ingredient should appear in at least two meals (half a cabbage on Monday, the rest on Thursday; roast chicken Sunday, the carcass as stock or the leftovers in a pie midweek). Alternate heavy and light, quick and slow; put the longest cook on the day the user has most time.
3. **Keep each day to one line in the plan:** day, dish, time, "uses" (ingredients carried over) and a flag for cook-once-eat-twice days.
4. **Write the recipes only on request**, one at a time, in the house layout. In the plan itself give the dish, timings and the key method in a sentence.
5. **Build the shopping list.** If a Python tool is available, put each recipe's ingredient lines into a JSON file and run `python3 scripts/shopping_list.py plan.json` (or feed plain text with `# Recipe name` headers; `--have pantry.txt` removes items the user already has; `--json` for structured output). The script merges quantities, converts spoons and cups to millilitres where it can, and groups by aisle. Present its output as the list. Without a Python tool, merge by hand and show the items you combined.
6. **Add a prep plan** when the user is batch cooking: what to cook on the prep day, how long each item keeps in the fridge or freezer (food-safety skill) and how to reheat.

## Rules

- A plan is only as good as its reuse: say explicitly which items are bought once and used twice.
- Price is a comparison, not a quote. Never give currency amounts for the shop unless the user gives prices; describe "cheaper" choices (dried beans over tinned, whole chicken over portions, seasonal vegetables).
- Keep store-cupboard items (oil, salt, spices, flour) in a separate "check you have" section rather than adding them to the buy list.
- Respect the diet for every meal, not just the first; re-check the whole plan against the allergy list before sending it.

## Output

A day-by-day table (day · dish · time · uses), a one-paragraph note on reuse and prep, then the shopping list grouped by aisle with merged quantities, and a "check you have" cupboard list. Offer to write any recipe in full, or to start cook-along mode for tonight.
