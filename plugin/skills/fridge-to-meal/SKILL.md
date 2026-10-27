---
name: fridge-to-meal
description: Turn whatever the user has into a meal. Use when the user lists ingredients, photographs a fridge, cupboard or shopping, asks "what can I make with…", wants to use up leftovers or food about to go off, or wants dinner from what is at home without shopping. Ranks candidate dishes from a library with scripts/dish_match.py, then writes one practical recipe from the available ingredients with store-cupboard assumptions stated.
metadata:
  publisher: NeuralTake
  version: "0.17.0"
---

# Fridge to meal

The signature ChefBot flow: from an inventory (typed or photographed) to one meal the user can cook now.

## Input

- A list of ingredients, a photo of a fridge, cupboard, shopping bag or counter, or a mix.
- Optional: number of people, time available, equipment, mood or cuisine, diet.

## Steps

1. **Read the inventory.** From a photo, list what you can identify with reasonable confidence, grouped as proteins, vegetables and fruit, dairy and eggs, carbs, sauces and condiments. Mark anything uncertain with a question ("the jar on the second shelf looks like harissa, is it?"). Do not guess at hidden or blurred items.
2. **Assume a basic store cupboard** unless the user says otherwise: oil, salt, pepper, an onion or garlic, a few dried herbs or spices, flour, sugar, stock cubes, vinegar or lemon. State the assumption in one line and let the user correct it.
3. **Rank candidate dishes.** If a Python tool is available, write the inventory one item per line and run `scripts/dish_match.py` on it before choosing:
   `python3 scripts/dish_match.py inventory.txt --top 8` with `--max-minutes 30`, `--tag vegetarian` (repeatable: vegan, gluten-free, quick, one-pan, batch, kids, leftovers, no-oven, cheap), `--exclude nuts` (repeatable; takes an ingredient or an allergen group such as dairy, egg, gluten, fish, shellfish, soy, sesame, pork, meat, alcohol), `--no-pantry` when the user has said the cupboard is bare, `--json` for structured output. It scores each dish in `references/dishes.json` by how much of its core and optional ingredients the inventory covers, breaks ties by how many perishables the dish clears, and marks dishes that are one ingredient away. Treat the ranking as candidates, not a verdict: the recipe still has to suit the people, time and equipment. Without a Python tool, scan the library yourself or choose from experience.
4. **Choose the meal.** Pick the one dish that uses the most perishable items first, suits the time and equipment, and needs the fewest extra purchases. Offer two alternatives in a single line each (name, main ingredients, time), not full recipes.
5. **Write the recipe** in the ChefBot layout (cooking-assistant skill): servings, timings, "You'll need" with exact quantities, numbered method with heat, times and doneness cues, notes with substitutions.
6. **Flag what is missing.** If one purchase would make the dish much better, say so plainly and give the version without it too. When suggesting what to buy or swap in, check [references/seasonal.md](references/seasonal.md) for the user's hemisphere and month and prefer what is in season.
7. **Offer the next move** in one line: scale it, adapt it for a diet, plan the rest of the week from what is left, or start cook-along mode.

## Leftovers and odd amounts

When the inventory is leftovers or part-used items (half a tin of coconut milk, egg whites, stale bread, cooked rice, roast meat, wilting herbs, open wine), load [references/use-it-up.md](references/use-it-up.md) for concrete uses and how long each keeps, and say which item is the most urgent to use.

## Rules

- Leftovers and open items are used before unopened ones. Say which items the recipe clears from the fridge.
- Cooked rice, cooked meat and fish, and anything the user describes as old or smelling off get a short safety note rather than a recipe (see the food-safety skill: reheating, the 2-hour rule, when to throw food away). Do not lecture; one or two sentences.
- If the inventory cannot make a sensible meal, say so and name the one or two cheapest additions that would unlock several dishes (eggs, a tin of tomatoes, pasta). The matcher's "one X away" notes are the shortlist for this.
- With a photo, never state quantities you cannot see; write "about" and let the user confirm.
- The dish library is a prompt for ideas, not a recipe source. Write every recipe fresh for the user's quantities and kit.

## Output

One recipe in the house layout, a short "clears from the fridge" line, two one-line alternatives, and the next-move offer. Keep the whole answer scannable on a phone at the counter.

## Examples

- "I have half a cabbage, two carrots, eggs, soy sauce and rice" → the matcher puts egg fried rice first (clears four items), then okonomiyaki; choose by time and pan; notes on the egg-fried-rice method with day-old rice.
- Photo of a fridge with chicken thighs, a lemon, yoghurt, spinach, a tube of harissa → harissa yoghurt chicken with wilted spinach; ask whether there is rice, couscous or bread.
- "Egg whites, stale bread and half a lemon" → use-it-up: meringues or a coconut macaroon for the whites, panzanella or croutons for the bread, the lemon in the dressing.
