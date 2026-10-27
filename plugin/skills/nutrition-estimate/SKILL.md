---
name: nutrition-estimate
description: Estimate calories and nutrients per serving for a recipe. Use when the user asks how many calories a dish has, for macros, protein, fat, carbs, sugar, fibre or salt, whether a recipe is "healthy", for a nutrition label or per-serving figures, to compare two recipes, or to adjust a recipe towards a calorie or protein target. Computes from ingredient weights with scripts/nutrition.py and references/nutrition-table.csv when a Python tool is available, otherwise estimates by hand from the same table, and always labels the result an estimate.
metadata:
  publisher: NeuralTake
  version: "0.17.0"
---

# Nutrition estimate

## Input

- The recipe's ingredient lines with quantities, and the number of servings. If servings are missing, ask once; if quantities are vague ("some cheese"), state the amount you assumed.

## Steps

1. If a Python tool is available, save the ingredient lines to a file and run `python3 scripts/nutrition.py ingredients.txt --servings 4` (add `--json` for structured output). The script converts volumes and counts to grams, matches each line to [references/nutrition-table.csv](references/nutrition-table.csv), and prints per-serving and whole-recipe figures, the assumptions it made, the lines it could not count, and the share of recipe weight it matched.
2. Without a Python tool, do the same by hand: convert each line to grams (typical weights: egg 50 g, onion 150 g, garlic clove 5 g, tbsp 15 ml, tsp 5 ml), take the per-100 g values from the table, sum, divide by servings. Show the working for the three heaviest contributors.
3. Present a small table per serving (energy, protein, fat, saturates, carbohydrate, sugars, fibre, salt) and the whole-recipe column if useful. Round to the nearest 5 kcal and to one decimal for grams under 10.
4. Add one line of caveats: what was assumed, what was not counted, and that cooking losses are not included.
5. If the user has a target (fewer calories, more protein), name the one or two ingredient changes that move the figure most, with the new estimate. Use the substitutions skill for swaps.
6. For "is it healthy", describe what the figures show against ordinary reference intakes (around 2,000 kcal, 50 g protein, 70 g fat of which 20 g saturates, 260 g carbohydrate of which 90 g sugars, 30 g fibre, under 6 g salt a day for an adult) and say which number stands out. No verdicts on the person.

## Rules

- Always call it an **estimate**. Figures come from typical composition values for raw ingredients; brands, cuts, trimming and cooking change them, often by 10 to 20 percent.
- State every assumption the script reports (counted items, densities, synonyms) in a short list, not as hidden adjustments.
- If the matched share of the recipe weight is **below 80 percent**, say the figures are rough and name the uncounted lines.
- Do not give medical or weight-loss advice, prescribe calorie targets, or comment on anyone's body. Apply targets the user brings; suggest they confirm medical targets with a professional.
- Nothing about dieting or calorie restriction for anyone the conversation shows is under 18; offer the cooking help and leave the targets out.
- Salt is reported as salt (sodium × 2.5), the convention on UK labels; say so if the user expects sodium.
- Do not claim a dedicated nutrition engine or database beyond the bundled table; if an ingredient is not in it, say so rather than guessing silently.

## Output

The per-serving table, the one-line caveat with assumptions, and, if asked, the two changes that would move the figure most. Read [references/sources.md](references/sources.md) if the user asks where the numbers come from.
