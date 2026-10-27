# ChefBot

ChefBot is a cooking assistant for ChatGPT, published by [NeuralTake](https://neuraltake.com) and used in more than 25,000 conversations as a GPT, rated 4.7 from 100+ ratings. This repository is the plugin that replaces the GPT: a skills-only ChatGPT plugin in the [Agent Plugins](https://agent-plugins.org) format, with deterministic scripts for the parts of cooking that should not be left to a language model's arithmetic.

Public site, support, privacy policy and terms: <https://chefbot.neuraltake.com>.

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
tests/                             unit tests for every script
package.py                         validation + ZIP build
CHANGELOG.md
```

## Skills

| Skill | Trigger | Deterministic help |
| --- | --- | --- |
| cooking-assistant | any cooking question; sets the house style | |
| fridge-to-meal | ingredients or a photo → one recipe | |
| recipe-scaling | change servings, convert units | `scale_recipe.py`: rounding rules, sub-linear seasoning, density-based cup conversion, pan and time notes |
| meal-planning | several days, batch cooking, shopping list | `shopping_list.py`: merges quantities, converts spoons and cups, groups by aisle |
| cook-along | step-by-step mode, "what's next", serving several dishes together | `serving_schedule.py`: backwards timeline, oven-on time, hands-on clash warnings |
| dietary-adaptation | allergies, intolerances, diets, nutrition goals | `references/allergens.md`: UK/EU, US lists, hidden sources, swap behaviour |
| substitutions | missing ingredient | `references/substitutions.md`: ratios and effects |
| drink-pairings | what to drink, alcohol-free included | `references/pairing-guide.md` |
| food-safety | temperatures, storage, reheating, "is it safe" | `references/temperatures-and-storage.md` (FSA and USDA figures) |
| recipe-cards | print, save, export | `assets/recipe-card.md` template |
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

## Constraints to remember

- Skills-only plugins cannot later add an MCP server. Saved recipes, accounts or pantry tracking would need a new plugin with a backend.
- Keep the internal `name`. Change `displayName` for the visible name.
- Preserve the three default prompts unless there is a reason to change them; they are the conversation starters users know.
- Do not add promotional text to responses. The listing links to the website; the skills do not advertise.

## Licence

Proprietary. © NeuralTake. The skill texts and scripts may not be redistributed without permission.
