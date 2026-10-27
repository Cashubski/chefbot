# Changelog

## 0.17.0 — 2026-10-27

Seven new skills and three new scripts, still skills-only.

- getting-started: onboarding skill (declared as `onboardingSkill`); two-line welcome, three things to try, one question.
- fridge-to-meal: `dish_match.py` ranks a library of 120+ dishes by inventory coverage ("one tin of tomatoes away from shakshuka"); use-it-up and seasonal references.
- baking-formulas: baker's percentages, dough-for-a-tin solving, recipe analysis and classic ratios with `bakers_percent.py`.
- nutrition-estimate: per-serving estimates from a 220+ ingredient per-100 g table with `nutrition.py`; always labelled as estimates.
- entertaining: quantities per head, make-ahead tables and `party_quantities.py`.
- cook-along: `roast_timer.py` for times, internal temperatures, resting, defrosting and a serve-at timeline.
- equipment-adaptation: air fryer, slow cooker, pressure cooker, microwave-only and no-oven conversions with time tables.
- flavour-pairings: 90+ ingredients with classic pairings and the method for improvising.
- recipe-doctor: a checklist-driven review of a pasted recipe with specific fixes and a corrected version.
- cooking-assistant: answers in the user's language; cross-references to every skill.
- Listing: description and keywords extended; onboarding skill declared.

## 0.16.0 — 2026-10-27

Migration from the ChatGPT GPT to a professional skills-only plugin.

- Replaced the single migrated `instructions` skill with eleven focused skills: cooking-assistant, fridge-to-meal, recipe-scaling, meal-planning, cook-along, dietary-adaptation, substitutions, drink-pairings, food-safety, recipe-cards, cooking-techniques.
- Added deterministic scripts with tests: recipe scaling and unit conversion, shopping-list merging by aisle, serving-time schedules.
- Added reference tables: regulated allergens and hidden sources, substitutions with ratios, drink pairings, safe temperatures and storage times (FSA and USDA), techniques and cuisine pantries.
- Added a recipe-card template.
- Listing: policy, support and website URLs on chefbot.neuraltake.com; developer name NeuralTake; brand colour; expanded keywords and description.
- Removed the end-of-conversation NeuralTake promotional line from responses, in line with the plugin guidelines on advertising.
- Removed the unused `gpt-icon.png` and the empty knowledge index.
- `package.py` now validates manifests, skills and scripts against the submission requirements and runs the tests before building a versioned ZIP in `dist/`.

## 0.15.3

- Automated export of the GPT as a plugin (single `instructions` skill).
