---
name: recipe-scaling
description: Scale an existing recipe up or down and convert its units. Use when the user wants a recipe for a different number of people, to double or halve it, to convert between grams and cups, ounces or millilitres, or °C and °F, or asks whether times, pan size or seasoning should change when scaling. Runs scripts/scale_recipe.py where a Python tool exists and follows the same rounding rules by hand otherwise. For building a dough or batter from percentages or a classic ratio see baking-formulas; for nutrition figures see nutrition-estimate.
metadata:
  publisher: NeuralTake
  version: "0.17.1"
---

# Recipe scaling and unit conversion

Input: the ingredient list (from the conversation or pasted by the user), the current number of servings and the target, or a factor ("double it"), and optionally a unit preference (metric or US).

## Steps

1. If a Python tool is available, write the ingredient lines to a file and run `python3 scripts/scale_recipe.py --from 4 --to 6 ingredients.txt` (or `--factor 1.5`, and `--units us` or `--units metric` to convert; `--json` for structured output). The script prints the scaled list, the lines it rounded or treated as "to taste", and method notes. Present its output in the house layout; do not re-round by hand.
2. Without a Python tool, apply the rules below by hand and show your working for any line you rounded.
3. Rewrite the method for the new quantity: pan or tin size, batch cooking, and timing. Keep the user's original step numbering so they can follow both versions.

## Rules

The script and the hand method both follow these.

- Multiply every quantity by the factor (target ÷ current servings).
- **Round to kitchen-usable amounts:** grams and millilitres to 0.5 below 10, to 1 below 100, to 5 below 1,000, to 10 above; teaspoons and tablespoons to the nearest quarter; cups to the nearest eighth.
- **Countable items** (eggs, cloves, whole vegetables, tins) round to the nearest half. A half egg is "whisk one egg and use half, about 25 g".
- **Seasoning does not scale linearly** beyond a factor of 2 or below 0.5: salt, yeast, baking powder and soda, chilli, strong spices, extracts and vinegar are scaled by factor^0.8 and marked "then adjust to taste". Leavening for baked goods is marked to re-check against the flour weight.
- **Unit conversion:** weight converts exactly (1 oz = 28.35 g, 1 lb = 453.6 g). Volume converts exactly for liquids (1 US cup = 240 ml, 1 fl oz = 29.57 ml, 1 tbsp = 15 ml, 1 tsp = 5 ml). Dry ingredients convert between cups and grams only through a density table (flour 125 g per cup, caster or granulated sugar 200, brown sugar packed 220, butter 227, uncooked rice 185, rolled oats 90, cocoa 85, icing sugar 120, honey 340); anything not in the table is given by weight in ounces with a note.
- **Temperature:** °C to °F exactly, then rounded to the nearest 5 °F or 10 °C; always state conventional and fan.
- **Pan or tin:** area scales with the factor. A round tin's diameter scales by √factor (20 cm doubled becomes 28 cm). If the user keeps the same tin, the mixture is deeper and bakes longer; say so.
- **Time:** cooking time does not scale with quantity. Same depth or thickness, similar time. Deeper, fuller or more crowded, longer; begin checking at the original time and give the doneness cue. Larger roasts: give minutes per kilogram and the internal temperature (the cook-along skill's roast timer).
- **Stovetop:** more than about 1.5× in the same pan means cook in batches to keep the heat; say which steps.
- **Below 0.5×:** small quantities burn and dry faster; reduce heat a notch and check early.

## Output

The scaled "You'll need" list in the house layout, a short "Adjusted by hand" list naming every rounded or to-taste line, and the method notes that apply. State the factor used ("×1.5, 4 to 6 servings") on the first line.
