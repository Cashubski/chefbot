---
name: recipe-doctor
description: Review and fix a recipe the user already has. Use when the user pastes or describes a recipe and asks to check it, improve it, fix it, simplify it, make it less bland, make it taste "restaurant quality", work out why it failed, adapt an old family recipe, or wants an opinion on a recipe found online or in a book. Runs the checklist in references/checklist.md (ratios, salt, method order, timings, temperatures, doneness cues, equipment, allergens, servings, vague steps, safety), then returns a verdict, specific numbered fixes with reasons, and the corrected recipe in the ChefBot house layout.
metadata:
  publisher: NeuralTake
  version: "0.17.0"
---

# Recipe doctor

## Steps

1. **Read the whole recipe first**, including the title, servings and any story around it. Note the dish's intent (quick weeknight, celebration, batch) and the user's own words for what went wrong, if anything.
2. **Run the checklist** in [references/checklist.md](references/checklist.md), in order: quantities and ratios, salt and acid, method order, timings and temperatures, doneness cues, equipment, allergens, servings and scaling, vague instructions, safety. Note each finding with the line it refers to.
3. **Diagnose a failure** the user reports by matching the symptom to the table in the checklist (dense cake, split sauce, dry meat, soggy base, bland stew) before proposing a fix. Ask one question only if two causes are equally likely and the answer changes the fix.
4. **Decide what to leave alone.** A working step stays as written. The user's dish, ingredients and voice are kept; the aim is their recipe, corrected, not a different recipe.
5. **Write the verdict** in one or two sentences: what the recipe does well and the one thing that matters most.
6. **List the fixes**, numbered, each with the exact change and the reason in a few words ("Add 1 tsp fine salt to the 500 g of sauce: it has none, and 1 percent by weight is the baseline for a savoury sauce"). Order them by impact.
7. **Rewrite the recipe** in the house layout from the cooking-assistant skill (Serves · Prep · Cook line, You'll need, Method with heat, time and doneness cues, Notes), with changed lines marked so the user can see what moved. If only two or three lines change, give the changed lines instead of a full rewrite.

## Rules

- Be specific. Quantities, temperatures and times, never "season to taste" or "cook until done" as a fix.
- Do not rewrite what works, and do not add ingredients the recipe did not call for unless the fix needs one (salt, acid, fat); say so when you do.
- Keep the cuisine's logic. Do not "improve" a traditional dish into a different one; offer that separately as an adaptation if the user wants it.
- Say plainly when a recipe is **unsafe**: home canning without a tested process, raw or lightly cooked egg for vulnerable people, undercooked poultry or pork timings, cooling or storage steps that break the 2-hour rule, kidney beans without a hard boil. Point to the food-safety skill's figures and do not soften the warning.
- Flag allergens present in the recipe (dietary-adaptation skill) in one line; do not rewrite for a diet unless asked.
- Old family recipes often assume knowledge ("a hot oven", "a knob of butter", "bake until done"). Fill the gaps with the standard values and say that you did, rather than treating the gaps as mistakes.
- Online recipes: comments about the recipe are evidence; the headnote and the photograph are not.

## Output

Verdict (one or two sentences), numbered fixes with reasons, then the corrected recipe in the house layout with changed lines marked, or the changed lines alone when the changes are few. End with the allergen line and any safety warning.
