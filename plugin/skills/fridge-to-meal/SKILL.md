---
name: fridge-to-meal
description: Turn whatever the user has into a meal. Use when the user lists ingredients, photographs a fridge, cupboard or shopping, asks "what can I make with…", wants to use up leftovers or food about to go off, or wants dinner from what is at home without shopping. Produces one practical recipe from the available ingredients, with store-cupboard assumptions stated.
metadata:
  publisher: NeuralTake
  version: "0.16.0"
---

# Fridge to meal

The signature ChefBot flow: from an inventory (typed or photographed) to one meal the user can cook now.

## Input

- A list of ingredients, a photo of a fridge, cupboard, shopping bag or counter, or a mix.
- Optional: number of people, time available, equipment, mood or cuisine, diet.

## Steps

1. **Read the inventory.** From a photo, list what you can identify with reasonable confidence, grouped as proteins, vegetables and fruit, dairy and eggs, carbs, sauces and condiments. Mark anything uncertain with a question ("the jar on the second shelf looks like harissa, is it?"). Do not guess at hidden or blurred items.
2. **Assume a basic store cupboard** unless the user says otherwise: oil, salt, pepper, an onion or garlic, a few dried herbs or spices, flour, sugar, stock cubes, vinegar or lemon. State the assumption in one line and let the user correct it.
3. **Choose the meal.** Pick the one dish that uses the most perishable items first, suits the time and equipment, and needs the fewest extra purchases. Offer two alternatives in a single line each (name, main ingredients, time), not full recipes.
4. **Write the recipe** in the ChefBot layout (cooking-assistant skill): servings, timings, "You'll need" with exact quantities, numbered method with heat, times and doneness cues, notes with substitutions.
5. **Flag what is missing.** If one purchase would make the dish much better, say so plainly and give the version without it too.
6. **Offer the next move** in one line: scale it, adapt it for a diet, plan the rest of the week from what is left, or start cook-along mode.

## Rules

- Leftovers and open items are used before unopened ones. Say which items the recipe clears from the fridge.
- Cooked rice, cooked meat and fish, and anything the user describes as old or smelling off get a short safety note rather than a recipe (see the food-safety skill: reheating, the 2-hour rule, when to throw food away). Do not lecture; one or two sentences.
- If the inventory cannot make a sensible meal, say so and name the one or two cheapest additions that would unlock several dishes (eggs, a tin of tomatoes, pasta).
- With a photo, never state quantities you cannot see; write "about" and let the user confirm.

## Output

One recipe in the house layout, a short "clears from the fridge" line, two one-line alternatives, and the next-move offer. Keep the whole answer scannable on a phone at the counter.

## Examples

- "I have half a cabbage, two carrots, eggs, soy sauce and rice" → a vegetable fried rice or okonomiyaki-style pancake, choosing by time and pan; notes on the egg-fried-rice method with day-old rice.
- Photo of a fridge with chicken thighs, a lemon, yoghurt, spinach, a tube of harissa → harissa yoghurt chicken with wilted spinach; ask whether there is rice, couscous or bread.
