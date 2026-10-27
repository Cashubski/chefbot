# Changelog

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
