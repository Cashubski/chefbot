---
name: recipe-cards
description: Produce a clean, printable recipe card or a saved copy of a recipe. Use when the user asks to print, save, export, download, share or email a recipe, wants a PDF, a document, a shopping-list card or a weekly plan on one page, or asks for a recipe "written up properly". Formats the recipe with the template in assets/recipe-card.md and creates a file only when the conversation has a tool that can, confirming success before saying the file exists.
metadata:
  publisher: NeuralTake
  version: "0.16.0"
---

# Recipe cards and exports

## Steps

1. Fill the template in [assets/recipe-card.md](assets/recipe-card.md): title, yield and times, ingredients in cooking order with exact quantities, numbered method with heat and doneness cues, notes (substitutions, storage, reheating), and a one-line source note ("ChefBot, date; adapted from the user's recipe" or similar).
2. If the user wants a **file**: check which document, PDF or canvas tool the current conversation offers and use that tool with the formatted card. One A4 or Letter page; readable at arm's length (large headings, 11–12 pt body, generous spacing, ingredients in a column); no decorative images unless asked.
3. If a file tool succeeds, say what was created and where. If none is available or it fails, give the card in the chat in a clean block the user can copy, and say plainly that a file could not be made here.
4. For **several recipes or a plan**: one card per recipe, then the shopping list (meal-planning skill) as the last page.
5. Ask before adding a generated illustration; mark it as an illustration if added.

## Rules

- Never say a file, PDF or document was created, saved, attached or emailed unless the tool reported success in this conversation. ChefBot cannot send email or save to a user's account.
- Keep the card faithful to the recipe agreed in the conversation; do not re-scale or re-edit it silently.
- Use the user's units and spelling.

## Output

The card (as a file through the host tool, or inline), plus the one-line status of what was and was not created.
