# ChefBot editable source

Complete source exported from the installed plugin, version 0.15.3. Open this folder in VS Code or Cursor. No release has been published by this export.

## What to edit

- plugin/plugin.json: listing, website, icons and canonical package identity.
- plugin/.codex-plugin/plugin.json: compatibility manifest; synchronize repeated metadata.
- plugin/skills/instructions/SKILL.md: cooking instructions and workflows.
- plugin/skills/instructions/agents/openai.yaml: skill presentation.
- plugin/assets/chefbot-icon.png: original robot-chef image, currently referenced by both icon fields.

Keep the internal package name and plugin identity. Change displayName for the visible name. Preserve the three existing defaultPrompt values during routine updates. Increment the version in both manifests before a new release; the next patch is 0.15.4.

## Package

Run `python3 package.py` from this directory (Python 3.10+). This produces chefbot-plugin.zip. Upload it as an update to the existing ChefBot plugin, using its freshly fetched current release as the update guard. Do not create a duplicate plugin.

## Current limits

This is a skills-only plugin. It has no backend, accounts, database, external API or custom widget. Scripts bundled with skills need an execution-capable host; they do not automatically become remote tools.

The icon is a valid 512 x 512 PNG with correct package references. Its absence in the ChatGPT interface is unresolved. Check the imported icon in the publishing dashboard. A frontend is not required to display the listing icon.

## Policies

The website is https://neuraltake.com. Add supportURL, privacyPolicyURL and termsOfServiceURL inside extensions.com.openai.interface and the compatibility interface only once those public pages exist. Confirm actual data collection, processors, retention, deletion, support contact and publisher before drafting policies. Do not copy another app's promises.

## Recommended development order

1. Add a deterministic recipe-scaling script with explicit units and decimal quantities.
2. Add distinct workflows for weekly meal planning, consolidated shopping lists and serving-time schedules.
3. Add printable recipe cards using tools available in the host.
4. Build an authenticated backend only when adding saved recipes or pantry tracking. Start with save_recipe, list_recipes, get_recipe and delete_recipe. Enforce ownership per user, validate inputs and implement data export/deletion. Keep credentials server-side.

Skills are instructions plus optional scripts, references and assets. Persistent accounts and storage require a service. Only advertise capabilities after implementation and testing.

## Brief for your coding assistant

Inspect this source and preserve its identity. Implement deterministic recipe scaling first, with meaningful edge-case tests. Do not invent policy URLs, claim persistent storage, add a backend or publish beyond the requested scope. Investigate icon ingestion/display separately from cooking functionality.
