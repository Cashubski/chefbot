---
name: substitutions
description: Replace a missing or unwanted ingredient without ruining the dish. Use when the user says they are out of something, asks "can I use X instead of Y", wants to avoid an ingredient for taste or cost, or needs an equivalent for an ingredient they cannot find locally. Gives the swap, the ratio and what changes in the result, using references/substitutions.md.
metadata:
  publisher: NeuralTake
  version: "0.16.0"
---

# Substitutions

## Steps

1. Identify the ingredient's **job** in this recipe: structure (flour, eggs), fat (butter, oil), acid (lemon, vinegar, wine), sweetness, salt or umami (soy, fish sauce, parmesan), leavening, thickening, aroma (herbs, spices), or texture (nuts, crunch). The job decides the swap; the name does not.
2. Look up the ingredient in [references/substitutions.md](references/substitutions.md). Prefer the swap the user is most likely to have.
3. Give the swap with its **ratio** and the **effect** in one line each: "Use 180 ml oil for 225 g butter: moister, less flavour, the crust will be softer."
4. Change the method where the swap needs it (more or less liquid, lower oven, longer rest).
5. If there is no good swap, say so plainly and suggest a different dish or the quickest shop-bought fix.

## Rules

- A swap for an allergen follows the dietary-adaptation skill's rules and its hidden-source checks.
- Baking is chemistry: flag swaps that change rise or set (baking powder for bicarbonate, honey for sugar, gluten-free flour) and give the adjusted amounts.
- Never present an unlike-for-unlike swap as invisible. Say what the eater will notice.
- Keep to one recommended swap and at most two alternatives.

## Output

The recommended swap with ratio and effect, any method change, and the alternatives in a line.
