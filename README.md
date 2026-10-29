# ChefBot

[![CI](https://github.com/Cashubski/chefbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Cashubski/chefbot/actions/workflows/ci.yml)
[![Open in ChatGPT](https://img.shields.io/badge/ChatGPT-open%20ChefBot-0F7C8A)](https://chatgpt.com/plugins/plugin_65cf8e2b928081919e9c1544d32a79dc)

ChefBot is a cooking assistant for ChatGPT, published by [NeuralTake](https://neuraltake.com) and used in more than 25,000 conversations as a GPT, rated 4.7 from 100+ ratings. This repository is the plugin that replaces the GPT: a skills-only ChatGPT plugin in the [Agent Plugins](https://agent-plugins.org) format, with deterministic scripts for the parts of cooking that should not be left to a language model's arithmetic.

Public site, support, privacy policy and terms: <https://chefbot.neuraltake.com>. Plugin listing: <https://chatgpt.com/plugins/plugin_65cf8e2b928081919e9c1544d32a79dc>.

## Layout

```
plugin/
  plugin.json                      Agent Plugins manifest (identity, listing, policy URLs)
  .codex-plugin/plugin.json        Codex compatibility manifest (kept in sync)
  assets/chefbot-icon.png          512 × 512 icon
  skills/<skill>/SKILL.md          one skill per directory, Agent Skills format
  skills/<skill>/references/       lookup tables the skill loads on demand
  skills/<skill>/scripts/          stdlib-only Python the model can run where a Python tool exists
  skills/<skill>/assets/           templates
tests/                             unit tests for every script, plus EVALUATION.md (manual activation sheet)
package.py                         validation + ZIP build
site/                              generator for chefbot.neuraltake.com (build_site.py, content fragments, assets)
.github/workflows/ci.yml           validation, tests, ZIP and site build on Python 3.10 and 3.13
CHANGELOG.md
```

## Skills

| Skill | Trigger | Deterministic help |
| --- | --- | --- |
| getting-started | first message, "what can you do" (onboarding skill) | |
| cooking-assistant | any cooking question; sets the house style | |
| fridge-to-meal | ingredients or a photo → one recipe; "what can I make" | `dish_match.py` ranks 120+ dishes by what you have; `references/use-it-up.md`, `references/seasonal.md` |
| recipe-scaling | change servings, convert units | `scale_recipe.py`: rounding rules, sub-linear seasoning, density-based cup conversion, pan and time notes |
| baking-formulas | hydration, baker's percentages, classic ratios, dough for a tin | `bakers_percent.py`; `references/ratios.md` |
| meal-planning | several days, batch cooking, shopping list | `shopping_list.py`: merges quantities, converts spoons and cups, groups by aisle |
| cook-along | step-by-step mode, "what's next", serving several dishes together, roast timing | `serving_schedule.py`: backwards timeline, oven-on time, hands-on clashes; `roast_timer.py` |
| entertaining | feeding a crowd, special occasions, make-ahead | `party_quantities.py`; `references/portions.md` |
| dietary-adaptation | allergies, intolerances, diets, nutrition goals | `references/allergens.md`: UK/EU and US lists, hidden sources, swap behaviour |
| nutrition-estimate | calories, macros, per-serving figures | `nutrition.py` with a 220+ ingredient per-100 g table |
| substitutions | missing ingredient | `references/substitutions.md`: ratios and effects |
| flavour-pairings | what goes with an ingredient, improvising | `references/pairings.md` |
| drink-pairings | what to drink, alcohol-free included | `references/pairing-guide.md` |
| food-safety | temperatures, storage, reheating, "is it safe" | `references/temperatures-and-storage.md` (FSA and USDA figures) |
| equipment-adaptation | air fryer, slow cooker, pressure cooker, microwave, no oven | `references/conversions.md` |
| recipe-cards | print, save, export | `assets/recipe-card.md` template |
| recipe-doctor | check, fix or improve a pasted recipe | `references/checklist.md` |
| cooking-techniques | learn a method, explore a cuisine | `references/techniques.md` |

Scripts are standard-library Python 3.10+. Every skill also describes the manual procedure, so the behaviour is the same where no Python tool is available.

## Build and release

```bash
python3 package.py --check     # validate manifests, skills, scripts
python3 package.py             # validate, run tests, write dist/chefbot-plugin-<version>.zip
```

Validation covers the public submission limits (display name and short description ≤ 30 characters, long description ≤ 4,000, up to three unique default prompts ≤ 128 characters, https policy URLs, square icon 48 to 4,096 px, brand colour contrast) and the Agent Skills rules (directory name equals the frontmatter name, description ≤ 1,024 characters, SKILL.md under 500 lines, referenced files exist, scripts compile).

Release steps:

1. Bump `version` in both manifests and add a CHANGELOG entry.
2. `python3 package.py`.
3. In the ChatGPT plugins dashboard, open the existing ChefBot plugin and upload the ZIP as an update against its current release. Never create a second plugin: the `name` field is the plugin's identity.
4. Submit for review; a skills-only plugin needs no MCP review cases or demo recording. Metadata, asset or skill changes always need a new ZIP and review.

## Website

`site/build_site.py` writes the static site for chefbot.neuraltake.com: the landing page with three worked examples computed by the real scripts, the skill list, FAQ, changelog (from `CHANGELOG.md`), and the support, privacy and terms pages from the fragments in `site/content/`.

```bash
python3 site/build_site.py --out site-out
```

## Testing in ChatGPT

`tests/EVALUATION.md` lists 90 prompts, five per skill, covering direct, indirect, incomplete, should-not-fire and edge cases, each with the behaviour expected. Run it after every upload; a skill firing for the wrong prompt is a description fix.

## Constraints to remember

- Skills-only plugins cannot later add an MCP server. Saved recipes, accounts or pantry tracking would need a new plugin with a backend.
- Keep the internal `name`. Change `displayName` for the visible name.
- Preserve the three default prompts unless there is a reason to change them; they are the conversation starters users know.
- Do not add promotional text to responses. The listing links to the website; the skills do not advertise.

## Licence

Code (scripts, tests, `package.py`, the site generator) is MIT. The skill texts, reference tables, dish and nutrition data, manifests, website copy and the ChefBot name and icon are © NeuralTake, all rights reserved. See [LICENSE](LICENSE).
