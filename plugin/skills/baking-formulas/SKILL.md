---
name: baking-formulas
description: Build bread, pastry, batters, custards and dressings from baker's percentages and classic ratios. Use when the user asks about hydration, baker's percentages, how much yeast, salt or starter for a given flour weight, how much dough a tin or a pizza needs, a sourdough or pizza dough formula, whether a dough recipe's hydration is high, or wants to make something from a ratio rather than a recipe. Computes the weights with scripts/bakers_percent.py where a Python tool exists and explains what each percentage does. For changing the servings or units of an existing recipe see recipe-scaling.
metadata:
  publisher: NeuralTake
  version: "0.17.1"
---

# Baking formulas and ratios

Baking is weighed, not measured. Flour is 100 % and every other ingredient is a percentage of it; a ratio recipe is the same idea for things with no flour.

## Steps

1. Work out which mode the user needs:
   - **Flour known** ("I have 500 g of flour"): weights from percentages.
   - **Dough weight known** ("I need 900 g of dough for two pizzas", "a 900 g loaf tin"): solve for the flour, then the weights.
   - **Recipe known** ("is this recipe's hydration high?"): percentages from the weights.
   - **No recipe at all** ("make me a shortcrust for a 23 cm tin"): start from a classic ratio in [references/ratios.md](references/ratios.md) and the tin table.
2. If a Python tool is available, run `python3 scripts/bakers_percent.py` with the matching flags (examples in the script's usage text: `--flour 500 --hydration 70 --salt 2 --yeast 1`, `--dough 900 --hydration 65 ...`, `--analyse recipe.txt`, `--ratio pie-dough --yield 600`). Present its table in the house layout's "You'll need" block. Without a Python tool, do the arithmetic by hand and show it.
3. Explain the formula in two or three lines: what the hydration means for handling and crumb, what the salt and yeast percentages do, what to change for the user's flour (wholemeal and rye drink more water; strong flour takes more hydration than plain).
4. Give the method only as far as the user needs it; the cooking-techniques skill has the full bread and pastry methods.

## Rules

- Standard ranges, state them when the user's numbers fall outside: hydration 60 to 65 % for sandwich loaves and pizza, 70 to 80 % for ciabatta and open-crumb sourdough; salt 1.8 to 2.2 %; instant yeast 0.5 to 1.5 % (fresh yeast three times that); sourdough starter 15 to 25 % at 100 % hydration, counted into the flour and water; sugar 0 to 10 % for lean and enriched breads; fat 0 to 15 %; egg 10 to 25 % for enriched doughs.
- Sourdough starter is half flour and half water: the script adds it into the totals, and the explanation should say so.
- Tin sizes: a 900 g (2 lb) loaf tin takes 800 to 950 g of dough; a 450 g (1 lb) tin 400 to 500 g; a 30 cm pizza 250 to 300 g; a 23 cm pie base 300 to 350 g of pastry, 500 to 550 g for base and lid; a 20 cm round cake tin 700 to 800 g of batter.
- Baking percentages use grams. If the user gives cups, convert with the recipe-scaling skill first and say that cup-to-gram conversions are approximate.
- Flour absorbs differently by brand, season and humidity: tell the user to hold back 5 % of the water and add it if the dough is stiff.

## Output

The formula as a table (ingredient, percentage, grams), the two-line explanation, and the one adjustment most likely to matter for the user's flour or tin.
